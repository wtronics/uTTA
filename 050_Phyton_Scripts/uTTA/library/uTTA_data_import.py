#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    uTTA_data_import.py
Description:    Data import and calibration parsing utilities for uTTA measurements.
                Provides functionality to read measurement files (*.umf) and 
                device/channel calibration files (*.ucf).

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

from collections import defaultdict
import configparser
from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List
from tkinter import messagebox
import tkinter as tk
import numpy as np
import numpy.dtypes

MCU_Clock = 72000000
TimerPrescaler = 9
TimerClock = MCU_Clock / TimerPrescaler


@dataclass
class DevCalibration:
    """Holds calibration data for a single device channel.

    Args:
        Name (str): Name of the channel.
        Offset (float): Offset of the channel.
        Lin_Gain (float): Linear Gain of the channel in mV/K.
        Quad_Gain (float): Quadratic Gain of the channel mV/K².
    """

    Name: str
    Offset: float
    Lin_Gain: float
    Quad_Gain: float


@dataclass
class UTTAMetaData:
    """Holds device and measurement metadata for a measurement run.

    Args:
        SamplesPerDecade (int): Number of samples per decade. Defaults to 250.
        MaxDivider (int): Maximum sampling clock divider (2^17). Defaults to 17.
        Channels (Dict[str, Any]): Dictionary of channel calibration data.
        Measurement (Dict[str, Any]): Dictionary of measurement related metadata.
        Isense (float): TSP sense current in µA. Defaults to 0.0.
        Voffs (List[float]): Offset Voltages in mV (CH0, CH1-3). Defaults to [0.00, 0.00].
        CalData (Dict[str, Any]): Dictionary of device calibration data.
        TPreheat (int): Measurement preheating time in seconds.
        THeating (int): Measurement heating time in seconds.
        TCooling (int): Measurement cooling time in seconds.
        CoolingStartBlock (int): Data block containing start of cooling section.
        TotalBlocks (int): Total number of blocks within the measurement.
        FlagTSPCalibrationFile (bool): Indicates if file was created during TSP calibration.
    """

    SamplesPerDecade: int = 250
    MaxDivider: int = 17
    Channels: Dict[str, Any] = field(default_factory=dict)
    Measurement: Dict[str, Any] = field(default_factory=dict)
    Isense: float = 0.0
    Voffs: List[float] = field(default_factory=lambda: [0.00, 0.00])
    CalData: Dict[str, Any] = field(default_factory=dict)
    TPreheat: int = 0
    THeating: int = 0
    TCooling: int = 0

    CoolingStartBlock: int = 0
    TotalBlocks: int = 0

    FlagTSPCalibrationFile: bool = False


def read_measurement_file(filename: str, flag_raw_value_mode: int = 0, logger: logging.Logger | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, UTTAMetaData]:
    """Import function to read *.umf measurement files.
    Originally this function bundled a common import function for all file versions.
    As all old measurement files have been abandoned the old import functions have been deprecaded and removed.

    Args:
        filename (str): File path to the *.umf file including the extension.
        flag_raw_value_mode (int): Set to 1 to output unscaled ADC values. Defaults to 0.
        logger (logging.Logger | None): Logger for common logging. Defaults to None.

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray, UTTAMetaData]:
            timebase_total (np.ndarray): Calculated sample time for each sample.
            adc (np.ndarray): Scaled or unscaled values of each ADC channel.
            temp (np.ndarray): All temperature samples of Type K thermocouples.
            meta_data (UTTAMetaData): Metadata related to the measurement.
    """
    if logger is None:
        logger = logging.getLogger("dummy")
        logger.addHandler(logging.NullHandler())
        logger.propagate = False # Important: prevents forwarding to the root logger
    else:
        logger = logger

    with open(filename, "r", encoding="utf-8") as fil:
        lines = fil.readlines()

    num_lines = len(lines)

    if num_lines > 0:
        # Read file version from first line and determine processing strategy
        cells = lines[0].split(";")
        t3r_file_version = str(cells[1])
        t3r_file_vers = float(t3r_file_version)
        logger.info(f"File Version: {t3r_file_vers:.1f}")

        timebase_total, adc, temp, meta_data = read_measurement_file_30up(lines,
                                                                          flag_raw_value_mode,
                                                                          t3r_file_vers, logger=logger)

        return timebase_total, adc, temp, meta_data

    return np.empty((1, 1)), np.empty((4, 1)), np.empty((4, 1)), UTTAMetaData()


def read_measurement_file_30up(lines: list[str], flag_raw_value_mode: int,
                               umf_fileversion: float, logger: logging.Logger) -> tuple[np.ndarray, np.ndarray, np.ndarray, UTTAMetaData]:
    """Import function for *.umf measurement files version 3.0 and above.

    Args:
        lines (list[str]): Lines read from the measurement file.
        flag_raw_value_mode (int): Set to 1 to output unscaled ADC values.
        umf_fileversion (float): Version of the file being parsed.
        logger (logging.Logger): Logger for reporting status and errors.

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray, UTTAMetaData]:
            timebase_total (np.ndarray): Calculated sample time array.
            adc (np.ndarray): ADC channel data array.
            temp (np.ndarray): Thermocouple temperature samples array.
            meta_data (UTTAMetaData): Extracted measurement metadata.
    Raises:
        ValueError: If file structure or metadata is severely corrupted.
    """
    num_lines = len(lines)
    adc = np.zeros((4, int(num_lines)), dtype=np.float32)

    adc_idx = 0
    temp_idx = 0
    temp = np.zeros((4, int(num_lines)), dtype=np.float32)
    pga_now = 0
    pga: np.ndarray = np.zeros((num_lines,), dtype=np.int16)
    last_block_no = 0
    block_count = 0
    block_no: np.ndarray = np.zeros((num_lines,), dtype=np.int16)

    tsamp_fast = (1000000 * 4.0) / TimerClock
    tsamp_slow = (1000000 * 524288.0) / TimerClock
    adc_samples_in_block = 0

    meas_meta_data = UTTAMetaData()
    if umf_fileversion >= 3.3:      # Scaling to fix miscalculated thermocouple scaling in older file versions
        temp_divider = 1.0
    elif umf_fileversion >= 3.2:
        temp_divider = 4.0
    else:
        temp_divider = 8.0

    for line_num, line in enumerate(lines, 1):
        line = line.replace("\r", "").replace("\n", "")

        if not line:
            continue  # Skip empty lines

        cells = line.split(";")

        if isinstance(cells, list):
            if not cells[0].isnumeric():
                match cells[0]:
                    case "#B" | "#BlockNo":
                        if len(cells) > 1 and cells[1].isnumeric():
                            last_block_no = int(cells[1])
                            block_count += 1
                        else:
                            logger.error(f"Line {line_num}: Corrupted block number format '{line}'")
                            
                        if adc_samples_in_block > 0:
                            logger.warning(
                                f"Line {line_num}: Block {last_block_no - 1} ended with "
                                f"{adc_samples_in_block} missing samples."
                            )
                        adc_samples_in_block = meas_meta_data.SamplesPerDecade
                    case "#P" | "#PGA":
                        if len(cells) > 1 and cells[1].isnumeric():
                            pga_now = int(cells[1])
                        else:
                            logger.error(f"Line {line_num}: Corrupted PGA value '{line}'")
                    case "#T" | "#TEMP":
                        if len(cells) >= 5:
                            try:
                                for cell_idx in range(1, 5):
                                    temp[cell_idx - 1, temp_idx] = float(cells[cell_idx]) / temp_divider
                                temp_idx += 1
                            except ValueError:
                                logger.error(f"Line {line_num}: Non-numeric temperature values in '{line}'")
                        else:
                            logger.error(f"Line {line_num}: Insufficient columns for #TEMP record")
                    case "FileVersion":
                        meas_meta_data.Measurement["FileVersion"] = str(cells[1]) if len(cells) > 1 else ""
                    case "Device":
                        meas_meta_data.Measurement["DeviceVersion"] = str(cells[1]) if len(cells) > 1 else ""
                    case "StartTime":
                        meas_meta_data.Measurement["StartTime"] = str(cells[1]) if len(cells) > 1 else ""
                    case "StartDate":
                        meas_meta_data.Measurement["StartDate"] = str(cells[1]) if len(cells) > 1 else ""
                        logger.info(f"Measurement Started {meas_meta_data.Measurement.get('StartDate', '')} "
                                    f"{meas_meta_data.Measurement.get('StartTime', '')}")
                    case "CH1 Name":
                        meas_meta_data.Channels["TSP0"] = __get_channel_data(0, cells, logger)
                    case "CH2 Name":
                        meas_meta_data.Channels["TSP1"] = __get_channel_data(1, cells, logger)
                    case "CH3 Name":
                        meas_meta_data.Channels["TSP2"] = __get_channel_data(2, cells, logger)
                    case "#CAL_DAC_ISEN":
                        if len(cells) >= 4:
                        # Convert values in µA to base units
                            meas_meta_data.CalData["CAL_DAC_ISEN"] = {"Offset": float(cells[1]) / 1000000.0,
                                                                    "LinGain": float(cells[2]) / 1000000.0,
                                                                    "QuadGain": float(cells[3]) / 1000000.0
                                                                    }

                    case s if s.startswith("#CAL_DAC_OFF"):
                        if len(cells) >= 4:
                            meas_meta_data.CalData[str(cells[0]).replace("#", "")] = {"Offset": float(cells[1]) / 1000.0,
                                                                                    "LinGain": float(cells[2]) / 1000.0,
                                                                                    "QuadGain": float(cells[3]) / 1000.0
                                                                                    }

                    case s if s.startswith("#CAL_"):
                        if len(cells) >= 4:
                            meas_meta_data.CalData[str(cells[0]).replace("#", "")] = {"Offset": float(cells[1]),
                                                                                    "LinGain": float(cells[2]),
                                                                                    "QuadGain": float(cells[3])
                                                                                    }

                    case "#ISEN":
                        if len(cells) > 1:
                            meas_meta_data.Isense = float(cells[1]) / 1000000
                            logger.info(f"SENSING: Sense Current was:    {meas_meta_data.Isense * 1000:>7.2f}mA")
                    case "#VOFFS0":
                        if len(cells) > 1:
                            meas_meta_data.Voffs[0] = float(cells[1]) / 1000
                    case "#VOFFS1":
                        if len(cells) > 1:
                            meas_meta_data.Voffs[1] = float(cells[1]) / 1000
                    case "T_Preheat":
                        if len(cells) > 1:
                            meas_meta_data.TPreheat = int(cells[1])
                    case "T_Heat":
                        if len(cells) > 1:
                            meas_meta_data.THeating = int(cells[1])
                            meas_meta_data.FlagTSPCalibrationFile = (int(cells[1]) == 0)

                    case "T_Cool":
                        if len(cells) > 1:
                            meas_meta_data.TCooling = int(cells[1])
                            logger.info(f"TIMING:   Preheating:    {meas_meta_data.TPreheat / 60:>7.2f}Min ; "
                                        f"Heating:  {meas_meta_data.THeating / 60:>7.2f}Min ; "
                                        f"Cooling:  {meas_meta_data.TCooling / 60:>7.2f}Min")

                    case "Cooling Start Block":
                        if len(cells) > 1:
                            meas_meta_data.CoolingStartBlock = int(cells[1]) + 1

                    case "Total Blocks":
                        if len(cells) > 1:
                            meas_meta_data.TotalBlocks = int(cells[1])
                            logger.info(f"BLOCKS:   Cool start block:  {meas_meta_data.CoolingStartBlock}    ; Total:        {meas_meta_data.TotalBlocks}")
                            if meas_meta_data.CoolingStartBlock > meas_meta_data.TotalBlocks:
                                meas_meta_data.CoolingStartBlock = meas_meta_data.TotalBlocks
                                meas_meta_data.FlagTSPCalibrationFile = True

                    case "ADC1":        # dummy case to remove skipped line statement
                        pass
                    case _:
                        logger.info(f"Skipped line: {line}")
            else:
                # Processing numeric ADC sample lines
                if len(cells) < 4:
                    logger.error(f"Line {line_num}: Incomplete data row '{line}' (expected 4 values, got {len(cells)})")
                    continue
                try: 
                    raw_values = [float(c) for c in cells[:4]]
                except ValueError as err:
                    logger.error(f"Line {line_num}: Non-numeric sample data found in '{line}'")
                    raise ValueError(f"Line {line_num}: Invalid numeric format in '{line}'") from err


                pga[adc_idx] = pga_now
                adc_samples_in_block -= 1
                block_no[adc_idx] = last_block_no

                if flag_raw_value_mode == 0:
                    ch_pa = f"CAL_PA_0{int(pga_now)}"
                    ch_diff = "CAL_DIFF0"

                    # Check calibration metadata availability to avoid KeyError
                    if ch_pa not in meas_meta_data.CalData or ch_diff not in meas_meta_data.CalData:
                        raise ValueError(f"Line {line_num}: Missing required calibration factors ({ch_pa} or {ch_diff}) in file header.")

                    adc[0, adc_idx] = ((float(cells[0]) * meas_meta_data.CalData[ch_pa]["LinGain"])
                                        + meas_meta_data.CalData[ch_pa]["Offset"] 
                                        - meas_meta_data.Voffs[0]
                                        ) / meas_meta_data.CalData[ch_diff]["LinGain"]

                    for cell_idx in range(1, 4):
                        if cell_idx == 3:
                            ch_pa = "CAL_ADC_I"
                            if ch_pa not in meas_meta_data.CalData:
                                raise ValueError(f"Line {line_num}: Missing calibration factor '{ch_pa}' in file header.")
                            
                            adc[cell_idx, adc_idx] = ((float(cells[cell_idx]) * meas_meta_data.CalData[ch_pa]["LinGain"])
                                                        + meas_meta_data.CalData[ch_pa]["Offset"])
                        else:
                            ch_pa = f"CAL_PA_{int(cell_idx)}0"
                            ch_diff = f"CAL_DIFF{cell_idx}"

                            if ch_pa not in meas_meta_data.CalData or ch_diff not in meas_meta_data.CalData:
                                raise ValueError(f"Line {line_num}: Missing required calibration factors ({ch_pa} or {ch_diff}) in header.")
                        
                            adc[cell_idx, adc_idx] = ((float(cells[cell_idx]) * meas_meta_data.CalData[ch_pa]["LinGain"])
                                                        + meas_meta_data.CalData[ch_pa]["Offset"]
                                                        - meas_meta_data.Voffs[1]
                                                        ) / meas_meta_data.CalData[ch_diff]["LinGain"]
                else:
                    adc[:, adc_idx] = raw_values
                adc_idx += 1

    # Truncate arrays to actual recorded sample lengths
    temp = temp[:, 0:temp_idx]
    adc = adc[:, 0:adc_idx]

    # Post-validation checks
    if meas_meta_data.TotalBlocks == 0:
        raise ValueError("File validation failed: 'Total Blocks' metadata missing or set to 0.")

    if meas_meta_data.CoolingStartBlock == 0:
        raise ValueError("File header corrupted: 'Cooling Start Block' is missing or 0.")
    
    if block_count != (meas_meta_data.TotalBlocks +1 ):
        raise ValueError(f"File truncated: Expected {meas_meta_data.TotalBlocks} blocks, but found only {block_count} blocks.")

    # Timebase calculation
    time_base_heating = np.arange(0.0, (meas_meta_data.CoolingStartBlock * meas_meta_data.SamplesPerDecade) * tsamp_slow, tsamp_slow, dtype=np.float64)
    timebase_total = np.copy(time_base_heating)

    # Create Timebase for all measurements
    for block_idx in range(meas_meta_data.CoolingStartBlock, meas_meta_data.TotalBlocks + 1):
        tb_start = timebase_total[-1]
        tb_increment = tsamp_fast * pow(2, min(meas_meta_data.MaxDivider, block_idx - meas_meta_data.CoolingStartBlock))
        tb_add = np.arange(tb_start + tb_increment, tb_start + (tb_increment * (meas_meta_data.SamplesPerDecade + 1)), tb_increment)

        timebase_total = np.append(timebase_total, tb_add)

    timebase_total = timebase_total / 1000000.0

    validate_meta_data_schema(meas_meta_data)

    return timebase_total, adc, temp, meas_meta_data


def __get_channel_data(ch_index: int, cells: List[str], logger: logging.Logger) -> dict[str, Any]:
    """ Parses channel metadata from header line cells with strict validation.

        Args:
            ch_index (int): Channel index identifier (e.g., 0 for CH1).
            cells (list[str]): Splitted CSV line cells for the channel entry.
            logger (logging.Logger): Logger instance for error reporting.

        Returns:
            dict[str, Any]: Parsed channel dictionary with standardized keys.

        Raises:
            ValueError: If essential channel parameters are missing or malformed.
    """
    # Expected minimum columns: 'CHx Name', Name, Offset, Linear, Quadratic
    min_required_cells = 6

    if len(cells) < min_required_cells:
        logger.error(f"Channel {ch_index + 1} metadata incomplete: expected at least {min_required_cells} fields, got {len(cells)}.")
        raise ValueError(f"Corrupted header: Channel {ch_index + 1} metadata is incomplete.")

    channel_name = cells[1].strip()
    if not channel_name:
        logger.warning(f"Channel {ch_index + 1} has an empty name string.")

    try:
        offset = float(cells[2]) / 1000000.0
        linear = float(cells[3]) / 1000000.0
        quadratic = float(cells[4]) / 1000000.0
        status = int(cells[5])

        if not (0 <= status <=2):
            raise ValueError(f"Invalid calibration status value for channel {ch_index + 1}.")
    except ValueError as err:
        logger.error(f"Channel {ch_index + 1} ('{channel_name}') contains non-numeric calibration values: {cells[2:min_required_cells]}")
        raise ValueError(f"Invalid numeric calibration format for channel {ch_index + 1}.") from err

    logger.info(f"CH{ch_index} Cal: {offset:>8.3f}V ; Linear: {linear:>11.6f}V/K ; Quadratic: {quadratic:>8.3f}")

    return {"Name": channel_name,
            "Offset": offset,
            "LinGain": linear,
            "QuadGain": quadratic,
            "CalStatus": status,
            }

def validate_meta_data_schema(meta_data: UTTAMetaData) -> None:
    """ Validates that all required keys are present in the generated metadata dictionaries.

    Args:
        meta_data (UTTAMetaData): The generated metadata structure to check.

    Raises:
        ValueError: If any required key is missing from the dictionaries.
    """
    required_measurement_keys = [
        "FileVersion",
        "DeviceVersion",
        "StartTime",
        "StartDate",
    ]

    for key in required_measurement_keys:
        if key not in meta_data.Measurement or not meta_data.Measurement[key]:
            raise ValueError(f"Generated metadata is incomplete: Missing required key '{key}' in Measurement dictionary.")

    required_cal_keys = ["CAL_DAC_ISEN", "CAL_DAC_SPARE",
                         "CAL_DAC_OFF0", "CAL_DAC_OFF1",
                         "CAL_DIFF0", "CAL_DIFF1", "CAL_DIFF2", "CAL_DIFF3",
                         "CAL_PA_00", "CAL_PA_01", "CAL_PA_02", "CAL_PA_03",
                         "CAL_PA_10", "CAL_PA_20", "CAL_PA_30",
                         "CAL_ADC_I" ]

    for key in required_cal_keys:
        if key not in meta_data.CalData or not meta_data.CalData[key]:
            raise ValueError(f"Generated metadata is incomplete: Missing required key '{key}' in Measurement dictionary.")

    required_channel_keys = [ "TSP0", "TSP1", "TSP2"]

    for key in required_channel_keys:
        if key not in meta_data.Channels or not meta_data.Channels[key]:
            raise ValueError(f"Generated metadata is incomplete: Missing required key '{key}' in Channels dictionary.")


    for ch_name, ch_data in meta_data.Channels.items():
        if ("LinGain" not in ch_data 
            or "Offset" not in ch_data 
            or "QuadGain" not in ch_data
            or "Name" not in ch_data
            or "CalStatus" not in ch_data
            ):
            raise ValueError(f"Generated metadata for channel '{ch_name}' is missing calibration parameters.")

def read_calfile2dict(filename: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Imports a uTTA calibration file (*.ucf) into dictionaries.
    Dictionaries for:
        - uTTA Device Calibration Data
        - uTTA Device Meta Data
        - TSP Calibration data from a Junction under Test (JUT)
        - Thermocouple calibration data (mostly not used)

    Args:
        filename (str): Path to the uTTA calibration file.

    Returns:
        tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
            utta_cal_data (dict[str, Any]): Device channel calibration factors.
            utta_dev_meta_data (dict[str, Any]): Device metadata.
            utta_tsp_cal (dict[str, Any]): Junction under test TSP calibration data.
            utta_tc_cal (dict[str, Any]): Thermocouple calibration data.
    """
    print("Reading calibration values from file: " + filename)
    config = configparser.ConfigParser()
    config.optionxform = str  # type: ignore # set configparser to Case-Sensitive

    with open(filename, "r", encoding="utf-8") as cal_file:
        config.read_file(cal_file)

    utta_cal_data: dict[str, Any] = {}
    utta_dev_meta_data: dict[str, Any] = {}
    utta_tc_cal: dict[str, Any] = {}
    utta_tsp_cal: dict[str, Any] = {}

    for sect in config.sections():
        match sect:
            case s if s.startswith("$CHAN_"):
                diode_val = {"Offset": float(config[str(sect)]["Offset"].replace('"', "")),
                             "LinGain": float(config[str(sect)]["LinGain"].replace('"', "")),
                             "QuadGain": float(config[str(sect)]["QuadGain"].replace('"', "")),
                            }
                if calstat := config[str(sect)].get("CalStatus"):
                    diode_val["CalStatus"] = int(calstat)
                else:  # channels with no CalStatus are assumed to be uncalibrated
                    diode_val["CalStatus"] = 0

                utta_tsp_cal[str(sect)] = diode_val
            case s if s.startswith("$TC_"):
                tc_cal = {"Offset": float(config[str(sect)]["Offset"].replace('"', "")),
                          "LinGain": float(config[str(sect)]["LinGain"].replace('"', "")),
                          "QuadGain": float(config[str(sect)]["QuadGain"].replace('"', ""))}
                utta_tc_cal[str(sect)] = tc_cal
            case "DEVICE_INFO":
                utta_dev_meta_data["DEVICE_INFO"] = dict(config["DEVICE_INFO"])
            case _:
                utta_cal = {"Offset": float(config[str(sect)]["Offset"].replace('"', "")),
                           "LinGain": float(config[str(sect)]["LinGain"].replace('"', "")),
                           "QuadGain": float(config[str(sect)]["QuadGain"].replace('"', ""))}
                utta_cal_data[str(sect)] = utta_cal

    return utta_cal_data, utta_dev_meta_data, utta_tsp_cal, utta_tc_cal


def write_tsp_cal_to_file(filename: str, tsp_cal: dict[str, Any]) -> None:
    """Writes TSP calibration data to a uTTA calibration file (*.ucf).

    Args:
        filename (str): Path to the uTTA calibration file.
        tsp_cal (dict[str, Any]): Dictionary of TSP calibration data.
    """
    print(f"Writing calibration values to file: {filename}")

    config = configparser.ConfigParser()
    config.optionxform = str  # type: ignore # set configparser to Case-Sensitive

    with open(filename, "r", encoding="utf-8") as cal_file:
        config.read_file(cal_file)

    for tsp_name, tsp in tsp_cal.items():
        tsp_offs = f'"{tsp["Offset"]:.6e}"'
        tsp_lin = f'"{tsp["LinGain"]:.6e}"'
        tsp_quad = f'"{tsp["QuadGain"]:.6e}"'

        print(f"Creating Cal Entry for Channel Name: {tsp_name}, Offset {tsp_offs}, "
              f"Gain {tsp_lin}, QuadGain {tsp_quad}, CalStat {tsp['CalStatus']}")

        if config.has_section(tsp_name):
            msgbox_ret = messagebox.askquestion("Existing Calibration",
                                                f"The channel '{tsp_name.replace('$CHAN_', '')}' already exists.\n"
                                                "Do you wish to overwrite existing values?",
                                                icon="warning")
            if msgbox_ret == "yes":
                config.set(tsp_name, "Offset", value=tsp_offs)
                config.set(tsp_name, "LinGain", value=tsp_lin)
                config.set(tsp_name, "QuadGain", value=tsp_quad)
                if tsp_name.startswith("$CHAN_"):
                    config.set(tsp_name, "CalStatus", value=str(tsp["CalStatus"]))
        else:
            config.add_section(tsp_name)
            config.set(tsp_name, "Offset", value=tsp_offs)
            config.set(tsp_name, "LinGain", value=tsp_lin)
            config.set(tsp_name, "QuadGain", value=tsp_quad)
            if tsp_name.startswith("$CHAN_"):
                config.set(tsp_name, "CalStatus", value=str(tsp["CalStatus"]))

        # save to a file
        with open(filename, "w", encoding="utf-8") as configfile:
            config.write(configfile)
