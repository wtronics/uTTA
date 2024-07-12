import numpy as np
import numpy.dtypes
import matplotlib.pyplot as plt
import time
from tkinter import filedialog as fd
import configparser
import os

# CalFilePath = '.\\TEST.uTTA_CAL'
CalFilePath = '.\\20240604_Calibration.uTTA_CAL'
StartFilePath = os.path.realpath(__file__)

PGA_Calibration_Gain = np.array([0.000405, 0.000275, 0.000210, 0.000168], dtype=float)
PGA_Calibration_Offset = np.array([-0.052951, -0.052294, -0.052003, -0.051640], dtype=float)
ADC_Calibration_Gain = np.array([1.0, 0.000327, 0.000326, 0.00789], dtype=float)
ADC_Calibration_Offset = np.array([0.0, -0.051671, -0.049331, -0.07651], dtype=float)

NoOfDUTs = 3
CH_Names = ["DUT", "Monitor1", "Monitor2"]
DUT_TSP_Sensitivity_offset = np.array([0.0, 0.0, 0.0], dtype=float)
DUT_TSP_Sensitivity_linear = np.array([-0.0026, -0.0026, -0.0026], dtype=float)
DUT_TSP_Sensitivity_square = np.array([0.0, 0.0, 0.0], dtype=float)


def select_file():
    filetypes = (('T3R Measurement Files', '*.t3r'), ('All files', '*.*'))

    filename = fd.askopenfilename(
        title='Open a T3R-File',
        initialdir=StartFilePath,
        filetypes=filetypes
    )
    return filename


def read_cal_file():
    print("Reading calibration values from file: " + CalFilePath)
    config = configparser.ConfigParser()
    config.read_file(open(CalFilePath))
#    confSect = config.sections()

    for ChIdx in range(0, 4):
        if ChIdx == 0:
            for PGA_Idx in range(0, 4):
                PGA_Calibration_Gain[PGA_Idx] = float(config["ADC0_CAL_PGA_"+str(PGA_Idx)]["Gain"].replace(",", "."))
                PGA_Calibration_Offset[PGA_Idx] = float(config["ADC0_CAL_PGA_"+str(PGA_Idx)]["Offset"].replace(",", "."))
                print("Calibration Values for Ch{ChNo}.PGA{PGANo}: Gain: {Slope:.6f} V/Digit, Offset: {Offs:.6f} V".format(
                    ChNo=ChIdx,
                    PGANo=PGA_Idx,
                    Slope=PGA_Calibration_Gain[PGA_Idx],
                    Offs=PGA_Calibration_Offset[PGA_Idx]))
        else:
            ADC_Calibration_Gain[ChIdx] = float(config["ADC"+str(ChIdx) + "_CAL"]["Gain"].replace(",", "."))
            ADC_Calibration_Offset[ChIdx] = float(config["ADC"+str(ChIdx) + "_CAL"]["Offset"].replace(",", "."))
            print("Calibration Values for Ch{ChNo}:      Gain: {Slope:.6f} V/Digit, Offset: {Offs:.6f} V".format(ChNo=ChIdx,
                                                                                                                 Slope=ADC_Calibration_Gain[ChIdx],
                                                                                                                 Offs=ADC_Calibration_Offset[ChIdx]))
    return


read_cal_file()
FileNam = select_file()

DataFile = os.path.basename(FileNam).split('/')[-1]
DataFileNoExt = DataFile.replace('.t3r', '')
FilePath = os.path.dirname(FileNam)

start = time.time()

MaxDeltaT_StartEnd = 1.0

MCU_Clock = 72000000
TimerPrescaler = 9
TimerClock = MCU_Clock/TimerPrescaler
FlagRawValueMode = 0

# print(FileNam)
with open(FileNam, 'r') as fil:
    Lines = fil.readlines()
    fil.close()
    NumLines = len(Lines)
    # print("Number of Lines: " + str(NumLines))
    ADC = np.zeros((4, NumLines), numpy.float32)
    ADC_Idx = 0
    Temp_Idx = 0

    for Line in Lines:
        Line = Line.replace("\r", "").replace("\n", "")
        Cells = Line.split(";")
        # print(type(Cells))
        if isinstance(Cells, list):
            if not Cells[0].isnumeric():
                match Cells[0]:
                    case 'FileVersion':
                        T3R_FileVersion = str(Cells[1])
                        T3R_FileVers = float(T3R_FileVersion)
                        print("File Version: {FileVers:.1f}".format(FileVers=T3R_FileVers))
                    case 'StartTime':
                        StartTime = str(Cells[1])
                    case 'StartDate':
                        StartDate = str(Cells[1])
                        print("Measurement Started " + StartDate + " " + StartTime)
                    case 'CH1 Name':
                        CH_Names[0] = str(Cells[1])
                        if T3R_FileVers > 2.1:
                            DUT_TSP_Sensitivity_offset[0] = float(Cells[2])/1000000
                            DUT_TSP_Sensitivity_linear[0] = float(Cells[3])/1000000
                            DUT_TSP_Sensitivity_square[0] = float(Cells[4])/1000000
                    case 'CH2 Name':
                        CH_Names[1] = str(Cells[1])
                        if T3R_FileVers > 2.1:
                            DUT_TSP_Sensitivity_offset[1] = float(Cells[2])/1000000
                            DUT_TSP_Sensitivity_linear[1] = float(Cells[3])/1000000
                            DUT_TSP_Sensitivity_square[1] = float(Cells[4])/1000000
                    case 'CH3 Name':
                        CH_Names[2] = str(Cells[1])
                        if T3R_FileVers > 2.1:
                            DUT_TSP_Sensitivity_offset[2] = float(Cells[2])/1000000
                            DUT_TSP_Sensitivity_linear[2] = float(Cells[3])/1000000
                            DUT_TSP_Sensitivity_square[2] = float(Cells[4])/1000000
                    case 'Tsamp,fast':
                        TsampFast = (1000000 * float(Cells[1]))/TimerClock
                    case 'Tsamp,low':
                        TsampSlow = (1000000 * float(Cells[1]))/TimerClock
                    case 'Samples/Decade':
                        SampDecade = int(Cells[1])
                        print(
                            "SAMPLING: Ts_fast:    {sampf:>7.2f}Hz  ; Ts_low:   {sampl:>7.2f}Hz  ; Samples/Decade: {SampDec:>7.2f}".format(
                                sampf=1000000 / TsampFast, sampl=1000000 / TsampSlow, SampDec=SampDecade))

                    case 'Max. Divider':
                        MaxDivider = int(Cells[1])
                    case 'T_Preheat':
                        TPreheat = int(Cells[1])
                    case 'T_Heat':
                        THeat = int(Cells[1])
                    case 'T_Cool':
                        TCool = int(Cells[1])
                        print("TIMING:   Preheating:    {tPreh:>7.2f}Min ; Heating:  {tHeat:>7.2f}Min ; Cooling:        {tCool:>7.2f}Min".format(
                            tPreh=TPreheat / 60, tHeat=THeat / 60, tCool=TCool / 60))
                        PGA = np.zeros((NumLines, ), numpy.int16)
                        Temp = np.zeros((4, int(NumLines)), numpy.float32)
                        BlockNo = np.zeros((NumLines, ), numpy.int16)
                    case '#B':
                        LastBlockNo = int(Cells[1])
                    case '#BlockNo':
                        LastBlockNo = int(Cells[1])
                    case '#P':
                        PGA_now = int(Cells[1])
                    case '#PGA':
                        PGA_now = int(Cells[1])
                    case '#T':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            Temp[CellIdx-1, Temp_Idx] = float(Cells[CellIdx])/10.0
                        Temp_Idx += 1
                    case '#TEMP':
                        for CellIdx in range(1, 5):  # copy the cells to the new array
                            Temp[CellIdx-1, Temp_Idx] = float(Cells[CellIdx])/10.0
                        Temp_Idx += 1
                    case 'Cooling Start Block':
                        CoolingStartBlock = int(Cells[1])+1

                    case 'Total Blocks':
                        TotalBlocks = int(Cells[1])
                        print("BLOCKS:   Cool start block:  {CSB}    ; Total:        {TotBlocks}".format(CSB=CoolingStartBlock, TotBlocks=TotalBlocks))
                    case 'Finished':
                        FinishingTime = str(Cells[1])
                        # print("Finishing time: " + FinishingTime)
                    case 'ADC1':
                        Cells[0] = ""
                    # dummy case to remove skipped line statement
                    case _:
                        print("Skipped Line: " + Line)
            else:
                if Cells[0].isnumeric():
                    PGA[ADC_Idx] = PGA_now
                    BlockNo[ADC_Idx] = LastBlockNo
                    if FlagRawValueMode == 0:
                        ADC[0, ADC_Idx] = (float(Cells[0]) * PGA_Calibration_Gain[PGA_now]) + PGA_Calibration_Offset[PGA_now]
                        for CellIdx in range(1, 4):         # copy the cells to the new array
                            ADC[CellIdx, ADC_Idx] = (float(Cells[CellIdx]) * ADC_Calibration_Gain[CellIdx]) + ADC_Calibration_Offset[CellIdx]
                    else:
                        ADC[0, ADC_Idx] = float(Cells[0])
                        for CellIdx in range(1, 4):         # copy the cells to the new array
                            ADC[CellIdx, ADC_Idx] = float(Cells[CellIdx])
                    ADC_Idx += 1


del Lines
del Line
del Cells
del CellIdx
del PGA
del BlockNo

print("Channel Names: " + str(CH_Names))
# print("ADC Array original: " + str(ADC.shape))
# print("PGA Array original: " + str(PGA.shape))
# print("Block Array original: " + str(BlockNo.shape))
# PGA = np.resize(PGA,(ADC_Idx, ))
# BlockNo = np.resize(BlockNo,(ADC_Idx, ))
Temp = Temp[:, 0:Temp_Idx+1]
ADC = ADC[:, 0:ADC_Idx]
del ADC_Idx

# print("\nADC Array resized: " + str(ADC.shape))
# print("PGA Array resized: " + str(PGA.shape))
# print("Block Array resized: " + str(BlockNo.shape))
print("")
TimeBaseHeating = np.arange(0.0, (CoolingStartBlock * SampDecade) * TsampSlow, TsampSlow, dtype=numpy.float64)
TimeBaseTotal = np.copy(TimeBaseHeating)
# print("Heating Timebase size: " + str(TimeBaseHeating.shape))

# Create Timebase for all measurements
for BlockIdx in range(CoolingStartBlock, TotalBlocks+1):
    TB_start = TimeBaseTotal[-1]        # get the last element of the already existing timebase
    TB_Increment = TsampFast * pow(2, (min(MaxDivider, BlockIdx - CoolingStartBlock)))
    # print("Building Timebase, Start Time: " + str(TB_start) + " Timebase increment: " + str(TB_Increment) + "s")
    TB_Add = np.arange(TB_start+TB_Increment, TB_start + (TB_Increment * (SampDecade + 1)), TB_Increment)

    TimeBaseTotal = np.append(TimeBaseTotal, TB_Add)
    # print("Adding to Timebase size: " + str(TimeBaseTotal.shape) + " " + str(TB_Add.shape))

TimeBaseTotal = TimeBaseTotal / 1000000.0

# Cut Timebase and measurement to cooling section
TimeBase_Cooling = (TimeBaseTotal[(CoolingStartBlock * SampDecade):-1] - TimeBaseTotal[(CoolingStartBlock * SampDecade) - 1])
ADC_Cooling = ADC[:, (CoolingStartBlock * SampDecade):-1]

# Get Min and Max Values of the Full Cooling Curve
DUT_Imin = min(ADC_Cooling[3, :])
DUT_Imax = max(ADC_Cooling[3, :])
print("Min Diode Current:  {min:.2f}A; Max Diode current: {max:.2f}A".format(min=DUT_Imin, max=DUT_Imax))
CoolingStartIndex = (np.where(np.isclose(ADC_Cooling[3, :], DUT_Imin)))[0][0]
print("Index of closest value: " + str(CoolingStartIndex))

# Cut the measurement data down to the starting point of the cooling phase
ADC_Cooling = ADC_Cooling[:, CoolingStartIndex:-1]
TimeBase_Cooling = TimeBase_Cooling[CoolingStartIndex:-1] - TimeBase_Cooling[CoolingStartIndex-1]
# print("ADC Cooling: " + str(ADC_Cooling.shape))
# print("Timebase Cooling: " + str(TimeBase_Cooling.shape))

# Calculate the average ambient temperature as starting point
StartTempTC = np.mean(Temp[3, 0:10])
print("Averaged start temperature form TC-Channel 3: {Tstart:.3f}°C".format(Tstart=StartTempTC))

# Calculate the average heating current, voltage and power through the diode
I_Heat = np.mean(ADC[3, ((CoolingStartBlock-2) * SampDecade):((CoolingStartBlock-1) * SampDecade) - 1])
UDio_Heated = np.mean(ADC[0, ((CoolingStartBlock - 2) * SampDecade):((CoolingStartBlock - 1) * SampDecade) - 1])
PDio_Heat = I_Heat * UDio_Heated
print("HEATING VALUES: Range: {tstart:.2f}s to {tend:.2f}s, Current: {curr:.2f}A, Voltage: {volts:.2f}V, Power: {pow:.2f}W".format(
    tstart=TimeBaseTotal[(CoolingStartBlock-2) * SampDecade],
    tend=TimeBaseTotal[((CoolingStartBlock-1) * SampDecade) - 1],
    curr=I_Heat,
    volts=UDio_Heated,
    pow=PDio_Heat))

UDio_Cold_Start = np.zeros((NoOfDUTs,), numpy.float32)
UDio_Cold_End = np.zeros((NoOfDUTs,), numpy.float32)
T_Monitor_Heated = np.zeros((NoOfDUTs,), numpy.float32)
TDio = np.zeros(shape=ADC_Cooling.shape)
for Ch in range(0, NoOfDUTs):
    # Calculate the average Diode voltage at the start of the measurement
    # print ("Channel {Chan}, Min ADC: {MinADC}, Max ADC: {MaxADC}".format(Chan=Ch,MinADC=ADC[Ch, :].min(), MaxADC=ADC[Ch, :].max()))
    UDio_Cold_Start[Ch] = np.mean(ADC[Ch, 0:SampDecade])
    # Calculate the average Diode voltage at the end of the measurement
    UDio_Cold_End[Ch] = np.mean(ADC[Ch, -SampDecade:-1])
    # The TSP Offset is the average diode start voltage
    DUT_TSP_Sensitivity_offset[Ch] = -UDio_Cold_Start[Ch]
    TDio[Ch, :] = (ADC_Cooling[Ch, :] + DUT_TSP_Sensitivity_offset[Ch]) / DUT_TSP_Sensitivity_linear[Ch]

    # Calculate the start temperature of both monitoring channels to have a good starting point for Zth-Matrix
    T_Monitor_Heated[Ch] = (np.mean(ADC[Ch, ((CoolingStartBlock-2) * SampDecade):((CoolingStartBlock-1) * SampDecade) - 1])
                            + DUT_TSP_Sensitivity_offset[Ch]) / DUT_TSP_Sensitivity_linear[Ch]
    if Ch == 0:
        print("COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C".format(
            DUTno=Ch,
            Ucold=UDio_Cold_Start[Ch],
            UColdEnd=UDio_Cold_End[Ch],
            dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
            dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / DUT_TSP_Sensitivity_linear[Ch])))
    else:
        print("COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C; "
              "Heated Temp: {T_heated: 3.4f}°C".format(DUTno=Ch,
                                                       Ucold=UDio_Cold_Start[Ch],
                                                       UColdEnd=UDio_Cold_End[Ch],
                                                       dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
                                                       dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / DUT_TSP_Sensitivity_linear[Ch]),
                                                       T_heated=T_Monitor_Heated[Ch]))

DioVoltageMaxLines = len(TimeBase_Cooling)
Diode_Output = np.zeros(shape=(2, DioVoltageMaxLines))
Diode_Output[0, ] = TimeBase_Cooling[0:DioVoltageMaxLines]
Diode_Output[1, ] = ADC_Cooling[0, 0:DioVoltageMaxLines]
Diode_Output = np.transpose(Diode_Output)

np.savetxt(FilePath + "\\" + DataFileNoExt + '_DiodeVoltages.txt', Diode_Output,
           delimiter='\t',
           fmt='%1.4e',
           newline='\n',
           header="Time\t" + str(CH_Names[0]))

# Parameters for Interpolation
InterpolationTStart = 0.000020
InterpolationTEnd = 0.00025
InterpolationAverageHW = 1   # Should be the half width of the averaged area

Cth_Si = 700.0           # Thermal capacity of silicon J*(kg*K)
rho_Si = 2330          # Density of silicon kg/m3
kappa_SI = 148.0         # Heat transmissivity of silicon W/(m*K)


InterpPointsIdxStart = int((np.where(np.isclose(TimeBase_Cooling, InterpolationTStart)))[0][0])
InterpPointsIdxEnd = int((np.where(np.isclose(TimeBase_Cooling, InterpolationTEnd, atol=0.000001)))[0][0])
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

Zth_output = np.zeros(shape=(NoOfDUTs+1, len(TDio[3, :])))
Zth_output[0, :] = TimeBase_Cooling
Zth_output[1, :] = Zth[0, :]
Zth_output[2, :] = Zth[1, :]
Zth_output[3, :] = Zth[2, :]
Zth_output = np.transpose(Zth_output)
np.savetxt(FilePath + "\\" + DataFileNoExt + '.t3i', Zth_output,
           delimiter='\t',
           fmt='%1.6e',
           newline='\n',
           header="Time\t" + str(CH_Names[0]) + "\t" + str(CH_Names[1]) + "\t" + str(CH_Names[2]))
del Zth_output

fig, axs = plt.subplots(nrows=4, ncols=2, layout="constrained")
axs[0, 0].plot(TimeBaseTotal, ADC[0, :], label=CH_Names[0])  # Plot some data on the axes.
axs[0, 0].plot(TimeBaseTotal, ADC[1, :], label=CH_Names[1])  # Plot some data on the axes.
axs[0, 0].plot(TimeBaseTotal, ADC[2, :], label=CH_Names[2])  # Plot some data on the axes.
# axs[0, 0].plot(TimeBaseTotal, PGA, label="PGA")  # Plot some data on the axes.
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

axs[1, 0].semilogx(TimeBase_Cooling, ADC_Cooling[0, :], label=CH_Names[0])  # Plot some data on the axes.
axs[1, 0].semilogx(TimeBase_Cooling, ADC_Cooling[1, :], label=CH_Names[1])  # Plot some data on the axes.
axs[1, 0].semilogx(TimeBase_Cooling, ADC_Cooling[2, :], label=CH_Names[2])  # Plot some data on the axes.
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
IdxMagnify = len(TimeBase_Cooling)
PlotArr = TDio


axs[2, 0].semilogx(TimeBase_Cooling[IdxCrop:IdxMagnify], PlotArr[1, IdxCrop:IdxMagnify], label=CH_Names[1])  # Plot some data on the axes.
axs[2, 0].semilogx(TimeBase_Cooling[IdxCrop:IdxMagnify], PlotArr[2, IdxCrop:IdxMagnify], label=CH_Names[2])  # Plot some data on the axes.
axs[2, 0].semilogx(TimeBase_Cooling[0:IdxMagnify], PlotArr[3, 0:IdxMagnify], label=CH_Names[0])  # Plot some data on the axes.
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

axs[3, 0].loglog(TimeBase_Cooling, Zth[0, :], label=CH_Names[0])  # Plot some data on the axes.
axs[3, 0].set_title("Thermal Impedance of the driven DUT")
axs[3, 0].set_ylabel('Thermal Impedance / [K/W]')
axs[3, 0].set_xlabel('Time / [s]')
axs[3, 0].legend()
axs[3, 0].grid(which='both')

axs[3, 1].loglog(TimeBase_Cooling[InterpPointsIdxStart: -1], Zth[1, InterpPointsIdxStart: -1], label=CH_Names[1])  # Plot some data on the axes.
axs[3, 1].loglog(TimeBase_Cooling[InterpPointsIdxStart: -1], Zth[2, InterpPointsIdxStart: -1], label=CH_Names[2])  # Plot some data on the axes.
axs[3, 1].set_title("Thermal Impedance of the monitored DUT")
axs[3, 1].set_ylabel('Thermal Impedance / [K/W]')
axs[3, 1].set_xlabel('Time / [s]')
axs[3, 1].legend()
axs[3, 1].grid(which='both')

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
