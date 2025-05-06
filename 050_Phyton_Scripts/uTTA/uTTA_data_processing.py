import numpy as np              # numpy 2.1.0
import numpy.dtypes             # numpy 2.1.0
from scipy.signal import find_peaks
import matplotlib.pyplot as plt                 # matplotlib 3.9.2
from skimage import color, data, restoration    # scikit-image 0.24.0


def interpolate_to_common_timebase(timebase_in, adc, tc):

    print("Number of temperature samples: {TCsamp}, Duration of measurement: {tmeas} = {TCsS} Samples/Second".format(TCsamp=len(tc[0]),
                                                                                                                     tmeas=timebase_in[-1],
                                                                                                                     TCsS=len(tc[0]) / timebase_in[-1]))
    timebase_int = np.linspace(0, stop=timebase_in[-1], num=int(timebase_in[-1]) + 1)

    num_adc = len(adc)
    adc_int = np.zeros((num_adc, len(timebase_int)), numpy.float32)

    for ch_idx in range(0, num_adc):
        adc_int[ch_idx] = np.interp(timebase_int, timebase_in, adc[ch_idx])

    num_tc = len(tc)
    timebase_tc = np.linspace(start=0, stop=timebase_in[-1], num=len(tc[0]))    # Create a dummy timebase for the thermocouples for interpolation
    tc_int = np.zeros((num_tc, len(timebase_int)), numpy.float32)
    for ch_idx in range(0, num_adc):
        tc_int[ch_idx] = np.interp(timebase_int, timebase_tc, tc[ch_idx])

    return timebase_int, adc_int, tc_int


def calculate_cooling_curve(timebase_total, adc, cooling_start_block, samp_decade):
    # Cut Timebase and measurement to cooling section
    time_base_cooling = (timebase_total[(cooling_start_block * samp_decade):-1] - timebase_total[(cooling_start_block * samp_decade) - 1])
    adc_cooling = adc[:, (cooling_start_block * samp_decade):-1]

    # Get Min and Max Values of the Full Cooling Curve
    dut_imin = min(adc_cooling[3, :])
    dut_imax = max(adc_cooling[3, :])
    print("Min Diode Current:  {min:.2f}A; Max Diode current: {max:.2f}A".format(min=dut_imin, max=dut_imax))
    cooling_start_index = (np.where(np.isclose(adc_cooling[3, :], dut_imin)))[0][0]
    print("Index of closest value: " + str(cooling_start_index))

    # Cut the measurement data down to the starting point of the cooling phase
    adc_cooling = adc_cooling[:, cooling_start_index:-1]
    time_base_cooling = time_base_cooling[cooling_start_index:-1] - time_base_cooling[cooling_start_index - 1]

    return time_base_cooling, adc_cooling


def calculate_diode_heating(timebase, adc, cooling_start_block, samp_decade):
    # Calculate the average heating current, voltage and power through the diode
    i_heat = np.mean(adc[3, ((cooling_start_block - 2) * samp_decade):((cooling_start_block - 1) * samp_decade) - 1])
    u_dio_heated = np.mean(adc[0, ((cooling_start_block - 2) * samp_decade):((cooling_start_block - 1) * samp_decade) - 1])
    p_dio_heat = i_heat * u_dio_heated
    print("HEATING VALUES: Range: {tstart:.2f}s to {tend:.2f}s, Current: {curr:.2f}A, Voltage: {volts:.2f}V, Power: {pow:.2f}W".format(
        tstart=timebase[(cooling_start_block - 2) * samp_decade],
        tend=timebase[((cooling_start_block - 1) * samp_decade) - 1],
        curr=i_heat,
        volts=u_dio_heated,
        pow=p_dio_heat))

    return p_dio_heat


def find_static_states(data, threshold=0.01, min_length=5):
    """
    Detects static areas within a numpy-array where values stay within a certain threshold and have a minimum length.

    Args:
        data (numpy.ndarray): Input data array
        threshold (float): Maximum absolute difference between values of the range.
        min_length (int): Minimum amount of consecutive values which must be within the threshold.

    Returns:
        list: a list of tuples which represent the start and end points of each area.
    """

    ranges = []
    start = None

    for i in range(len(data)):
        if start is None:
            start = i
        elif abs(data[i] - data[start]) > threshold:
            if i - start >= min_length:
                ranges.append((start, i - 1))
            start = i

    # checking if the last range is long enough
    if len(data) - start >= min_length:
        ranges.append((start, len(data) - 1))

    return ranges


def deconvolve_zth_lucy_richardson(t, zth, samp_decade, get_peaks, iterations):
    # deconv_zShift = -2.82660000000

    z_raw = np.log(t)

    NoSamplePoints = int((z_raw[-1] - z_raw[0]) * samp_decade)
    NoSamplePointsLog = int(np.power(2, np.ceil(np.log2(NoSamplePoints))))
    print("Number of SamplePoints: {NoSampPoints} SamplePoints power of 2: {NoSampPnts}".format(NoSampPoints=NoSamplePoints, NoSampPnts=NoSamplePointsLog))

    LogSampPointIntervall = (z_raw[-1] - z_raw[0]) / NoSamplePointsLog
    print("SamplePoint Intervall: {SampInt}".format(SampInt=LogSampPointIntervall))

    z = np.linspace(start=z_raw[0], stop=z_raw[-1], num=NoSamplePointsLog) # create constant step width timebase
    a_z = np.interp(z, z_raw, zth)
    Rth_Stat = np.mean(a_z[int(0.98 * len(a_z)):-1])
    print("Zth end value: {ZthEnd:.3f}, Zth Curve Start Value {Rth_start}K/W".format(ZthEnd=Rth_Stat, Rth_start=zth[0]))

    dadz = np.diff(a_z) / np.diff(z)
    # sum_dadz = np.sum(dadz)
    # dadz = dadz / np.sum(dadz)
    w_z = np.exp(z - np.exp(z))

    ref_z = (1-np.exp(-np.exp(z)))     # for testing: create a reference curve with a known reference RC Element of 1Ohm and 1F = 1tau
    ref_dadz = np.diff(ref_z) / np.diff(z)

    fig, axs = plt.subplots(nrows=3, ncols=2, layout="constrained")

    axs[0, 0].loglog(np.exp(z), a_z, label="Input Zth Curve")  # Input curve to be deconvolved
    axs[0, 0].set_title("Input Zth Curve")
    axs[0, 0].set_ylabel('Zth / [K/W]')
    axs[0, 0].set_xlabel('Time / [ln(s)]')

    axs[0, 1].plot(z[:-1], dadz, label="da/dz", linestyle='dashed')  # Plot some data on the axes.

    axs[0, 1].set_title("Interpolated and differentiated Zth Curve")
    axs[0, 1].set_ylabel('Derivative of Zth / [K/W/ln(s)')
    axs[0, 1].set_xlabel('Time / [ln(s)]')

    print("z-Base Timestep: " + str(z[2] - z[1]))

    for Step in iterations:
        ref_deconv = restoration.richardson_lucy(ref_dadz, w_z[:-1] / np.sum(w_z[:-1]), num_iter=Step, clip=False)  # * sum_ref_dadz
        ref_peaks, _ = find_peaks(ref_deconv)

        deconv_zShift = z[ref_peaks[0]]

        axs[1, 0].plot(z[:-1] - deconv_zShift, ref_deconv,
                       label="Reference deconv with " + str(Step) + " Iterations")  # Plot some data on the axes.

        print("1Ohm + 1F Reference peak height: {pheight:.4f}, peak location: {ploc:5f}".format(pheight=np.max(ref_deconv), ploc=deconv_zShift))

        deconvolved = restoration.richardson_lucy(dadz, w_z, num_iter=Step, clip=False)  # * sum_dadz
        peaks, _ = find_peaks(deconvolved)

        axs[1, 0].plot(z[:-1] - deconv_zShift, deconvolved,
                       label="Deconvolved with " + str(Step) + " Iterations")  # Plot some data on the axes.

        outp = ""
        print("Deconvolvable to {n_peaks} peaks".format(n_peaks=len(peaks)))
        for peak in peaks:
            outp = outp + "{tim:.4f};{R:.4f};".format(tim=z[peak] - deconv_zShift, R=deconvolved[peak])
            # outp = outp + "{tim:.4f};{R:.4f};".format(tim=z[peak] - deconv_zShift, R=deconvolved[peak] * (zth[-1] / np.sum(peaks)))
        print(outp)

        # dadz_conv = (np.convolve(deconvolved, w_z, "same") / np.sum(deconvolved)) * (z[2] - z[1])
        dadz_conv = (np.convolve(deconvolved, w_z, "same")) * (z[2] - z[1])
        Zth_Conv = (np.cumsum(dadz_conv) / np.sum(deconvolved)) * Rth_Stat + a_z[0]

        axs[0, 1].plot(z, dadz_conv, label="da/dz " + str(Step) + " Iterations")  # Plot some data on the axes.
        axs[1, 1].plot(z[:-1] - deconv_zShift, dadz - dadz_conv[:-1], label="Delta da/dz " + str(Step) + " Iterations")  # Plot some data on the axes.
        axs[0, 0].loglog(np.exp(z), Zth_Conv, label="Reconstructed Zth " + str(Step) + " Iterations")  # Plot some data on the axes.
        axs[2, 0].plot(z - deconv_zShift, Zth_Conv - a_z, label="Delta Zth " + str(Step) + " Iterations")  # Plot some data on the axes.

    axs[0, 0].legend()
    axs[0, 0].grid(which='both')

    axs[0, 1].set_title("Interpolated time constant spectrum")
    axs[1, 0].legend()
    axs[1, 0].grid(which='both')

    axs[2, 0].legend()
    axs[2, 0].grid(which='both')

    axs[0, 1].grid(which='both')
    axs[0, 1].legend()

    axs[1, 1].grid(which='both')
    axs[1, 1].legend()

    plt.show()

    return peaks

