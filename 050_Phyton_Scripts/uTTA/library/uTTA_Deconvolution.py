import numpy as np              # numpy 2.1.0
from scipy.signal import find_peaks
import matplotlib.pyplot as plt                 # matplotlib 3.9.2
from skimage import restoration    # scikit-image 0.24.0


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
        self.deconv_z_shift = 0         # deconv_z_shift = -2.82660000000
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

    def prepare_zth_deconvolution(self):

        no_sample_points = int((self.z_raw[-1] - self.z_raw[0]) * self.deconv_samples_per_decade)
        no_sample_points_log = int(np.power(2, np.ceil(np.log2(no_sample_points))))
        print("Number of SamplePoints: {NoSampPoints} SamplePoints power of 2: {NoSampPnts}".format(NoSampPoints=no_sample_points, NoSampPnts=no_sample_points_log))

        log_samp_point_intervall = (self.z_raw[-1] - self.z_raw[0]) / no_sample_points_log
        print("SamplePoint Intervall: {SampInt}".format(SampInt=log_samp_point_intervall))

        z = np.linspace(start=self.z_raw[0], stop=self.z_raw[-1], num=no_sample_points_log) # create constant step width timebase
        self.a_z = np.interp(z, self.z_raw, self.zth_raw)
        self.rth_stat = np.mean(self.a_z[int(0.98 * len(self.a_z)):-1])
        print("Zth end value: {ZthEnd:.3f}, Zth Curve Start Value {Rth_start}K/W".format(ZthEnd=self.rth_stat, Rth_start=self.zth_raw[0]))

        self.dadz = np.diff(self.a_z) / np.diff(z)
        # sum_dadz = np.sum(dadz)
        # dadz = dadz / np.sum(dadz)
        self.w_z = np.exp(z - np.exp(z))
        self.z = z

        self.create_zth_reference_curve()       # for trials generate the Zth reference curve
        return

    def create_zth_reference_curve(self):

        self.ref_z = (1-np.exp(-np.exp(self.z)))     # for testing: create a reference curve with a known reference RC Element of 1Ohm and 1F = 1tau
        self.ref_dadz = np.diff(self.ref_z) / np.diff(self.z)
        return

    def add_deconv_plot_input_zth_curve(self, plot_id):

        plot_id.loglog(np.exp(self.z), self.a_z, label="Input Zth Curve")  # Input curve to be deconvolved
        plot_id.set_title("Input Zth Curve")
        plot_id.set_ylabel('Zth / [K/W]')
        plot_id.set_xlabel('Time / [ln(s)]')
        plot_id.legend()
        plot_id.grid(which='both')
        return

    def add_deconv_input_dadz_plot(self, plot_id):

        plot_id.plot(self.z[:-1], self.dadz, label="da/dz", linestyle='dashed')  # Plot some data on the axes.
        plot_id.set_title("Interpolated and differentiated Zth Curve")
        plot_id.set_ylabel('Derivative of Zth / [K/W/ln(s)')
        plot_id.set_xlabel('Time / [ln(s)]')
        plot_id.legend()
        plot_id.grid(which='both')
        return

    def deconvolve_reference_zth_lucy_richardson(self, iterations):

        self.ref_deconv, self.ref_peaks = self.deconvolve_get_peaks(self.ref_dadz, self.w_z, iterations)

        print("1Ohm + 1F Reference peak height: {PHeight:.4f}, peak location: {ploc:5f}".format(
              PHeight=np.max(self.ref_deconv), ploc=self.deconv_z_shift))
        return

    def deconvolve_get_peaks(self, dadz, w_z, iterations):

        deconv = restoration.richardson_lucy(dadz, self.w_z[:-1] / np.sum(w_z[:-1]),
                                             num_iter=iterations,
                                             clip=False)  # * sum_ref_dadz
        peaks, _ = find_peaks(deconv)

        # ToDo: find a better way to determine the zshift. at the moment this relies on having the ref curve deconvolved first.
        if self.deconv_z_shift == 0:
            self.deconv_z_shift = self.z[peaks[0]]

        return deconv, peaks

    def add_reference_deconv_output_plot(self, plot_id,  iterations):
        plot_id.plot(self.z[:-1] - self.deconv_z_shift, self.ref_deconv,
                     label="Reference deconv with {iter} Iterations".format(iter=iterations))  # Plot some data on the axes.

    def add_deconv_output_plot(self, plot_id,  iterations):
        plot_id.plot(self.z[:-1] - self.deconv_z_shift, self.deconvolved,
                     label="Deconvolved with {iter} Iterations".format(iter=iterations))  #

    def add_dadz_deconv_output_plot(self, plot_id, iterations):
        plot_id.plot(self.z, self.dadz_deconvolved,
                     label="da/dz {iter} Iterations".format(iter=iterations))  #

    def add_dadz_deconv_error_plot(self, plot_id, iterations):
        plot_id.plot(self.z[:-1] - self.deconv_z_shift, self.dadz - self.dadz_deconvolved[:-1],
                     label="Delta da/dz {iter} Iterations".format(iter=iterations))  #

    def add_zth_deconvolution_error_plot(self, plot_id, iterations):
        plot_id.plot(self.z - self.deconv_z_shift, self.zth_deconvolved - self.a_z,
                     label="Delta Zth {iter} Iterations".format(iter=iterations))  # Plot some data on the axes.

    def add_deconv_zth_output_plot(self, plot_id, iterations):
        plot_id.loglog(np.exp(self.z), self.zth_deconvolved,
                       label="Reconstructed Zth {iter} Iterations".format(iter=iterations))  #

    def deconvolve_zth_lucy_richardson(self, iterations):
        self.deconvolved, self.peaks = self.deconvolve_get_peaks(self.dadz, self.w_z, iterations)

        self.report_peaks_to_console(self.peaks)

        # dadz_conv = (np.convolve(deconvolved, w_z, "same") / np.sum(deconvolved)) * (z[2] - z[1])
        self.dadz_deconvolved = (np.convolve(self.deconvolved, self.w_z, "same")) * (self.z[2] - self.z[1])
        self.zth_deconvolved = (np.cumsum(self.dadz_deconvolved) / np.sum(self.deconvolved)) * self.rth_stat + self.a_z[0]
        return

    def report_peaks_to_console(self, peaks):
        outp = ""
        print("Deconvolvable to {n_peaks} peaks".format(n_peaks=len(peaks)))
        for peak in peaks:
            outp = outp + "{tim:.4f};{R:.4f};".format(tim=self.z[peak] - self.deconv_z_shift, R=self.deconvolved[peak])
        print(outp)
        return

    def deconvolve_zth_full(self, iterations, do_plot):
        #print("z-Base Timestep: " + str(self.z[2] - self.z[1]))
        #peaks = []

        self.deconvolve_reference_zth_lucy_richardson(iterations)  # for trials, do the zth reference deconvolution to get the real z-shift
        self.deconvolve_zth_lucy_richardson(iterations)

        fig, axs = plt.subplots(nrows=3, ncols=2, layout="constrained")
        self.add_deconv_plot_input_zth_curve(axs[0 ,0])
        self.add_deconv_zth_output_plot(axs[0, 0], iterations)

        self.add_deconv_input_dadz_plot(axs[0 ,1])
        self.add_dadz_deconv_output_plot(axs[0, 1], iterations)

        self.add_reference_deconv_output_plot(axs[1, 0],  iterations)
        self.add_deconv_output_plot( axs[1, 0],  iterations)

        self.add_dadz_deconv_error_plot(axs[1, 1], iterations)

        self.add_zth_deconvolution_error_plot(axs[2, 0], iterations)

        axs[0, 0].legend()
        axs[0, 0].grid(which='both')

        axs[0, 1].grid(which='both')
        axs[0, 1].legend()

        axs[1, 0].legend()
        axs[1, 0].grid(which='both')

        axs[2, 0].grid(which='both')
        axs[2, 0].legend()

        plt.show()

        return
