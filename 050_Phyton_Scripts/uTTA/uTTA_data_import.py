import numpy as np  # numpy 2.1.0
import numpy.dtypes  # numpy 2.1.0
import tkinter as tk
from tkinter import messagebox  # part of python 3.12.5
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List
import configparser  # part of python 3.12.5

MCU_Clock = 72000000
TimerPrescaler = 9
TimerClock = MCU_Clock / TimerPrescaler


@dataclass
class DevCalibration:
    Name: str
    Offset: float
    Lin_Gain: float
    Quad_Gain: float

@dataclass
class UTTAMetaData:
    SamplesPerDecade: int = 250
    MaxDivider: int = 17
    Channels: defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))
    Measurement: defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))
    Isense: float = None
    Voffs: List = field(default_factory=lambda: [0.00, 0.00])
    CalData: defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))
    TPreheat: int = None
    THeating: int = None
    TCooling: int = None

    CoolingStartBlock: int = None
    TotalBlocks: int = None

    FlagTSPCalibrationFile: bool = False
    FlagImportSuccessful: bool = False

def read_measurement_file(filename, flag_raw_value_mode):
    with open(filename, 'r') as fil:
        lines = fil.readlines()
        fil.close()
        num_lines = len(lines)

        if num_lines > 0:
            # read the file version from the first line and decide how to process the file
            cells = lines[0].split(";")
            t3r_file_version = str(cells[1])
            t3r_file_vers = float(t3r_file_version)
            print("File Version: {FileVers:.1f}".format(FileVers=t3r_file_vers))
            # print("Number of Lines: " + str(num_lines))

            timebase_total, adc, temp, meta_data = read_measurement_file_30up(lines,
                                                                              flag_raw_value_mode,
                                                                              t3r_file_vers)
            return timebase_total, adc, temp, meta_data
    return 0, 0, 0, {}


def read_measurement_file_30up(lines, flag_raw_value_mode, umf_fileversion):
    num_lines = len(lines)
    adc = np.zeros((4, num_lines), numpy.float32)

    adc_idx = 0
    temp_idx = 0
    temp = []
    pga_now = 0
    pga = []
    last_block_no = 0
    block_no = []

    tsamp_fast = (1000000 * 4.0) / TimerClock
    tsamp_slow = (1000000 * 524288.0) / TimerClock
    adc_samples_in_block = 0

    meas_meta_data = UTTAMetaData()

    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        cells = line.split(";")

        if isinstance(cells, list):
            if not cells[0].isnumeric():
                match cells[0]:
                    case 'StartTime':
                        meas_meta_data.Measurement["StartTime"] = str(cells[1])
                    case 'StartDate':
                        meas_meta_data.Measurement["StartDate"] = str(cells[1])
                        print("Measurement Started " + meas_meta_data.Measurement["StartDate"] + " " + meas_meta_data.Measurement["StartTime"])
                    case 'CH1 Name':
                        meas_meta_data.Channels["TSP0"] = get_channel_data(0, cells)

                    case 'CH2 Name':
                        meas_meta_data.Channels["TSP1"] = get_channel_data(1, cells)
                    case 'CH3 Name':
                        meas_meta_data.Channels["TSP2"] = get_channel_data(2, cells)
                    case '#CAL_DAC_ISEN':  # ISense DAC Calibration needs to be divided by 1000000 because values are in µA
                        meas_meta_data.CalData["CAL_DAC_ISEN"] = {"Offset": float(cells[1]) / 1000000.0,
                                                                  "LinGain": float(cells[2]) / 1000000.0,
                                                                  "QuadGain": float(cells[3]) / 1000000.0
                                                                  }

                    case s if s.startswith('#CAL_DAC_OFF'):
                        meas_meta_data.CalData[str(cells[0]).replace("#", "")] = {"Offset": float(cells[1]) / 1000.0,
                                                                          "LinGain": float(cells[2]) / 1000.0,
                                                                          "QuadGain": float(cells[3]) / 1000.0
                                                                          }

                    case s if s.startswith('#CAL_'):
                        print(str(cells[0]).replace("#", ""))
                        print(meas_meta_data.CalData)
                        meas_meta_data.CalData[str(cells[0]).replace("#", "")] = {"Offset": float(cells[1]),
                                                                          "LinGain": float(cells[2]),
                                                                          "QuadGain": float(cells[3])
                                                                          }

                    case '#ISEN':
                        meas_meta_data.Isense = float(cells[1]) / 1000000
                        print("SENSING: Sense Current was:    {isen:>7.2f}mA".format(isen=meas_meta_data.Isense * 1000))
                    case '#VOFFS0':
                        meas_meta_data.Voffs[0] = float(cells[1]) / 1000
                    case '#VOFFS1':
                        meas_meta_data.Voffs[1] = float(cells[1]) / 1000
                    case 'T_Preheat':
                        meas_meta_data.TPreheat = int(cells[1])
                    case 'T_Heat':
                        meas_meta_data.THeating = int(cells[1])
                        if int(cells[1]) == 0:
                            meas_meta_data.FlagTSPCalibrationFile = True
                        else:
                            meas_meta_data.FlagTSPCalibrationFile = False

                    case 'T_Cool':
                        meas_meta_data.TCooling = int(cells[1])
                        print("TIMING:   Preheating:    {tPreh:>7.2f}Min ; Heating:  {tHeat:>7.2f}Min ; Cooling:        {tCool:>7.2f}Min".format(
                            tPreh=meas_meta_data.TPreheat / 60, tHeat=meas_meta_data.THeating / 60, tCool=meas_meta_data.TCooling / 60))
                        pga = np.zeros((num_lines,), numpy.int16)
                        temp = np.zeros((4, int(num_lines)), numpy.float32)
                        block_no = np.zeros((num_lines,), numpy.int16)
                    case '#B':
                        last_block_no = int(cells[1])
                        if adc_samples_in_block > 0:
                            print("\033[92mERROR: Seems like the previous block ({bno}) did not have samples.".format(bno=last_block_no-1) +
                                  " There were {left} samples not filled!\033[0m".format(left=adc_samples_in_block))
                        adc_samples_in_block = meas_meta_data.SamplesPerDecade
                    case '#BlockNo':
                        last_block_no = int(cells[1])
                        if adc_samples_in_block > 0:
                            print("\033[92mERROR: Seems like the previous block ({bno}) did not have samples.".format(bno=last_block_no-1) +
                                  " There were {left} samples not filled!\033[0m".format(left=adc_samples_in_block))
                        adc_samples_in_block = meas_meta_data.SamplesPerDecade
                    case '#P':
                        pga_now = int(cells[1])
                    case '#PGA':
                        pga_now = int(cells[1])
                    case '#T':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            if umf_fileversion >= 3.3:
                                temp[CellIdx - 1, temp_idx] = float(cells[CellIdx])
                            elif umf_fileversion >= 3.2:
                                temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 4.0
                            else:
                                temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 8.0
                        temp_idx += 1
                    case '#TEMP':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            if umf_fileversion >= 3.3:
                                temp[CellIdx - 1, temp_idx] = float(cells[CellIdx])
                            elif umf_fileversion >= 3.2:
                                temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 4.0
                            else:
                                temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 8.0
                        temp_idx += 1
                    case 'Cooling Start Block':
                        meas_meta_data.CoolingStartBlock = int(cells[1]) + 1

                    case 'Total Blocks':
                        meas_meta_data.TotalBlocks = int(cells[1])
                        print("BLOCKS:   Cool start block:  {CSB}    ; Total:        {TotBlocks}".format(CSB=meas_meta_data.CoolingStartBlock,
                                                                                                         TotBlocks=meas_meta_data.TotalBlocks))
                        if meas_meta_data.CoolingStartBlock > meas_meta_data.TotalBlocks:
                            meas_meta_data.CoolingStartBlock = meas_meta_data.TotalBlocks
                            meas_meta_data.FlagTSPCalibrationFile = True

                    case 'ADC1':
                        cells[0] = ""
                    # dummy case to remove skipped line statement
                    case _:
                        print("Skipped line: " + line)
            else:
                if cells[0].isnumeric():
                    pga[adc_idx] = pga_now
                    adc_samples_in_block -= 1
                    block_no[adc_idx] = last_block_no
                    if flag_raw_value_mode == 0:
                        ch_pa = "CAL_PA_0{ch}".format(ch=int(pga_now))
                        ch_diff = "CAL_DIFF0"

                        adc[0, adc_idx] = ((float(cells[0]) * meas_meta_data.CalData[ch_pa]["LinGain"]) + meas_meta_data.CalData[ch_pa]["Offset"] -
                                           meas_meta_data.Voffs[0]) / meas_meta_data.CalData[ch_diff]["LinGain"]
                        for CellIdx in range(1, 4):  # copy the cells to the new array
                            if CellIdx == 3:  # scaling for the heating current channel
                                ch_pa = "CAL_ADC_I"
                                adc[CellIdx, adc_idx] = ((float(cells[CellIdx]) * meas_meta_data.CalData[ch_pa]["LinGain"]) + meas_meta_data.CalData[ch_pa]["Offset"])
                            else:  # scaling 2 the 2 monitoring channels
                                ch_pa = "CAL_PA_{ch}0".format(ch=int(CellIdx))
                                ch_diff = "CAL_DIFF{ch}".format(ch=CellIdx)
                                adc[CellIdx, adc_idx] = ((float(cells[CellIdx]) * meas_meta_data.CalData[ch_pa]["LinGain"]) + meas_meta_data.CalData[ch_pa]["Offset"] -
                                                         meas_meta_data.Voffs[1]) / meas_meta_data.CalData[ch_diff]["LinGain"]
                    else:
                        adc[0, adc_idx] = float(cells[0])
                        for CellIdx in range(1, 4):  # copy the cells to the new array
                            adc[CellIdx, adc_idx] = float(cells[CellIdx])
                    adc_idx += 1

    del lines
    del line
    del cells

    # print("Channel Names: " + str(ch_names))

    temp = temp[:, 0:temp_idx + 1]
    adc = adc[:, 0:adc_idx]
    del adc_idx
    if meas_meta_data.TotalBlocks != last_block_no:
        print(
            "\033[92mERROR: The number of total blocks ({bno}) does not match".format(bno=meas_meta_data.TotalBlocks) +
            " the actual number of blocks imported ({imported})\033[0m".format(imported=last_block_no))


    time_base_heating = np.arange(0.0, (meas_meta_data.CoolingStartBlock * meas_meta_data.SamplesPerDecade) * tsamp_slow, tsamp_slow, dtype=numpy.float64)
    timebase_total = np.copy(time_base_heating)

    # Create Timebase for all measurements
    for BlockIdx in range(meas_meta_data.CoolingStartBlock, meas_meta_data.TotalBlocks + 1):
        tb_start = timebase_total[-1]  # get the last element of the already existing timebase
        tb_increment = tsamp_fast * pow(2, (min(meas_meta_data.MaxDivider, BlockIdx - meas_meta_data.CoolingStartBlock)))
        tb_add = np.arange(tb_start + tb_increment, tb_start + (tb_increment * (meas_meta_data.SamplesPerDecade + 1)), tb_increment)

        timebase_total = np.append(timebase_total, tb_add)

    timebase_total = timebase_total / 1000000.0

    # print(meas_meta_data)
    return timebase_total, adc, temp, meas_meta_data


def get_channel_data(tsp_no, cells):
    channel = {}
    if 0 <= tsp_no <= 3:
        if len(cells) > 5:
            channel = {"Name": str(cells[1]),
                       "Offset": float(cells[2]) / 1000000,
                       "LinGain": float(cells[3]) / 1000000,
                       "QuadGain": float(cells[4]) / 1000000,
                       "CalStatus": int(cells[5])
                       }
        else:
            channel = {"Name": str(cells[1]),
                       "Offset": float(cells[2]) / 1000000,
                       "LinGain": float(cells[3]) / 1000000,
                       "QuadGain": float(cells[4]) / 1000000,
                       "CalStatus": 0
                       }
        print("CH{no} Cal:    {Offs:.3f}V  ; Linear:   {Lin:.6f}V/K  ; Quadratic: {Cub:.3f}".format(
            no=tsp_no-1,
            Offs=channel["Offset"],
            Lin=channel["LinGain"],
            Cub=channel["QuadGain"]))

    return channel



def read_calfile2dict(filename):
    print("Reading calibration values from file: " + filename)
    config = configparser.ConfigParser()
    config.optionxform = str  # set configparser to Case-Sensitive
    config.read_file(open(filename))

    utta_cal_data = {}  # dictionary for device calibration data
    utta_dev_meta_data = {}  # dictionary for device meta data
    utta_tc_cal = {}  # dictionary for thermocouple calibration data
    utta_tsp_cal = {}  # dictionary for TSP (temperature sensitive parameter)

    # look for Diode channel calibration values
    for sect in config.sections():
        match sect:
            case s if s.startswith('$CHAN_'):
                diode_val = {}

                diode_val["Offset"] = float(config[str(sect)]["Offset"].replace('"', ""))
                diode_val["LinGain"] = float(config[str(sect)]["LinGain"].replace('"', ""))
                diode_val["QuadGain"] = float(config[str(sect)]["QuadGain"].replace('"', ""))
                # CalStatus Parameter Definition:
                # 0 = Uncalibrated
                # 1 = Calibrated
                # 2 = Dummy
                if calstat := config[str(sect)].get("CalStatus"):
                    diode_val["CalStatus"] = int(calstat)
                else:  # channels with no CalStatus are assumed to be uncalibrated
                    diode_val["CalStatus"] = 0

                utta_tsp_cal[str(sect)] = diode_val
            case s if s.startswith('$TC_'):
                tc_cal = {}

                tc_cal["Offset"] = float(config[str(sect)]["Offset"].replace('"', ""))
                tc_cal["LinGain"] = float(config[str(sect)]["LinGain"].replace('"', ""))
                tc_cal["QuadGain"] = float(config[str(sect)]["QuadGain"].replace('"', ""))
                utta_tc_cal[str(sect)] = tc_cal
            case "DEVICE_INFO":
                utta_dev_meta_data["DEVICE_INFO"] = dict(config["DEVICE_INFO"])
            case _:
                utta_cal = {}
                utta_cal["Offset"] = float(config[str(sect)]["Offset"].replace('"', ""))
                utta_cal["LinGain"] = float(config[str(sect)]["LinGain"].replace('"', ""))
                utta_cal["QuadGain"] = float(config[str(sect)]["QuadGain"].replace('"', ""))
                utta_cal_data[str(sect)] = utta_cal

    return utta_cal_data, utta_dev_meta_data, utta_tsp_cal, utta_tc_cal


def write_tsp_cal_to_file(filename, tsp_cal):
    print("Writing calibration values to file: " + filename)

    config = configparser.ConfigParser()
    config.optionxform = str  # set configparser to Case-Sensitive
    config.read_file(open(filename))

    for tsp_name, tsp in tsp_cal.items():
        tsp_offs = '"{:.6e}"'.format(tsp["Offset"])
        tsp_lin = '"{:.6e}"'.format(tsp["LinGain"])
        tsp_quad = '"{:.6e}"'.format(tsp["QuadGain"])

        print("Creating Cal Entry for Channel Name: {nam}, Offset {Offs}, Gain {Gain}, QuadGain {QGain}, CalStat {CS}".
              format(nam=tsp_name, Offs=tsp_offs, Gain=tsp_lin, QGain=tsp_quad, CS=tsp["CalStatus"]))

        if config.has_section(tsp_name):
            msgbox_ret = tk.messagebox.askquestion("Existing Calibration",
                                                   "The channel '" + tsp_name.replace("$CHAN_", "") + "' already exists.\n" +
                                                   "Do you wish to overwrite existing values?", icon="warning", )
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
        with open(filename, 'w') as configfile:
            config.write(configfile)

    return
