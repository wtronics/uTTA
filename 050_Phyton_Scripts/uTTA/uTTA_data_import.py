import numpy as np                      # numpy 2.1.0
import numpy.dtypes                     # numpy 2.1.0
from tkinter import filedialog as fd    # part of python 3.12.5
import configparser                     # part of python 3.12.5
import os                               # part of python 3.12.5

MCU_Clock = 72000000
TimerPrescaler = 9
TimerClock = MCU_Clock/TimerPrescaler


def read_measurement_file(filename, pga_calibration, adc_calibration, flag_raw_value_mode):

    with open(filename, 'r') as fil:
        lines = fil.readlines()
        fil.close()
        num_lines = len(lines)
        # print("Number of Lines: " + str(num_lines))
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
                        case 'FileVersion':
                            t3r_file_version = str(cells[1])
                            t3r_file_vers = float(t3r_file_version)
                            print("File Version: {FileVers:.1f}".format(FileVers=t3r_file_vers))
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
                        case 'CH2 Name':
                            ch_names[1] = str(cells[1])
                            if t3r_file_vers > 2.1:
                                dut_tsp_sensitivity[1, 0] = float(cells[2]) / 1000000
                                dut_tsp_sensitivity[1, 1] = float(cells[3]) / 1000000
                                dut_tsp_sensitivity[1, 2] = float(cells[4]) / 1000000
                        case 'CH3 Name':
                            ch_names[2] = str(cells[1])
                            if t3r_file_vers > 2.1:
                                dut_tsp_sensitivity[2, 0] = float(cells[2]) / 1000000
                                dut_tsp_sensitivity[2, 1] = float(cells[3]) / 1000000
                                dut_tsp_sensitivity[2, 2] = float(cells[4]) / 1000000
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
    del CellIdx
    del pga
    del block_no

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
    return pga_calibration, adc_calibration


def select_file(heading, file_filter):
    # filetypes = (('Text Files', '*.txt'), ('T3R Measurement Files', '*.t3r'), ('All files', '*.*'))

    filename = fd.askopenfilename(
        title=heading,
        initialdir=os.path.realpath(__file__),
        filetypes=file_filter
    )
    return filename


def split_file_path(file_path, file_extension):
    data_file = os.path.basename(file_path).split('/')[-1]
    data_file_no_ext = data_file.replace(file_extension, '')
    file_path = os.path.dirname(file_path)
    return data_file, data_file_no_ext, file_path
