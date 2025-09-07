import matplotlib.pyplot as plt     # matplotlib 3.9.2
import time                         # part of python 3.12.5
import uTTA_data_processing as udpc

ExportDiodeVoltages = 0
ExportIntermediateFile = 1

udp = udpc.UttaZthProcessing()

FileNam = udpc.select_file("Select the measurement file",
                   (('uTTA Measurement File', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))

DataFile, DataFileNoExt, FilePath = udpc.split_file_path(FileNam)

start = time.time()

NoErrFlag = udp.import_data(FileNam)

if NoErrFlag and udp.meta_data.FlagTSPCalibrationFile:
    NoErrFlag = False
    print("\033[91mERROR: Seems like this measurement file contains a calibration measurement instead of a "
          "normal measurement. Analysis will be aborted!\033[0m")

if NoErrFlag:

    udp.calculate_cooling_curve()

    udp.calculate_diode_heating()

    udp.calculate_tsp_start_voltages()

    udp.interpolate_zth_curve_start()

    if ExportDiodeVoltages:
       udp.export_diode_voltages(FilePath + "\\" + DataFileNoExt + '_DiodeVoltages.txt')

    if ExportIntermediateFile:
      udp.export_t3i_file(FilePath + "\\" + DataFileNoExt + '.t3i')

    fig, axs = plt.subplots(nrows=4, ncols=2, layout="constrained")

    udp.add_input_tsp_measure_curve_plot(axs[0, 0])

    udp.add_input_current_measure_curve_plot(axs[0, 1])

    udp.add_tsp_measure_cooling_curve_plot(axs[1, 0])

    udp.add_cooling_curve_start_plot(axs[1, 1])
    # udp.add_current_measure_cooling_curve_plot(axs[1, 1])

    udp.add_diode_dt_curve_plot(axs[2, 0])

    udp.add_thermocouple_plot(axs[2, 1])

    udp.add_zth_curve_plot(axs[3, 0])

    udp.add_zth_coupling_curve_plot(axs[3, 1])

    end = time.time()
    print("Execution Time: {time:.3f}s".format(time=end - start))

    plt.show()
