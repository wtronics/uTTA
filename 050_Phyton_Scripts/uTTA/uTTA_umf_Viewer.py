import numpy as np                  # numpy 2.1.0
import numpy.dtypes                 # numpy 2.1.0
import matplotlib.pyplot as plt     # matplotlib 3.9.2
import time                         # part of python 3.12.5
import os                           # part of python 3.12.5
import uTTA_data_import
import uTTA_data_processing
import uTTA_data_export

CalFilePath = '.\\20240604_Calibration.uTTA_CAL'

NoOfDUTs = 3
MaxDeltaT_StartEnd = 1.0


FileNam = uTTA_data_import.select_file("Select the measurement file",
                                       (('uTTA Measurement File', '*.umf'),
                                        ('uTTA Measurement Files', '*.t3r'),
                                        ('Text-Files', '*.txt'),
                                        ('All files', '*.*')))

DataFile, DataFileNoExt, FilePath = uTTA_data_import.split_file_path(FileNam)

start = time.time()

TimeBaseTotal, ADC, Temp, SampDecade, CoolingStartBlock, CH_Names, DUT_TSP_Sensitivity = uTTA_data_import.read_measurement_file(FileNam,
                                                                                                                                CalFilePath,
                                                                                                                                0)

# Calculate the average ambient temperature as starting point
StartTempTC = np.mean(Temp[3, 0:10])
print("Averaged start temperature form TC-Channel 3: {Tstart:.3f}°C".format(Tstart=StartTempTC))

# Cut Timebase and measurement to cooling section
TimeBase_Cooling, ADC_Cooling = uTTA_data_processing.calculate_cooling_curve(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade)

# # Calculate the average heating current, voltage and power through the diode
PDio_Heat = uTTA_data_processing.calculate_diode_heating(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade)

UDio_Cold_Start = np.zeros((NoOfDUTs,), numpy.float32)
UDio_Cold_End = np.zeros((NoOfDUTs,), numpy.float32)
T_Monitor_Heated = np.zeros((NoOfDUTs,), numpy.float32)
TDio = np.zeros(shape=ADC_Cooling.shape)
for Ch in range(0, NoOfDUTs):
    if CH_Names[Ch] != "OFF":
        # Calculate the average Diode voltage at the start of the measurement
        # print ("Channel {Chan}, Min ADC: {MinADC}, Max ADC: {MaxADC}".format(Chan=Ch,MinADC=ADC[Ch, :].min(), MaxADC=ADC[Ch, :].max()))
        UDio_Cold_Start[Ch] = np.mean(ADC[Ch, 0:SampDecade])
        # Calculate the average Diode voltage at the end of the measurement
        UDio_Cold_End[Ch] = np.mean(ADC[Ch, -SampDecade:-1])
        # The TSP Offset is the average diode start voltage
        DUT_TSP_Sensitivity[Ch, 0] = -UDio_Cold_Start[Ch]
        TDio[Ch, :] = (ADC_Cooling[Ch, :] + DUT_TSP_Sensitivity[Ch, 0]) / DUT_TSP_Sensitivity[Ch, 1]

        # Calculate the start temperature of both monitoring channels to have a good starting point for Zth-Matrix
        T_Monitor_Heated[Ch] = (np.mean(ADC[Ch, ((CoolingStartBlock-2) * SampDecade):((CoolingStartBlock-1) * SampDecade) - 1])
                                + DUT_TSP_Sensitivity[Ch, 0]) / DUT_TSP_Sensitivity[Ch, 1]
        if Ch == 0:
            print("COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C".format(
                DUTno=Ch,
                Ucold=UDio_Cold_Start[Ch],
                UColdEnd=UDio_Cold_End[Ch],
                dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
                dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / DUT_TSP_Sensitivity[Ch, 0])))
        else:
            print("COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C; "
                  "Heated Temp: {T_heated: 3.4f}°C".format(DUTno=Ch,
                                                           Ucold=UDio_Cold_Start[Ch],
                                                           UColdEnd=UDio_Cold_End[Ch],
                                                           dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
                                                           dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / DUT_TSP_Sensitivity[Ch, 1]),
                                                           T_heated=T_Monitor_Heated[Ch]))


fig, axs = plt.subplots(nrows=3, ncols=2, layout="constrained")
for Ch in range(0, NoOfDUTs):
    if CH_Names[Ch] != "OFF":
        axs[0, 0].plot(TimeBaseTotal, ADC[Ch, :], label=CH_Names[Ch])  # Plot some data on the axes.

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
    if CH_Names[Ch] != "OFF":
        axs[1, 0].semilogx(TimeBase_Cooling, ADC_Cooling[Ch, :], label=CH_Names[Ch])  # Plot some data on the axes.

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

axs[2, 0].plot(Temp[0, :], label="Sensor 1")  # Plot some data on the axes.
axs[2, 0].plot(Temp[1, :], label="Sensor 2")  # Plot some data on the axes.
axs[2, 0].plot(Temp[2, :], label="Sensor 3")  # Plot some data on the axes.
axs[2, 0].plot(Temp[3, :], label="Sensor 4")  # Plot some data on the axes.
axs[2, 0].set_ylabel('Temperature / [°C]')
axs[2, 0].set_xlabel('Sample')
axs[2, 0].legend()
axs[2, 0].grid(which='both')

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
