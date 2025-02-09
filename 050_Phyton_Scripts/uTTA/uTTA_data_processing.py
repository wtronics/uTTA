import numpy as np              # numpy 2.1.0
import numpy.dtypes             # numpy 2.1.0


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
