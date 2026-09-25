#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    uTTA_data_export.py
Description:    uTTA Data exporting utilities.
                This is a collection of export functions for various tasks:
                - Export of raw diode voltages.
                - Generation of t3i-files as intermediate files between uTTA_Postprocess_Measurement_GUI and uTTA_Zth_Comparison_GUI.
                - TDIM-Master measurement files to be directly importable into JESD51-14 TDIM Master Software.

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

from typing import Any
import numpy as np
import library.uTTA_data_processing as ud_proc



def write_diode_voltages(timebase: np.ndarray, adc: np.ndarray, headername: str, filename: str) -> None:
    """Writes raw diode voltages of the cooling curve to a tab-separated text file.

    Only exports the diode voltage of the heated diode.

    Args:
        timebase (np.ndarray): Raw measurement timebase array.
        adc (np.ndarray): Raw measurement data matrix of the heated TSP.
        headername (str): Label for the heated TSP column header.
        filename (str): Target export file path including extension.
    """
    dio_voltage_max_lines = len(timebase)
    diode_output = np.zeros(shape=(2, dio_voltage_max_lines))
    diode_output[0, :] = timebase[0:dio_voltage_max_lines]
    diode_output[1, :] = adc[0, 0:dio_voltage_max_lines]
    diode_output = np.transpose(diode_output)

    np.savetxt(filename, diode_output, delimiter="\t", fmt="%1.4e", newline="\n", header=f"Time\t{headername}")


def export_t3i_file(timebase: np.ndarray, zth: np.ndarray, headername: str, filename: str) -> None:
    """Exports processed Zth curves for all channels to a tab-separated text file.

    Generates intermediate files formatted with dot decimal separators.
    This file includes all three measurement channels, even when these channels were set to OFF in the Application GUI.

    Args:
        timebase (np.ndarray): Timebase array of the Zth curve.
        zth (np.ndarray): Matrix containing processed Zth data for all channels.
        headername (str): Channel header description text.
        filename (str): Target export path (typically *.t3i).
    """
    zth_output = np.zeros(shape=(len(zth) + 1, len(zth[0])))
    zth_output[0, :] = timebase
    zth_output[1, :] = zth[0, :]
    zth_output[2, :] = zth[1, :]
    zth_output[3, :] = zth[2, :]
    zth_output = np.transpose(zth_output)

    np.savetxt(filename, zth_output,
        delimiter="\t",
        fmt="%1.6e",
        newline="\n",
        header=f"Time\t{headername}")


def export_tdim_master_file(timebase: np.ndarray, zth: np.ndarray, meta_data: Any,
    p_heat: float, filename: str, tdim_data_limit: int = 49999,
    t_reduce_data: float = 100.0) -> None:
    """Exports measurement data compatible with the JESD51-14 TDIM Master software.

    Args:
        timebase (np.ndarray): Timebase array of the Zth curve.
        zth (np.ndarray): Matrix containing processed Zth data.
        meta_data (Any): Object or dict containing measurement metadata.
        p_heat (float): Calculated heating power in Watts.
        filename (str): Target export path (typically *.txt).
        tdim_data_limit (int): Maximum sample limit for TDIM Master. Defaults to 49999.
        t_reduce_data (float): Threshold time above which data is compressed. Defaults to 100.0.
    """
    if meta_data is not None:
        tsp0_name = meta_data.Channels["TSP0"]["Name"]
        start_date = meta_data.Measurement["StartDate"]
        start_time = meta_data.Measurement["StartTime"]
        lin_gain = meta_data.Channels["TSP0"]["LinGain"]

        header = f"# Transient Dual Interface Measurement: {tsp0_name}\n"
        header += f"# Measurement Date: {start_date}\n"
        header += f"# Measurement Time: {start_time}\n"
        header += f"POWERSTEP    = {p_heat:.3f}       # Power Dissipation [W].\n"
        header += "HEATSINKTEMP = 25.0           # Cold-plate temperature [degC].\n"
        header += f"SENSITIVITY  = {lin_gain:.3e}     # Temperature coefficient [V/K].\n"
        header += "# Please note the sign convention: the temperature\n"
        header += "# coefficient (sensitivity) for diodes is negative!\n"
        header += "DATA\n"
        header += "#Time [s]        Usens [V]"

        reduce_above_idx = int(ud_proc.find_nearest(timebase, t_reduce_data))

        if t_reduce_data > 0 and len(timebase) > reduce_above_idx:
            remaining_samples = max(0, tdim_data_limit - reduce_above_idx)
            compressed_time = compress_array(
                timebase[reduce_above_idx:-1], remaining_samples
            )
            compressed_zth = compress_array(
                zth[0, reduce_above_idx:-1], remaining_samples
            )

            time_concatenated = np.concatenate(
                (timebase[0:reduce_above_idx], compressed_time)
            )
            zth_concatenated = np.concatenate(
                (zth[0, 0:reduce_above_idx], compressed_zth)
            )

            zth_output = np.zeros(shape=(2, len(time_concatenated)))
            zth_output[0, :] = time_concatenated
            zth_output[1, :] = zth_concatenated
        else:
            meas_len = min(len(zth[0]), tdim_data_limit)
            zth_output = np.zeros(shape=(2, meas_len))
            zth_output[0, 0:meas_len] = timebase[0:meas_len]
            zth_output[1, 0:meas_len] = zth[0, 0:meas_len]

        zth_output = np.transpose(zth_output)

        np.savetxt(
            filename,
            zth_output,
            delimiter="  ",
            newline="\n",
            fmt="%1.8e",
            header=header,
            comments="",
        )

def export_zth_curve(timebase: np.ndarray, zth: np.ndarray, meta_data: Any, samples_decade: int, p_heat: float, filename: str) -> None:
    """Exports logarithmic-sampled Zth curves to a tab-separated text file.
    Decimal separator is point!

    Args:
        timebase (np.ndarray): Timebase array of the Zth curve.
        zth (np.ndarray): Matrix containing processed Zth data.
        meta_data (Any): Object or dict containing measurement metadata.
        samples_decade (int): Desired number of samples per decade.
        p_heat (float): Calculated heating power in Watts.
        filename (str): Target export path (typically *.txt).

    Raises:
        ValueError: If samples_decade is non-positive or not an integer.
    """
    if not isinstance(samples_decade, int) or samples_decade <= 0:
        raise ValueError("Input 'samples_decade' must be a non-negative integer.")
    if samples_decade >= len(timebase):
        return

    if meta_data is not None:
        tsp0_name = meta_data.Channels["TSP0"]["Name"]
        start_date = meta_data.Measurement["StartDate"]
        start_time = meta_data.Measurement["StartTime"]

        header = f"# Transient Dual Interface Measurement: {tsp0_name}\n"
        header += f"# Measurement Date: {start_date}\n"
        header += f"# Measurement Time: {start_time}\n"
        header += f"# POWERSTEP    = {p_heat:.3f}       # Power Dissipation [W].\n"
        header += "# Time [s]\tZth [K/W]"

        sub_timebase = np.power(10.0, np.linspace(0, 1 / samples_decade * (samples_decade - 1), samples_decade))

        time_multiplier = -6.0
        interpol_timebase: list[float] = []
        while True:
            timestep = np.power(10.0, time_multiplier)
            segment_timebase = timestep * sub_timebase
            time_multiplier += 1
            interpol_timebase.extend(segment_timebase.tolist())

            if np.max(interpol_timebase) > np.max(timebase):
                break

        max_time = float(np.max(timebase))
        filtered_timebase = [tim for tim in interpol_timebase if tim < max_time]
        zth_output = np.zeros(shape=(2, len(filtered_timebase)))
        zth_output[0, :] = filtered_timebase
        zth_output[1, :] = np.interp(filtered_timebase, timebase, zth[0, :])

        zth_output = np.transpose(zth_output)
        np.savetxt( filename, zth_output, delimiter="\t", newline="\n", fmt="%1.4e", header=header, comments="")


def compress_array(arr: np.ndarray, length: int) -> list[float] | np.ndarray:
    """Compresses a given input array into an array of a specified maximum length.

    If the input array is shorter than the desired length, the original array is returned.
    To compress, the algorithm splits the input array into equal segments and averages each.

    Args:
        arr (np.ndarray): One-dimensional input array to compress.
        length (int): Desired maximum output length.

    Returns:
        list[float] | np.ndarray: Compressed array as a list or original array.

    Raises:
        ValueError: If length is a negative integer.
    """
    if not isinstance(length, int) or length < 0:
        raise ValueError("Input 'length' must be a non-negative integer.")
    if length == 0:
        return []
    if length >= len(arr):
        return list(arr)

    compressed_arr: list[float] = []
    ratio = len(arr) / length

    for i in range(length):
        start_index = int(i * ratio)
        end_index = int((i + 1) * ratio)
        end_index = min(end_index, len(arr))

        segment = arr[start_index:end_index]
        if len(segment) == 0:
            compressed_arr.append(0.0)
        else:
            compressed_arr.append(float(np.mean(segment)))

    return compressed_arr