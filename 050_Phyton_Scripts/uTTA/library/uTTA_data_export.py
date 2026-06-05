#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    utta_data_export.py
Description:    uTTA Data exporting utilities
                This is a collection of export functions for various tasks:
                - Export of diode voltages
                - Generation of t3i-files as intermediate files between uTTA_Postprocess_Measurement_GUI and uTTA_Zth_Comparison_GUI
                - TDIM-Master measurement files to be directly importable into JESD51-14 TDIM Master Software

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           28.09.2025 (moved)
Version:        $VERSION$

--------------------------------------------------------------------------
License:
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0)

You are free to share and adapt this material under the following terms:
- Attribution: You must give appropriate credit.
- NonCommercial: You may not use the material for commercial purposes.
- ShareAlike: You must distribute your contributions under the same license.

The full license text can be found at:
https://creativecommons.org/licenses/by-nc-sa/4.0/
--------------------------------------------------------------------------
"""
import numpy as np
import pprint as pprint

def write_diode_voltages(timebase:np.ndarray, adc:np.ndarray, headername:str, filename:str) -> None:
    ''' Write the raw diode voltages of the cooling curve to a new tabulator separated
    text file. Only the diode voltage of the heated diode is exported.
    Args:
        timebase (np.ndarray)   : The raw measurement timebase of the cooling curve
        adc      (np.ndarray)   : Raw measurement data of the heated TSP
        headername   (string)   : How the heated TSP shall be called in the file header
        filename     (string)   : Complete export file path including file extension
    Returns:
        None
    '''
        
    dio_voltage_max_lines = len(timebase)
    diode_output = np.zeros(shape=(2, dio_voltage_max_lines))
    diode_output[0, ] = timebase[0:dio_voltage_max_lines]
    diode_output[1, ] = adc[0, 0:dio_voltage_max_lines]
    diode_output = np.transpose(diode_output)

    np.savetxt(filename, diode_output,
               delimiter='\t',
               fmt='%1.4e',
               newline='\n',
               header=f"Time\t{headername}")

def export_t3i_file(timebase:np.ndarray, zth:np.ndarray, headername:str, filename:str) -> None:
    ''' Exports the completely processed Zth curve (including start interpolation of the heated channel)
    to a tabulator separated text file. Decimal separation is point!
    This file includes all three measurement channels, even when these channels were set to OFF in the Application GUI.

    Args:
        timebase (np.ndarray)   : The measurement timebase of the zth curve
        zth      (np.ndarray)   : Processed and interpolated Zth data of all channels
        headername   (string)   : How the TSPs shall be called in the file header
        filename     (string)   : Complete export file path including file extension. The intended file extension is *.t3i
    Returns:
        None
    '''

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
               header=f"Time\t{headername}")
    del zth_output

def export_tdim_master_file(timebase:np.ndarray, zth:np.ndarray, meta_data,
                            p_heat:float, filename:str, tdim_data_limit:int=49999,
                            t_reduce_data:float=100.0) -> None:
    ''' Exports a text file which is compatible with the TDIM Master software supplied together with JESD51-14
    Args:
        timebase (np.ndarray)   : The measurement timebase of the zth curve
        zth      (np.ndarray)   : Processed and interpolated Zth data of all channels
        meta_data (meta_data)   : Measurement meta data 
        p_heat        (float)   : The heating power calculated during postprocessing
        filename     (string)   : Complete export file path including file extension. The intended file extension is *.txt
        tdim_data_limit (int)   : The maximum number of samples to be exported. TDIM Master accepts only 49999. Default: 49999
        t_reduce_data (float)   : Above this time the Zth curve gets reduced to fit into the maximum number of samples. Default: 100.0
    Returns:
        None
    '''
    if meta_data is not None:
        header = f"# Transient Dual Interface Measurement: {meta_data.Channels["TSP0"]["Name"]}\n"
        header += f"# Measurement Date: {meta_data.Measurement["StartDate"]}\n"
        header += f"# Measurement Time: {meta_data.Measurement["StartTime"]}\n"
        header += f"POWERSTEP    = {p_heat:.3f}       # Power Dissipation [W].\n"
        header += "HEATSINKTEMP = 25.0           # Cold-plate temperature [degC].\n"
        header += f"SENSITIVITY  = {meta_data.Channels["TSP0"]["LinGain"]:.3e}     # Temperature coefficient [V/K].\n"
        header += "# Please note the sign convention: the temperature\n"
        header += "# coefficient (sensitivity) for diodes is negative!\n"
        header += "DATA\n"
        header += "#Time [s]        Usens [V]"

        # above the reduction time, data will be reduced to fit into the 49999 samples TDIM Master can handle
        reduce_above_idx = int(find_nearest(timebase, t_reduce_data))

        if t_reduce_data > 0:
            zth_output = np.zeros(shape=(2, tdim_data_limit))
            zth_output[0, 0:reduce_above_idx] = timebase[0:reduce_above_idx]
            zth_output[1, 0:reduce_above_idx] = zth[0, 0:reduce_above_idx]

            zth_output[0, reduce_above_idx:] = compress_array(timebase[reduce_above_idx:-1], tdim_data_limit - reduce_above_idx)
            zth_output[1, reduce_above_idx:] = compress_array(zth[0, reduce_above_idx:-1], tdim_data_limit - reduce_above_idx)
        else:
            meas_len = min(len(zth[0]), tdim_data_limit)  # limit the export length to 49999 because TDIM Master doesn't work with more lines
            zth_output = np.zeros(shape=(2, meas_len))
            zth_output[0, 0:meas_len] = timebase[0:meas_len]
            zth_output[1, 0:meas_len] = zth[0, 0:meas_len]

        zth_output = np.transpose(zth_output)

        np.savetxt(filename, zth_output,delimiter="  ", newline='\n',fmt='%1.8e',header=header, comments='')
        del zth_output

def export_zth_curve(timebase:np.ndarray, zth:np.ndarray, meta_data, samples_decade:int, p_heat:float, filename:str) -> None:
    ''' Exports the Z_th curve of the heated JUT to a tabulator separated text file. Decimal separator is point!
    Args:
        timebase (np.ndarray)   : The measurement timebase of the zth curve
        zth      (np.ndarray)   : Processed and interpolated Zth data of all channels
        meta_data (meta_data)   : Measurement meta data 
        samples_decade  (int)   : Number of samples per decade to be exported
        p_heat        (float)   : The heating power calculated during postprocessing
        filename     (string)   : Complete export file path including file extension. The intended file extension is *.txt
    Returns:
        None
    '''

    if not isinstance(samples_decade, int) or samples_decade <= 0:
        raise ValueError("Input 'samples_decade' must be a non-negative integer.")
    if samples_decade >= len(timebase):
        return

    if meta_data is not None:
        header = f"# Transient Dual Interface Measurement: {meta_data.Channels["TSP0"]["Name"]}\n"
        header += f"# Measurement Date: {meta_data.Measurement["StartDate"]}\n"
        header += f"# Measurement Time: {meta_data.Measurement["StartTime"]}\n"
        header += f"# POWERSTEP    = {p_heat:.3f}       # Power Dissipation [W].\n"
        header += "# Time [s]\tZth [K/W]"

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

        zth_output = np.transpose(zth_output)
        np.savetxt(filename, zth_output,delimiter="\t", newline='\n',fmt='%1.4e',header=header, comments='')
        del zth_output

def compress_array(arr:np.ndarray, length:int) -> list[float]|np.ndarray:
    ''' Compress a given input array into an array of a maximum given length.
    If the input array is shorter than the desired lenght, the original array will be returned.
    To compress the array the algorithm splits the input array into N equal segments. All segments are averaged and filled into the output array.
    Args:
        arr      (np.ndarray)   : The one dimensional input array
        length   (int)          : Desired maximum output length
    Returns:
        (list[float]|np.ndarray)    : Compressed array
    '''
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
        # pprint.pprint(segment)
        if len(segment) == 0:
            # In case segment is empty (should be impossible due to ratio calculation),
            # 0 is returned as a standard value
            compressed_arr.append(0)
        else:
            compressed_arr.append(sum(segment) / len(segment))

    return compressed_arr

def find_nearest(arr:np.ndarray, value:float) -> np.intp:
    ''' Searches an array to find the array index of the value which is closest to the searched value.
    Args:
        arr      (np.ndarray)   : Array which shall be searched through
        value    (float)        : Value the which shall be searched for
    Returns:
        (np.intp)   : Index of the closest array element
    '''
    # Element in nd array `arr` closest to the scalar value `value`
    idx = np.abs(arr - value).argmin()
    return idx

