import numpy as np              # numpy 2.1.0


def write_diode_voltages(timebase, adc, headername, filename):
    dio_voltage_max_lines = len(timebase)
    diode_output = np.zeros(shape=(2, dio_voltage_max_lines))
    diode_output[0, ] = timebase[0:dio_voltage_max_lines]
    diode_output[1, ] = adc[0, 0:dio_voltage_max_lines]
    diode_output = np.transpose(diode_output)

    np.savetxt(filename, diode_output,
               delimiter='\t',
               fmt='%1.4e',
               newline='\n',
               header="Time\t" + str(headername))


def export_t3i_file(timebase, zth, headername, filename):
    zth_output = np.zeros(shape=(len(zth), len(zth[0])))
    zth_output[0, :] = timebase
    zth_output[1, :] = zth[0, :]
    zth_output[2, :] = zth[1, :]
    zth_output[3, :] = zth[2, :]
    zth_output = np.transpose(zth_output)
    np.savetxt(filename, zth_output,
               delimiter='\t',
               fmt='%1.6e',
               newline='\n',
               header="Time\t" + str(headername))
    del zth_output

def export_tdim_master_file(timebase, zth, meta_data, filename):
    print(meta_data)
    if meta_data is not None:
        header = "# Transient Dual Interface Measurement: {dutname}\n".format(dutname=meta_data["TSP0"]["Name"])
        header += "# Measurement Date: {datemeas}\n".format(datemeas=meta_data["StartDate"])
        header += "# Measurement Time: {tmeas}\n".format(tmeas=meta_data["StartTime"])
        header += "POWERSTEP    = {pheat:.3f}       # Power Dissipation [W].\n".format(pheat=meta_data["P_Heat"])
        header += "HEATSINKTEMP = 25.0           # Cold-plate temperature [degC].\n"
        header += "SENSITIVITY  = {sens:.3e}     # Temperature coefficient [V/K].\n".format(sens=meta_data["TSP0"]["LinGain"])
        header += "# Please note the sign convention: the temperature\n"
        header += "# coefficient (sensitivity) for diodes is negative!\n"
        header += "DATA\n"
        header += "#Time [s]        Usens [V]"

        tdim_data_limit = 49999
        t_reduce_data = 100     # above 100s data will be reduced to fit into the 49999 samples TDIM Master can handle
        reduce_data = 1
        reduce_above_idx = int(find_nearest(timebase, t_reduce_data))

        if reduce_data:
            zth_output = np.zeros(shape=(2, tdim_data_limit))
            zth_output[0, 0:reduce_above_idx-1] = timebase[0:reduce_above_idx-1]
            zth_output[1, 0:reduce_above_idx-1] = zth[0, 0:reduce_above_idx-1]
            print("Input Samples {nsamp}, Reduction Index {red_idx}".format(nsamp=len(zth[0]), red_idx=reduce_above_idx))

            zth_output[0, reduce_above_idx:] = compress_array(timebase[reduce_above_idx:-1], tdim_data_limit - reduce_above_idx)
            zth_output[1, reduce_above_idx:] = compress_array(zth[0, reduce_above_idx:-1], tdim_data_limit - reduce_above_idx)
        else:
            meas_len = min(len(zth[0]),
                           tdim_data_limit)  # limit the export length to 49999 because TDIM Master doesn't work with more lines
            zth_output = np.zeros(shape=(2, meas_len))
            zth_output[0, 0:meas_len] = timebase[0:meas_len]
            zth_output[1, 0:meas_len] = zth[0, 0:meas_len]

        zth_output = np.transpose(zth_output)

        np.savetxt(filename, zth_output,delimiter="  ", newline='\n',fmt='%1.8e',header=header, comments='')
        del zth_output


def export_zth_curve(timebase, zth, meta_data,samples_decade, filename):

    if not isinstance(samples_decade, int) or samples_decade <= 0:
        raise ValueError("Input 'samples_decade' must be a non-negative integer.")
    if samples_decade >= len(timebase):
        return

    if meta_data is not None:
        header = "# Transient Dual Interface Measurement: {dutname}\n".format(dutname=meta_data["TSP0"]["Name"])
        header += "# Measurement Date: {datemeas}\n".format(datemeas=meta_data["StartDate"])
        header += "# Measurement Time: {tmeas}\n".format(tmeas=meta_data["StartTime"])
        header += "# POWERSTEP    = {pheat:.3f}       # Power Dissipation [W].\n".format(pheat=meta_data["P_Heat"])
        header += "#Time [s]        Zth [K/W]"

        # build the basic timebase for one decade. This will be reused and multiplied by the corresponding decade
        sub_timebase = np.power(10.0, np.linspace(0, 1/samples_decade * (samples_decade-1), samples_decade))

        time_multiplier = -6.0
        interpol_timebase = []
        while(True):    # make a little do-while loop...
            timestep = np.power(10.0, time_multiplier)
            segment_timebase =  timestep * sub_timebase
            time_multiplier += 1
            interpol_timebase.extend(segment_timebase)

            if np.max(interpol_timebase) > np.max(timebase):
                break

        filtered_timebase = [tim for tim in interpol_timebase if tim < np.max(timebase)]
        zth_output = np.zeros(shape=(2, len(filtered_timebase)))
        zth_output[0, :] = filtered_timebase
        zth_output[1, :] = np.interp(filtered_timebase, timebase, zth[0, :])

        # print("Export Timebase:")
        # print(zth_output[0, :])
        zth_output = np.transpose(zth_output)
        np.savetxt(filename, zth_output,delimiter="  ", newline='\n',fmt='%1.4e',header=header, comments='')
        del zth_output

def compress_array(arr, length):

    if not isinstance(length, int) or length < 0:
        raise ValueError("Input 'length' must be a non-negative integer.")
    if length == 0:
        return []
    if length >= len(arr):
        return list(arr)  # returns the original array because the desired length is longer than the input length

    compressed_arr = []
    ratio = len(arr) / length

    for i in range(length):

        start_index = int(i * ratio)
        end_index = int((i + 1) * ratio)

        # Make sure the end index is within the range of the input array
        end_index = min(end_index, len(arr))

        segment = arr[start_index:end_index]
        if segment:
            compressed_arr.append(sum(segment) / len(segment))
        else:
            # In case segment is empty (should be impossible due to ratio calculation),
            # 0 is returned as a standard value
            compressed_arr.append(0)

    return compressed_arr

def find_nearest(arr, value):
    # Element in nd array `arr` closest to the scalar value `value`
    idx = np.abs(arr - value).argmin()
    return idx