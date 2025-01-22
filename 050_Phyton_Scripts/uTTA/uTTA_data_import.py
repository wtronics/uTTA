import numpy as np                      # numpy 2.1.0
import numpy.dtypes                     # numpy 2.1.0
import tkinter as tk
from tkinter import filedialog as fd    # part of python 3.12.5
from tkinter import messagebox          # part of python 3.12.5
from dataclasses import dataclass
from collections import defaultdict
import configparser                     # part of python 3.12.5
import os                               # part of python 3.12.5

MCU_Clock = 72000000
TimerPrescaler = 9
TimerClock = MCU_Clock/TimerPrescaler


@dataclass
class DevCalibration:
    Name:   str
    Offset: float
    Lin_Gain: float
    Cub_Gain: float


def read_measurement_file(filename, calfilepath,  flag_raw_value_mode):

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

            if t3r_file_vers < 2.9:
                pga_calibration, pga_calibration,  = read_calfile(calfilepath)
                timebase_total, adc, temp, samp_decade, cooling_start_block, ch_names, dut_tsp_sensitivity = read_measurement_file_lt30(lines,
                                                                                                                                        pga_calibration,
                                                                                                                                        pga_calibration,
                                                                                                                                        flag_raw_value_mode)
            else:
                timebase_total, adc, temp, samp_decade, cooling_start_block, ch_names, dut_tsp_sensitivity = read_measurement_file_30up(lines,
                                                                                                                                        flag_raw_value_mode)
            return timebase_total, adc, temp, samp_decade, cooling_start_block, ch_names, dut_tsp_sensitivity
    return 0, 0, 0, 0, 0, 0, 0


def read_measurement_file_30up(lines, flag_raw_value_mode):
    num_lines = len(lines)
    adc = np.zeros((4, num_lines), numpy.float32)
    dut_tsp_sensitivity = np.zeros((3, 4), numpy.float32)
    ch_names = ["DUT", "Monitor1", "Monitor2"]
    adc_idx = 0
    temp_idx = 0
    start_time = ""
    tsamp_fast = 0
    tsamp_slow = 0
    cooling_start_block = 0
    t_heat = 0
    t_preheat = 0
    i_sen = 0.0
    voffs = np.zeros(2, numpy.float32)
    tsamp_fast = (1000000 * 4.0) / TimerClock
    tsamp_slow = (1000000 * 524288.0) / TimerClock
    samp_decade = 250
    max_divider = 17
    utta_cal_values = dict()
    cal_val_name = ""

    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        cells = line.split(";")
        # print(type(cells))
        if isinstance(cells, list):
            if not cells[0].isnumeric():
                match cells[0]:
                    case 'StartTime':
                        start_time = str(cells[1])
                    case 'StartDate':
                        start_date = str(cells[1])
                        print("Measurement Started " + start_date + " " + start_time)
                    case 'CH1 Name':
                        ch_names[0] = str(cells[1])
                        dut_tsp_sensitivity[0, 0] = float(cells[2]) / 1000000
                        dut_tsp_sensitivity[0, 1] = float(cells[3]) / 1000000
                        dut_tsp_sensitivity[0, 2] = float(cells[4]) / 1000000
                        print("CH1 Cal:    {Offs:.3f}V  ; Linear:   {Lin:.6f}V/K  ; Cubic: {Cub:.3f}".format(
                              Offs=dut_tsp_sensitivity[0, 0], Lin=dut_tsp_sensitivity[0, 1], Cub=dut_tsp_sensitivity[0, 2]))
                    case 'CH2 Name':
                        ch_names[1] = str(cells[1])
                        dut_tsp_sensitivity[1, 0] = float(cells[2]) / 1000000
                        dut_tsp_sensitivity[1, 1] = float(cells[3]) / 1000000
                        dut_tsp_sensitivity[1, 2] = float(cells[4]) / 1000000
                        print("CH2 Cal:    {Offs:.3f}V  ; Linear:   {Lin:.6f}V/K  ; Cubic: {Cub:.3f}".format(
                              Offs=dut_tsp_sensitivity[1, 0], Lin=dut_tsp_sensitivity[1, 1], Cub=dut_tsp_sensitivity[1, 2]))
                    case 'CH3 Name':
                        ch_names[2] = str(cells[1])

                        dut_tsp_sensitivity[2, 0] = float(cells[2]) / 1000000
                        dut_tsp_sensitivity[2, 1] = float(cells[3]) / 1000000
                        dut_tsp_sensitivity[2, 2] = float(cells[4]) / 1000000
                        print("CH3 Cal:    {Offs:.3f}V  ; Linear:   {Lin:.6f}V/K  ; Cubic: {Cub:.3f}".format(
                              Offs=dut_tsp_sensitivity[2, 0], Lin=dut_tsp_sensitivity[2, 1], Cub=dut_tsp_sensitivity[2, 2]))
                    case s if s.startswith('#CAL_DIFF'):    # Differential Amplifier Calibration
                        cal_val_name = str(cells[0]).replace("#CAL_", "")
                        utta_cal_values[cal_val_name] = dict()
                        utta_cal_values[cal_val_name]["Offset"] = float(cells[1])
                        utta_cal_values[cal_val_name]["Lin_Gain"] = float(cells[2])
                        utta_cal_values[cal_val_name]["Cub_Gain"] = float(cells[3])

                    case '#CAL_ADC_I':      # Heating Current Sense Calibration
                        cal_val_name = str(cells[0]).replace("#CAL_", "")
                        utta_cal_values[cal_val_name] = dict()
                        utta_cal_values[cal_val_name]["Offset"] = float(cells[1])
                        utta_cal_values[cal_val_name]["Lin_Gain"] = float(cells[2])
                        utta_cal_values[cal_val_name]["Cub_Gain"] = float(cells[3])

                    case s if s.startswith('#CAL_PA_'):
                        cal_val_name = str(cells[0]).replace("#CAL_", "")
                        utta_cal_values[cal_val_name] = dict()
                        utta_cal_values[cal_val_name]["Offset"] = float(cells[1])
                        utta_cal_values[cal_val_name]["Lin_Gain"] = float(cells[2])
                        utta_cal_values[cal_val_name]["Cub_Gain"] = float(cells[3])

                    case '#CAL_DAC_ISEN':    # ISense DAC Calibration needs to be divided by 1000000 because values are in µA
                        cal_val_name = str(cells[0]).replace("#CAL_", "")
                        utta_cal_values[cal_val_name] = dict()
                        utta_cal_values[cal_val_name]["Offset"] = float(cells[1]) / 1000000.0
                        utta_cal_values[cal_val_name]["Lin_Gain"] = float(cells[2]) / 1000000.0
                        utta_cal_values[cal_val_name]["Cub_Gain"] = float(cells[3]) / 1000000.0

                    case s if s.startswith('#CAL_DAC_OFF'):    # ISense DAC Calibration needs to be divided by 1000 because values are in m
                        cal_val_name = str(cells[0]).replace("#CAL_", "")
                        utta_cal_values[cal_val_name] = dict()
                        utta_cal_values[cal_val_name]["Offset"] = float(cells[1]) / 1000.0
                        utta_cal_values[cal_val_name]["Lin_Gain"] = float(cells[2]) / 1000.0
                        utta_cal_values[cal_val_name]["Cub_Gain"] = float(cells[3]) / 1000.0

                    case '#CAL_DAC_SPARE':  # Dummy calibration value for the spare DAC channel
                        cal_val_name = str(cells[0]).replace("#CAL_", "")
                        utta_cal_values[cal_val_name] = dict()
                        utta_cal_values[cal_val_name]["Offset"] = float(cells[1]) / 1000.0
                        utta_cal_values[cal_val_name]["Lin_Gain"] = float(cells[2]) / 1000.0
                        utta_cal_values[cal_val_name]["Cub_Gain"] = float(cells[3]) / 1000.0

                    case '#ISEN':
                        i_sen = float(cells[1]) / 1000000
                        print("SENSING: Sense Current was:    {isen:>7.2f}mA".format(isen=i_sen*1000))
                    case '#VOFFS0':
                        voffs[0] = float(cells[1]) / 1000
                    case '#VOFFS1':
                        voffs[1] = float(cells[1]) / 1000
                    case 'T_Preheat':
                        t_preheat = int(cells[1])
                    case 'T_Heat':
                        t_heat = int(cells[1])
                    case 'T_Cool':
                        t_cool = int(cells[1])
                        print("TIMING:   Preheating:    {tPreh:>7.2f}Min ; Heating:  {tHeat:>7.2f}Min ; Cooling:        {tCool:>7.2f}Min".format(
                              tPreh=t_preheat / 60, tHeat=t_heat / 60, tCool=t_cool / 60))
                        pga = np.zeros((num_lines,), numpy.int16)
                        temp = np.zeros((4, int(num_lines)), numpy.float32)
                        block_no = np.zeros((num_lines,), numpy.int16)
                    case '#B':
                        last_block_no = int(cells[1])
                    case '#BlockNo':
                        last_block_no = int(cells[1])
                    case '#P':
                        pga_now = int(cells[1])
                    case '#PGA':
                        pga_now = int(cells[1])
                    case '#T':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 10.0
                        temp_idx += 1
                    case '#TEMP':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 10.0
                        temp_idx += 1
                    case 'Cooling Start Block':
                        cooling_start_block = int(cells[1]) + 1

                    case 'Total Blocks':
                        total_blocks = int(cells[1])
                        print("BLOCKS:   Cool start block:  {CSB}    ; Total:        {TotBlocks}".format(CSB=cooling_start_block, TotBlocks=total_blocks))
                        # case 'Finished':
                        # print("Finishing time: " + str(cells[1]))
                    case 'ADC1':
                        cells[0] = ""
                    # dummy case to remove skipped line statement
                    case _:
                        print("Skipped line: " + line)
            else:
                if cells[0].isnumeric():
                    pga[adc_idx] = pga_now
                    block_no[adc_idx] = last_block_no
                    if flag_raw_value_mode == 0:
                        ch_pa = "PA_0{ch}".format(ch=int(pga_now))
                        ch_diff = "DIFF0"

                        adc[0, adc_idx] = ((float(cells[0]) * utta_cal_values[ch_pa]["Lin_Gain"]) + utta_cal_values[ch_pa]["Offset"] - voffs[0]) / \
                                           utta_cal_values[ch_diff]["Lin_Gain"]
                        for CellIdx in range(1, 4):  # copy the cells to the new array
                            if CellIdx == 3:    # scaling for the heating current channel
                                ch_pa = "ADC_I"
                                adc[CellIdx, adc_idx] = ((float(cells[CellIdx]) * utta_cal_values[ch_pa]["Lin_Gain"]) + utta_cal_values[ch_pa]["Offset"])
                            else:   # scaling 2 the 2 monitoring channels
                                ch_pa = "PA_{ch}0".format(ch=int(CellIdx))
                                ch_diff = "DIFF{ch}".format(ch=CellIdx)
                                adc[CellIdx, adc_idx] = ((float(cells[CellIdx]) * utta_cal_values[ch_pa]["Lin_Gain"]) + utta_cal_values[ch_pa]["Offset"] -
                                                         voffs[1]) / utta_cal_values[ch_diff]["Lin_Gain"]
                    else:
                        adc[0, adc_idx] = float(cells[0])
                        for CellIdx in range(1, 4):  # copy the cells to the new array
                            adc[CellIdx, adc_idx] = float(cells[CellIdx])
                    adc_idx += 1

    del lines
    del line
    del cells
    print(utta_cal_values)
    print("Channel Names: " + str(ch_names))

    temp = temp[:, 0:temp_idx + 1]
    adc = adc[:, 0:adc_idx]
    del adc_idx

    time_base_heating = np.arange(0.0, (cooling_start_block * samp_decade) * tsamp_slow, tsamp_slow, dtype=numpy.float64)
    timebase_total = np.copy(time_base_heating)

    # Create Timebase for all measurements
    for BlockIdx in range(cooling_start_block, total_blocks + 1):
        tb_start = timebase_total[-1]  # get the last element of the already existing timebase
        tb_increment = tsamp_fast * pow(2, (min(max_divider, BlockIdx - cooling_start_block)))
        tb_add = np.arange(tb_start + tb_increment, tb_start + (tb_increment * (samp_decade + 1)), tb_increment)

        timebase_total = np.append(timebase_total, tb_add)

    timebase_total = timebase_total / 1000000.0

    return timebase_total, adc, temp, samp_decade, cooling_start_block, ch_names, dut_tsp_sensitivity


# import a file of version less than 3.0
def read_measurement_file_lt30(lines,  pga_calibration, adc_calibration, flag_raw_value_mode):
    num_lines = len(lines)
    adc = np.zeros((4, num_lines), numpy.float32)
    dut_tsp_sensitivity = np.zeros((3, 4), numpy.float32)
    ch_names = ["DUT", "Monitor1", "Monitor2"]
    adc_idx = 0
    temp_idx = 0

    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        cells = line.split(";")
        # print(type(cells))
        if isinstance(cells, list):
            if not cells[0].isnumeric():

                match cells[0]:
                    case '#B':
                        last_block_no = int(cells[1])
                    case '#BlockNo':
                        last_block_no = int(cells[1])
                    case '#P':
                        pga_now = int(cells[1])
                    case '#PGA':
                        pga_now = int(cells[1])
                    case '#T':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 10.0
                        temp_idx += 1
                    case '#TEMP':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            temp[CellIdx - 1, temp_idx] = float(cells[CellIdx]) / 10.0
                        temp_idx += 1
                    case 'FileVersion':
                        t3r_file_vers = float(str(cells[1]))
                    case 'StartTime':
                        start_time = str(cells[1])
                    case 'StartDate':
                        start_date = str(cells[1])
                        print("Measurement Started " + start_date + " " + start_time)
                    case 'CH1 Name':
                        ch_names[0] = str(cells[1])
                        if t3r_file_vers > 2.1:
                            dut_tsp_sensitivity[0, 0] = float(cells[2]) / 1000000
                            dut_tsp_sensitivity[0, 1] = float(cells[3]) / 1000000
                            dut_tsp_sensitivity[0, 2] = float(cells[4]) / 1000000
                            print("CH1 Cal:    {Offs:.3f}V  ; Linear:   {Lin:.3f}V  ; Cubic: {Cub:.3f}".format(
                                Offs=dut_tsp_sensitivity[0, 0], Lin=dut_tsp_sensitivity[0, 1], Cub=dut_tsp_sensitivity[0, 2]))
                    case 'CH2 Name':
                        ch_names[1] = str(cells[1])
                        if t3r_file_vers > 2.1:
                            dut_tsp_sensitivity[1, 0] = float(cells[2]) / 1000000
                            dut_tsp_sensitivity[1, 1] = float(cells[3]) / 1000000
                            dut_tsp_sensitivity[1, 2] = float(cells[4]) / 1000000
                            print("CH2 Cal:    {Offs:.3f}V  ; Linear:   {Lin:.3f}V  ; Cubic: {Cub:.3f}".format(
                                Offs=dut_tsp_sensitivity[1, 0], Lin=dut_tsp_sensitivity[1, 1], Cub=dut_tsp_sensitivity[1, 2]))
                    case 'CH3 Name':
                        ch_names[2] = str(cells[1])
                        if t3r_file_vers > 2.1:
                            dut_tsp_sensitivity[2, 0] = float(cells[2]) / 1000000
                            dut_tsp_sensitivity[2, 1] = float(cells[3]) / 1000000
                            dut_tsp_sensitivity[2, 2] = float(cells[4]) / 1000000
                            print("CH2 Cal:    {Offs:.3f}V  ; Linear:   {Lin:.3f}V  ; Cubic: {Cub:.3f}".format(
                                Offs=dut_tsp_sensitivity[2, 0], Lin=dut_tsp_sensitivity[2, 1], Cub=dut_tsp_sensitivity[2, 2]))
                    case 'Tsamp,fast':
                        tsamp_fast = (1000000 * float(cells[1])) / TimerClock
                    case 'Tsamp,low':
                        tsamp_slow = (1000000 * float(cells[1])) / TimerClock
                    case 'Samples/Decade':
                        samp_decade = int(cells[1])
                        print(
                            "SAMPLING: Ts_fast:    {sampf:>7.2f}Hz  ; Ts_low:   {sampl:>7.2f}Hz  ; Samples/Decade: {SampDec:>7.2f}".format(
                                sampf=1000000 / tsamp_fast, sampl=1000000 / tsamp_slow, SampDec=samp_decade))
                    case 'Max. Divider':
                        max_divider = int(cells[1])
                    case 'T_Preheat':
                        t_preheat = int(cells[1])
                    case 'T_Heat':
                        t_heat = int(cells[1])
                    case 'T_Cool':
                        t_cool = int(cells[1])
                        print("TIMING:   Preheating:    {tPreh:>7.2f}Min ; Heating:  {tHeat:>7.2f}Min ; Cooling:        {tCool:>7.2f}Min".format(
                            tPreh=t_preheat / 60, tHeat=t_heat / 60, tCool=t_cool / 60))
                        pga = np.zeros((num_lines,), numpy.int16)
                        temp = np.zeros((4, int(num_lines)), numpy.float32)
                        block_no = np.zeros((num_lines,), numpy.int16)
                    case 'Cooling Start Block':
                        cooling_start_block = int(cells[1]) + 1

                    case 'Total Blocks':
                        total_blocks = int(cells[1])
                        print("BLOCKS:   Cool start block:  {CSB}    ; Total:        {TotBlocks}".format(CSB=cooling_start_block, TotBlocks=total_blocks))
                    # case 'Finished':
                    # print("Finishing time: " + str(cells[1]))
                    case 'ADC1':
                        cells[0] = ""
                    # dummy case to remove skipped line statement
                    case _:
                        print("Skipped line: " + line)
            else:
                if cells[0].isnumeric():
                    pga[adc_idx] = pga_now
                    block_no[adc_idx] = last_block_no
                    if flag_raw_value_mode == 0:
                        adc[0, adc_idx] = (float(cells[0]) * pga_calibration[1][pga_now]) + pga_calibration[0][pga_now]
                        for CellIdx in range(1, 4):  # copy the cells to the new array
                            adc[CellIdx, adc_idx] = (float(cells[CellIdx]) * adc_calibration[1][CellIdx]) + adc_calibration[0][CellIdx]
                    else:
                        adc[0, adc_idx] = float(cells[0])
                        for CellIdx in range(1, 4):  # copy the cells to the new array
                            adc[CellIdx, adc_idx] = float(cells[CellIdx])
                    adc_idx += 1

    del lines
    del line
    del cells

    print("Channel Names: " + str(ch_names))

    temp = temp[:, 0:temp_idx + 1]
    adc = adc[:, 0:adc_idx]
    del adc_idx

    time_base_heating = np.arange(0.0, (cooling_start_block * samp_decade) * tsamp_slow, tsamp_slow, dtype=numpy.float64)
    timebase_total = np.copy(time_base_heating)

    # Create Timebase for all measurements
    for BlockIdx in range(cooling_start_block, total_blocks + 1):
        tb_start = timebase_total[-1]  # get the last element of the already existing timebase
        tb_increment = tsamp_fast * pow(2, (min(max_divider, BlockIdx - cooling_start_block)))
        tb_add = np.arange(tb_start + tb_increment, tb_start + (tb_increment * (samp_decade + 1)), tb_increment)

        timebase_total = np.append(timebase_total, tb_add)

    timebase_total = timebase_total / 1000000.0

    return timebase_total, adc, temp, samp_decade, cooling_start_block, ch_names, dut_tsp_sensitivity


def read_calfile(filename):

    print("Reading calibration values from file: " + filename)
    config = configparser.ConfigParser()
    config.read_file(open(filename))

    pga_calibration = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], dtype=float)
    adc_calibration = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], dtype=float)

    for ChIdx in range(0, 4):
        if ChIdx == 0:
            for PGA_Idx in range(0, 4):
                pga_calibration[1][PGA_Idx] = float(config["ADC0_CAL_PGA_" + str(PGA_Idx)]["Gain"].replace(",", "."))
                pga_calibration[0][PGA_Idx] = float(config["ADC0_CAL_PGA_" + str(PGA_Idx)]["Offset"].replace(",", "."))
                print("Calibration Values for Ch{ChNo}.PGA{PGANo}: Gain: {Slope:.6f} V/Digit, Offset: {Offs:.6f} V".format(
                    ChNo=ChIdx,
                    PGANo=PGA_Idx,
                    Slope=pga_calibration[1][PGA_Idx],
                    Offs=pga_calibration[0][PGA_Idx]))
        else:
            adc_calibration[1][ChIdx] = float(config["ADC" + str(ChIdx) + "_CAL"]["Gain"].replace(",", "."))
            adc_calibration[0][ChIdx] = float(config["ADC" + str(ChIdx) + "_CAL"]["Offset"].replace(",", "."))
            print("Calibration Values for Ch{ChNo}:      Gain: {Slope:.6f} V/Digit, Offset: {Offs:.6f} V".format(ChNo=ChIdx,
                                                                                                                 Slope=adc_calibration[1][ChIdx],
                                                                                                                 Offs=adc_calibration[0][ChIdx]))
    diode_cal_values = []

    # look for Diode channel calibration values
    for sect in config.sections():

        if str(sect).startswith("$CHAN_"):
            print(sect)
            diode_val = DevCalibration
            diode_val.Name = str(sect).replace("$CHAN_", "")
            diode_val.Offset = float(config[str(sect)]["Offset"].replace(",", "."))
            diode_val.Lin_Gain = float(config[str(sect)]["Lin_Gain"].replace(",", "."))
            diode_val.Cub_Gain = float(config[str(sect)]["Quad_Gain"].replace(",", "."))
            print(diode_val)
            diode_cal_values.append(diode_val)

    return pga_calibration, adc_calibration, diode_cal_values


def write_diodes_to_calfile(filename, cal_value):
    print("Writing calibration values to file: " + filename)

    config = configparser.ConfigParser()
    config.read_file(open(filename))

    tsp_name = cal_value.Name
    cfg_section_name = "$CHAN_"+tsp_name
    print("Writing Channel " + tsp_name)

    tsp_offs = str(cal_value.Offset).replace(".", ",")
    tsp_lin = str(cal_value.Lin_Gain).replace(".", ",")
    tsp_cub = str(cal_value.Cub_Gain).replace(".", ",")
    print("Creating Cal Entry for Channel Name: {nam}, Offset {Offs}, Gain {Gain}".format(nam=tsp_name, Offs=tsp_offs, Gain=tsp_lin))

    if config.has_section(cfg_section_name):

        msgbox_ret = tk.messagebox.askquestion("Existing Calibration",
                                               "The channel '" + tsp_name + "' already exists.\n" +
                                               "Do you wish to overwrite existing values?", icon="warning",)
        if msgbox_ret == "yes":
            config.set(cfg_section_name, "Offset", value=tsp_offs)
            config.set(cfg_section_name, "Lin_Gain", value=tsp_lin)
            config.set(cfg_section_name, "Quad_Gain", value=tsp_cub)
    else:
        config.add_section(cfg_section_name)
        config.set(cfg_section_name, "Offset", value=tsp_offs)
        config.set(cfg_section_name, "Lin_Gain", value=tsp_lin)
        config.set(cfg_section_name, "Quad_Gain", value=tsp_cub)

    # save to a file
    with open(filename, 'w') as configfile:
        config.write(configfile)

    return


def select_file(heading, file_filter):
    # filetypes = (('Text Files', '*.txt'), ('T3R Measurement Files', '*.t3r'), ('All files', '*.*'))

    filename = fd.askopenfilename(
        title=heading,
        initialdir=os.path.realpath(__file__),
        filetypes=file_filter
    )
    return filename


def split_file_path(file_path):
    # get the filename including the file extension (should be the last value in the split tuple)
    data_file = os.path.basename(file_path).split('/')[-1]

    # get the file extension. Should be the last item when splitting the filename at the dots
    file_extension = data_file.split('.')[-1]

    data_file_no_ext = data_file.replace('.' + file_extension, '')
    file_path = os.path.dirname(file_path)
    return data_file, data_file_no_ext, file_path
