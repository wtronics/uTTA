import numpy as np
from scipy.signal import find_peaks
from skimage import restoration    # scikit-image
import library.uTTA_data_processing as udProc
import library.uTTA_data_plotting as ud_plot
import logging


class UttaDeconvolution:

    def __init__(self, logger=None):

        if logger is None:
            self.logger = logging.getLogger("dummy")
            self.logger.addHandler(logging.NullHandler())
            self.logger.propagate = False # Important: prevents forwarding to the root logger
        else:
            self.logger = logger

        # Variables for the Zth deconvolution with Lucy-Richardson Algorithm
        self.rth_stat = 0
        self.deconv_samples_per_decade = 50
        self.z_raw = np.array([])       # the raw converted cooling time base, basically just ln(t)
        self.zth_raw = np.array([])  # the raw converted cooling time base, basically just ln(t)
        self.z = np.array([])           # interpolated, equidistant linear ln(t)-timebase

        self.a_z = np.array([])         # interpolated input Zth-curve with timebase z
        self.dadz = np.array([])        # differentiated input Zth-curve
        self.w_z = np.array([])         # weighing function  --> exp(z - exp(z)), needed for interpolation
        #self.deconv_z_shift = 0         # deconv_z_shift = -2.82660000000
        self.deconvolved = np.array([])
        self.dadz_deconvolved = np.array([])
        self.zth_deconvolved = np.array([])
        self.peaks = np.array([])

        # Additional experimental curves
        self.ref_z = np.array([])       # reference curve with a known reference RC Element of 1Ohm and 1F = 1tau
        self.ref_dadz = np.array([])    # differentiated reference curve
        self.ref_peaks = np.array([])
        self.ref_deconv = np.array([])

    def import_zth_input_data(self, timebase, zth):
        """
        Import zth-data and their timebase into the class from two independent arrays of the same length

        Args:
            timebase (list oder numpy.array): timepoints when the zth samples were taken
            zth      (list oder numpy.array): thermal impedances at a given time

        Returns:
            None
                
        Raises:
            ValueError: When array length are not the same
        """

        if len(timebase) != len(zth):
            raise ValueError("Array length must be the same")
        self.z_raw = np.log(timebase)
        self.zth_raw = zth
    
    def import_from_postprocess(self, utta_postprocess:udProc.UttaZthProcessing):
        """
        Imports zth-data and the timebase into the classs for processing

        Args:
            utta_postprocess (UttaZthProcessing): uTTA Postprocessing class

        Returns:
            None
                
        Raises:
            ValueError: When postprocessing class has no data to hand over
        """

        if not utta_postprocess.flag_import_successful:
            raise ValueError("No data to load from UttaZthProcessing")
        self.z_raw = np.log(utta_postprocess.adc_timebase_cooling)
        self.zth_raw = utta_postprocess.zth[0, :]

    def prepare_zth_deconvolution(self):
        """
        Prepares imported data for the upcoming deconvolution:
            - prepares a new, evenly spaced timebase in ln(t)-space
            - do the differentiation (da/dz) of the input curve
            - create the reference function (greens function) for the deconvolution

        Args:
            None

        Returns:
            None
                
        Raises:
            None
        """
        no_sample_points = int((self.z_raw[-1] - self.z_raw[0]) * self.deconv_samples_per_decade)
        self.logger.info(f"Number of SamplePoints: {no_sample_points}")

        log_samp_point_intervall = (self.z_raw[-1] - self.z_raw[0]) / no_sample_points
        self.logger.info(f"SamplePoint Intervall: {log_samp_point_intervall}")

        z = np.linspace(start=self.z_raw[0], stop=self.z_raw[-1], num=no_sample_points) # create constant step width timebase
        self.a_z = np.interp(z, self.z_raw, self.zth_raw)

        self.rth_stat = np.mean(self.a_z[int(0.98 * len(self.a_z)):-1])
        self.logger.info(f"Zth end value: {self.rth_stat:.3f}, Zth Curve Start Value {self.zth_raw[0]}K/W")

        self.dadz = np.diff(self.a_z) / np.diff(z)
        self.w_z = np.exp(z - np.exp(z))
        self.z = z

        return

    def deconvolve_get_peaks(self, dadz, w_z, iterations):
        """
        Deconvolve the prepared signal by using the Lucy-Richardson deconvolution algorithm.
        After deconvolution, try to find the visible peaks as a first attempt to identify the equivalent RC-elements

        Args:
            None

        Returns:
            None
                
        Raises:
            None
        """
        deconv = restoration.richardson_lucy(dadz, self.w_z[:-1] / np.sum(w_z[:-1]),
                                             num_iter=iterations,
                                             clip=False)  # * sum_ref_dadz
        peaks, _ = find_peaks(deconv)
        return deconv, peaks
    
    def deconvolve_zth_lucy_richardson(self, iterations):
        self.deconvolved, self.peaks = self.deconvolve_get_peaks(self.dadz, self.w_z, iterations)

        self.dadz_deconvolved = (np.convolve(self.deconvolved, self.w_z, "same")) * (self.z[2] - self.z[1])
        self.zth_deconvolved = (np.cumsum(self.dadz_deconvolved) / np.sum(self.deconvolved)) * self.rth_stat + self.a_z[0]
        return

    def report_peaks_to_console(self, peaks):
        outp = ""
        print(f"Deconvolvable to {len(peaks)} peaks")
        for peak in peaks:
            outp = outp + f"{self.z[peak]:.4e};{self.deconvolved[peak]:.4e};"
        print(outp)
        return

    # def add_reference_deconv_output_plot(self):
    #     iterations = 1000
    #     lines = [
    #             {'x_data': self.z[:-1],
    #              'y_data': self.ref_deconv,
    #              'label': f"Reference deconv with {iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='A.U',
    #                                          title='Reference Deconvolution (1K/W & 1Ws/K)')

    def add_deconv_tau_output_plot(self):
        iterations = 1000
        lines = [
                {'x_data': self.z[:-1],
                 'y_data': self.deconvolved,
                 'label': f"Deconvolved with {iterations} Iterations",
                 'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Tau / [s]',
                                             y_label='Zth / [K/W]',
                                             title='Deconvolved Spectrum')

    # def add_dadz_deconv_output_plot(self):
    #     iterations = 1000
    #     lines = [
    #             {'x_data': self.z,
    #              'y_data': self.dadz_deconvolved,
    #              'label': f"da/dz {iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='A.U',
    #                                          title='da/dz')

    # def add_dadz_deconv_error_plot(self):
    #     iterations = 1000
    #     lines = [
    #             {'x_data': self.z[:-1],
    #              'y_data': self.dadz - self.dadz_deconvolved[:-1],
    #              'label': f"Delta da/dz {iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='A.U',
    #                                          title='da/dz Error')
 
    def add_zth_deconvolution_error_plot(self):
        iterations = 1000
        lines = [
                {'x_data': self.z,
                 'y_data': self.zth_deconvolved - self.a_z,
                 'label': f"Delta Zth {iterations} Iterations",
                 'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Tau / [s]',
                                             y_label='Thermal Impedance / [K/W]',
                                             title='Deconvolved Thermal Impedance Error')

    def add_deconv_zth_output_plot(self):
        iterations = 1000
        lines = [{'x_data': np.exp(self.z),
                  'y_data': self.zth_deconvolved,
                  'label': f"Reconstructed Zth {iterations} Iterations",
                  'axis': 0},
                  {'x_data': np.exp(self.z),
                  'y_data': self.a_z,
                  'label': "Input Zth Curve",
                  'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             x_scale='log',
                                             y_scale='log',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label='Thermal Impedance / [K/W]',
                                             title='Thermal Impedance')



