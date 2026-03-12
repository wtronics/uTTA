import numpy as np              # numpy 2.1.0
from scipy.signal import find_peaks
import matplotlib.pyplot as plt                 # matplotlib 3.9.2
from skimage import restoration    # scikit-image 0.24.0
import library.uTTA_data_processing as udProc
import library.uTTA_data_plotting as ud_plot


class UttaDeconvolution:

    def __init__(self):
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
        self.z_raw = np.log(timebase)
        self.zth_raw = zth
    
    def import_from_postprocess(self, utta_postprocess:udProc.UttaZthProcessing):
        self.z_raw = np.log(utta_postprocess.adc_timebase_cooling)
        self.zth_raw = utta_postprocess.zth[0, :]

    def prepare_zth_deconvolution(self):

        no_sample_points = int((self.z_raw[-1] - self.z_raw[0]) * self.deconv_samples_per_decade)
        print(f"Number of SamplePoints: {no_sample_points}")

        log_samp_point_intervall = (self.z_raw[-1] - self.z_raw[0]) / no_sample_points
        print(f"SamplePoint Intervall: {log_samp_point_intervall}")

        z = np.linspace(start=self.z_raw[0], stop=self.z_raw[-1], num=no_sample_points) # create constant step width timebase
        self.a_z = np.interp(z, self.z_raw, self.zth_raw)

        self.rth_stat = np.mean(self.a_z[int(0.98 * len(self.a_z)):-1])
        print(f"Zth end value: {self.rth_stat:.3f}, Zth Curve Start Value {self.zth_raw[0]}K/W")

        self.dadz = np.diff(self.a_z) / np.diff(z)
        self.w_z = np.exp(z - np.exp(z))
        self.z = z

        return

    def deconvolve_get_peaks(self, dadz, w_z, iterations):

        deconv = restoration.richardson_lucy(dadz, self.w_z[:-1] / np.sum(w_z[:-1]),
                                             num_iter=iterations,
                                             clip=False)  # * sum_ref_dadz
        peaks, _ = find_peaks(deconv)
        return deconv, peaks

    def add_reference_deconv_output_plot(self):
        iterations = 1000
        lines = [
                {'x_data': self.z[:-1],
                 'y_data': self.ref_deconv,
                 'label': f"Reference deconv with {iterations} Iterations",
                 'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Tau / [s]',
                                             y_label='A.U',
                                             title='Reference Deconvolution (1K/W & 1Ws/K)')

    def add_deconv_output_plot(self):
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

    def add_dadz_deconv_output_plot(self):
        iterations = 1000
        lines = [
                {'x_data': self.z,
                 'y_data': self.dadz_deconvolved,
                 'label': f"da/dz {iterations} Iterations",
                 'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Tau / [s]',
                                             y_label='A.U',
                                             title='da/dz')

    def add_dadz_deconv_error_plot(self):
        iterations = 1000
        lines = [
                {'x_data': self.z[:-1],
                 'y_data': self.dadz - self.dadz_deconvolved[:-1],
                 'label': f"Delta da/dz {iterations} Iterations",
                 'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Tau / [s]',
                                             y_label='A.U',
                                             title='da/dz Error')
 
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

