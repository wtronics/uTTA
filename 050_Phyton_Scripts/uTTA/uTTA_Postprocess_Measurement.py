import numpy as np                  # numpy 2.1.0
import numpy.dtypes                 # numpy 2.1.0
import matplotlib.pyplot as plt     # matplotlib 3.9.2
import time                         # part of python 3.12.5
import os                           # part of python 3.12.5
import uTTA_data_import
import uTTA_data_processing
import uTTA_data_export

NoOfDUTs = 3
MaxDeltaT_StartEnd = 1.0

# Parameters for Interpolation
InterpolationTStart = 0.00030
InterpolationTEnd = 0.0025
#InterpolationTStart = 0.00020
#InterpolationTEnd = 0.0025
InterpolationAverageHW = 1   # Should be the half width of the averaged area

# Options for output files
ExportDiodeVoltages = 0
ExportIntermediateFile = 1


def find_nearest(arr, value):
    # Element in nd array `arr` closest to the scalar value `value`
    idx = np.abs(arr - value).argmin()
    return idx


FileNam = uTTA_data_import.select_file("Select the measurement file",
                                       (('uTTA Measurement File', '*.umf'),
                                        ('Text-Files', '*.txt'),
                                        ('All files', '*.*')))

DataFile, DataFileNoExt, FilePath = uTTA_data_import.split_file_path(FileNam)

start = time.time()

TimeBaseTotal, ADC, Temp, MetaData = uTTA_data_import.read_measurement_file(FileNam, 0)

ErrMeasFlag = False
if len(TimeBaseTotal) < 1:
    ErrMeasFlag = True
    print("Seems like this measurement file contains no useable data. Analysis will be aborted!")

if not MetaData["TSP_Calibration_File"]:
    ErrMeasFlag = True
    print("Seems like this measurement file contains a calibration measurement instead of a normal measurement. Analysis will be aborted!")


if not ErrMeasFlag:
    # Calculate the average ambient temperature as starting point
    StartTempTC = np.mean(Temp[3, 0:10])
    print("Averaged start temperature form TC-Channel 3: {Tstart:.3f}°C".format(Tstart=StartTempTC))

    CoolingStartBlock = MetaData["CoolingStartBlock"]
    SampDecade = MetaData["SamplesPerDecade"]

    # Cut Timebase and measurement to cooling section
    TimeBase_Cooling, ADC_Cooling = uTTA_data_processing.calculate_cooling_curve(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade)

    # # Calculate the average heating current, voltage and power through the diode
    PDio_Heat = uTTA_data_processing.calculate_diode_heating(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade)

    UDio_Cold_Start = np.zeros((NoOfDUTs,), numpy.float32)
    UDio_Cold_End = np.zeros((NoOfDUTs,), numpy.float32)
    T_Monitor_Heated = np.zeros((NoOfDUTs,), numpy.float32)
    TDio = np.zeros(shape=ADC_Cooling.shape)
    for Ch in range(0, NoOfDUTs):
        ch_tsp = "TSP{Ch}".format(Ch=Ch)
        if MetaData[ch_tsp]["Name"] != "OFF":
            # Calculate the average Diode voltage at the start of the measurement
            # print ("Channel {Chan}, Min ADC: {MinADC}, Max ADC: {MaxADC}".format(Chan=Ch,MinADC=ADC[Ch, :].min(), MaxADC=ADC[Ch, :].max()))
            UDio_Cold_Start[Ch] = np.mean(ADC[Ch, 0:SampDecade])
            # Calculate the average Diode voltage at the end of the measurement
            UDio_Cold_End[Ch] = np.mean(ADC[Ch, -SampDecade:-1])
            # The TSP Offset is the average diode start voltage
            MetaData[ch_tsp]["Offset"] = -UDio_Cold_Start[Ch]
            TDio[Ch, :] = (ADC_Cooling[Ch, :] + MetaData[ch_tsp]["Offset"]) / MetaData[ch_tsp]["LinGain"]

            # Calculate the start temperature of both monitoring channels to have a good starting point for Zth-Matrix
            T_Monitor_Heated[Ch] = (np.mean(ADC[Ch, ((CoolingStartBlock-2) * SampDecade):((CoolingStartBlock-1) * SampDecade) - 1])
                                    + MetaData[ch_tsp]["Offset"]) / MetaData[ch_tsp]["LinGain"]
            if Ch == 0:
                print("COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C".format(
                    DUTno=Ch,
                    Ucold=UDio_Cold_Start[Ch],
                    UColdEnd=UDio_Cold_End[Ch],
                    dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
                    dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / MetaData[ch_tsp]["LinGain"])))
            else:
                print("COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C; "
                      "Heated Temp: {T_heated: 3.4f}°C".format(DUTno=Ch,
                                                               Ucold=UDio_Cold_Start[Ch],
                                                               UColdEnd=UDio_Cold_End[Ch],
                                                               dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
                                                               dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / MetaData[ch_tsp]["LinGain"]),
                                                               T_heated=T_Monitor_Heated[Ch]))

    if ExportDiodeVoltages:
        uTTA_data_export.write_diode_voltages(TimeBase_Cooling, ADC_Cooling,  MetaData["TSP0"]["Name"], FilePath + "\\" + DataFileNoExt + '_DiodeVoltages.txt')

    # Parameters for the interpolation depth estimation
    Cth_Si = 700.0           # Thermal capacity of silicon J*(kg*K)
    rho_Si = 2330          # Density of silicon kg/m3
    kappa_SI = 148.0         # Heat transmissivity of silicon W/(m*K)

    #InterpPointsIdxStart = int((np.where(np.isclose(TimeBase_Cooling, InterpolationTStart)))[0][0])
    InterpPointsIdxStart = find_nearest(TimeBase_Cooling, InterpolationTStart)
    print(InterpPointsIdxStart)
    # InterpPointsIdxEnd = int((np.where(np.isclose(TimeBase_Cooling, InterpolationTEnd, atol=0.000001)))[0][0])
    InterpPointsIdxEnd = find_nearest(TimeBase_Cooling, InterpolationTEnd)
    print(InterpPointsIdxEnd)
    print("INTERPOLATION: Start: {IntStart: .6f}s; Index: {IdxStart:3d}; End: {IntEnd: .6f}s; Index: {IdxEnd:3d}".format(
        IntStart=InterpolationTStart,
        IntEnd=InterpolationTEnd,
        IdxStart=InterpPointsIdxStart,
        IdxEnd=InterpPointsIdxEnd))

    InterpolSqTStart = np.sqrt(InterpolationTStart)
    InterpolSqTEnd = np.sqrt(InterpolationTEnd)

    # Get the measured temperatures at the interpolation points
    InterpolYStart = np.mean(TDio[0, InterpPointsIdxStart - InterpolationAverageHW:InterpPointsIdxStart + InterpolationAverageHW])
    InterpolYEnd = np.mean(TDio[0, InterpPointsIdxEnd - InterpolationAverageHW:InterpPointsIdxEnd + InterpolationAverageHW])

    # Calculation of the interpolation parameters
    InterpolationFactorM = (InterpolYEnd - InterpolYStart) / (InterpolSqTEnd - InterpolSqTStart)
    InterpolationOffset = InterpolYStart - (InterpolationFactorM * InterpolSqTStart)
    k_therm = (2 / np.sqrt(Cth_Si * rho_Si * kappa_SI))
    EstimatedDieSize = 1000000 * (k_therm * (-PDio_Heat / InterpolationFactorM))
    TDie_Start = InterpolationOffset        # Starting temperature of the Die at the moment of switch off

    # dchip = sqrt(t_valild * 2*lambda/(cth*rho))
    DieMaxThickness = np.sqrt((InterpPointsIdxStart * 2 * kappa_SI) / (Cth_Si * rho_Si))  # Die thickness in METER
    print("Maximum Die thickness based on current interpolation: {MaxThick: .2f}mm".format(MaxThick=DieMaxThickness))

    # Interpolated curve of the temperature.
    InterpolatedStart = np.sqrt(TimeBase_Cooling[0:InterpPointsIdxStart]) * InterpolationFactorM + InterpolationOffset
    # Build the final Zth-curve with interpolated start
    TDio[3, :] = TDio[0, :]
    TDio[3, 0:InterpPointsIdxStart] = InterpolatedStart[0:InterpPointsIdxStart]
    print("INTERPOLATION: Start: {StartY: .3f}K; End: {EndY: .3f}K; Factor M: {IntFactM: .4f}; "
          "Offset: {IntOffs: .4f}; Estimated Die Size: {DieSize: .2f}mm²".format(StartY=InterpolYStart,
                                                                                 EndY=InterpolYEnd,
                                                                                 IntFactM=InterpolationFactorM,
                                                                                 IntOffs=InterpolationOffset,
                                                                                 DieSize=EstimatedDieSize))

    Zth = np.zeros(shape=ADC_Cooling.shape)
    Zth_static = np.zeros(NoOfDUTs)
    DT_Dio = np.zeros(shape=(NoOfDUTs, len(TDio[3, InterpPointsIdxStart:-1])))
    for Ch in range(0, NoOfDUTs):
        ch_tsp = "TSP{Ch}".format(Ch=Ch)
        if MetaData[ch_tsp]["Name"] != "OFF":
            if Ch == 0:
                # Do the Zth calculation for the driven channel
                Zth[0, :] = (TDio[3, :] - TDie_Start) / -PDio_Heat
                Zth_static[Ch] = np.mean(Zth[Ch, -100:-1])
                print("Static Zth for Channel{ChNo}: {ZthStat: .4f}K/W".format(ChNo=Ch, ZthStat=Zth_static[Ch]))
            else:
                # Do the Zth calculation for the Monitor channels
                T_Monitor_Heated[Ch] = InterpolationOffset - T_Monitor_Heated[Ch]
                DT_Dio[Ch, :] = TDio[Ch, InterpPointsIdxStart:-1] - TDio[0, InterpPointsIdxStart:-1] + T_Monitor_Heated[Ch]
                Zth[Ch, InterpPointsIdxStart:-1] = DT_Dio[Ch, :] / PDio_Heat
                Zth_static[Ch] = np.mean(Zth[Ch, -100:-1])
                print("Static Coupling-Zth for Channels 0-{ChNo}: {ZthStat: .4f}K/W".format(ChNo=Ch, ZthStat=Zth_static[Ch]))

    if ExportIntermediateFile:
        uTTA_data_export.export_t3i_file(TimeBase_Cooling, Zth,
                                         headername=str(MetaData["TSP0"]["Name"]) + "\t" + str(MetaData["TSP1"]["Name"]) + "\t" + str(MetaData["TSP2"]["Name"]),
                                         filename=FilePath + "\\" + DataFileNoExt + '.t3i')

    fig, axs = plt.subplots(nrows=4, ncols=2, layout="constrained")
    for Ch in range(0, NoOfDUTs):
        ch_tsp = "TSP{Ch}".format(Ch=Ch)
        if MetaData[ch_tsp]["Name"] != "OFF":
            axs[0, 0].plot(TimeBaseTotal, ADC[Ch, :], label=MetaData[ch_tsp]["Name"])  # Plot some data on the axes.

    axs[0, 0].set_title("Diode Voltages of the full measurement")
    axs[0, 0].set_ylabel('Diode Voltage / [V]')
    axs[0, 0].set_xlabel('Time / [s]')
    axs[0, 0].legend()
    axs[0, 0].grid(which='both')

    axs[0, 1].plot(TimeBaseTotal, ADC[3, :], label="Current")  # Plot some data on the axes.
    axs[0, 1].set_title("Drive current")
    axs[0, 1].set_ylabel('Current / [A]')
    axs[0, 1].set_xlabel('Time / [s]')
    axs[0, 1].legend()
    axs[0, 1].grid(which='both')

    for Ch in range(0, NoOfDUTs):
        ch_tsp = "TSP{Ch}".format(Ch=Ch)
        if MetaData[ch_tsp]["Name"] != "OFF":
            axs[1, 0].semilogx(TimeBase_Cooling, ADC_Cooling[Ch, :], label=MetaData[ch_tsp]["Name"])  # Plot some data on the axes.

    axs[1, 0].set_title("Diode Voltages of the cooling section")
    axs[1, 0].set_ylabel('Diode Voltage / [V]')
    axs[1, 0].set_xlabel('Time / [s]')
    axs[1, 0].legend()
    axs[1, 0].grid(which='both')

    axs[1, 1].semilogx(TimeBase_Cooling, ADC_Cooling[3, :], label="Current")  # Plot some data on the axes.
    axs[1, 1].set_title("Drive current in cooling section")
    axs[1, 1].set_ylabel('Current / [A]')
    axs[1, 1].set_xlabel('Time / [s]')
    axs[1, 1].legend()
    axs[1, 1].grid(which='both')

    IdxCrop = InterpPointsIdxStart
    # IdxMagnify = len(TimeBase_Cooling)
    IdxMagnify = -1
    PlotArr = TDio

    for Ch in range(1, NoOfDUTs):
        ch_tsp = "TSP{Ch}".format(Ch=Ch)
        if MetaData[ch_tsp]["Name"] != "OFF":
            axs[2, 0].semilogx(TimeBase_Cooling[IdxCrop:IdxMagnify], PlotArr[Ch, IdxCrop:IdxMagnify], label=MetaData[ch_tsp]["Name"])  # Plot some data on the axes.

    axs[2, 0].semilogx(TimeBase_Cooling[0:IdxMagnify], PlotArr[3, 0:IdxMagnify], label=MetaData["TSP0"]["Name"])  # Plot some data on the axes.
    axs[2, 0].set_title("Diode temperatures of the cooling section")
    axs[2, 0].set_ylabel('Diode Temperature / [K]')
    axs[2, 0].set_xlabel('Time / [s]')
    axs[2, 0].legend()
    axs[2, 0].grid(which='both')

    axs[2, 1].plot(Temp[0, :], label="Sensor 1")  # Plot some data on the axes.
    axs[2, 1].plot(Temp[1, :], label="Sensor 2")  # Plot some data on the axes.
    axs[2, 1].plot(Temp[2, :], label="Sensor 3")  # Plot some data on the axes.
    axs[2, 1].plot(Temp[3, :], label="Sensor 4")  # Plot some data on the axes.
    axs[2, 1].set_ylabel('Temperature / [°C]')
    axs[2, 1].set_xlabel('Sample')
    axs[2, 1].legend()
    axs[2, 1].grid(which='both')

    axs[3, 0].loglog(TimeBase_Cooling, Zth[0, :], label=MetaData["TSP0"]["Name"])  # Plot some data on the axes.
    axs[3, 0].set_title("Thermal Impedance of the driven DUT")
    axs[3, 0].set_ylabel('Thermal Impedance / [K/W]')
    axs[3, 0].set_xlabel('Time / [s]')
    axs[3, 0].legend()
    axs[3, 0].grid(which='both')

    for Ch in range(1, NoOfDUTs):
        ch_tsp = "TSP{Ch}".format(Ch=Ch)
        if MetaData[ch_tsp]["Name"] != "OFF":
            axs[3, 1].loglog(TimeBase_Cooling[InterpPointsIdxStart: -1], Zth[Ch, InterpPointsIdxStart: -1], label=MetaData[ch_tsp]["Name"])  # Plot some data on the axes.

    if MetaData["TSP1"]["Name"] != "OFF" or MetaData["TSP2"]["Name"] != "OFF":
        axs[3, 1].set_title("Thermal Impedance of the monitored DUT")
        axs[3, 1].set_ylabel('Thermal Impedance / [K/W]')
        axs[3, 1].set_xlabel('Time / [s]')
        axs[3, 1].legend()
        axs[3, 1].grid(which='both')

    end = time.time()
    print("Execution Time: {time:.3f}s".format(time=end - start))

    plt.show()
