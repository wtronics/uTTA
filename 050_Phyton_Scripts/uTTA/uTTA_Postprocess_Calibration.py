import uTTA_data_import
import numpy as np
import numpy.dtypes
import matplotlib.pyplot as plt
import time

CalFilePath = uTTA_data_import.select_file("Select the calibration file",
                                           (('uTTA Calibration Files', '*.uTTA_CAL'),
                                           ('All files', '*.*')))

PGA_Calibration, ADC_Calibration = uTTA_data_import.read_calfile(CalFilePath)

FileNam = uTTA_data_import.select_file("Select the measurement file",
                                       (('uTTA Measurement Files', '*.t3r'),
                                        ('uTTA Measurement Data', '*.umd'),
                                        ('Text-Files', '*.txt'),
                                        ('All files', '*.*')))

DataFile, DataFileNoExt, FilePath = uTTA_data_import.split_file_path(FileNam, '.t3r')

start = time.time()

TimeBaseTotal, ADC, Temp, SampDecade, CoolingStartBlock, CH_Names, DUT_TSP_Sensitivity = uTTA_data_import.read_measurement_file(FileNam,
                                                                                                                                PGA_Calibration,
                                                                                                                                ADC_Calibration,
                                                                                                                                0)

NoOfDUTs = 3
NoOfTypeK = 4

EndTime = TimeBaseTotal[-1]

TimeBase = np.arange(0.0, int(EndTime), 1)
TimeBase_TC = np.linspace(start=0.0, stop=EndTime, num=len(Temp[0]))
ADC_Voltage = np.zeros((4, int(EndTime)), numpy.float32)
Temperatures = np.zeros((4, int(EndTime)), numpy.float32)


for Idx in range(0, NoOfDUTs):
    ADC_Voltage[Idx, :] = np.interp(TimeBase, TimeBaseTotal, ADC[Idx, :])

for Idx in range(0, NoOfTypeK):
    Temperatures[Idx, :] = np.interp(TimeBase, TimeBase_TC, Temp[Idx, :])

print("Size ADC Voltages: {S_ADC}, Size Temperatures: {S_Temp}".format(S_ADC=len(ADC_Voltage), S_Temp=len(Temperatures)))
OutMaxLines = len(TimeBase)
CAL_Output = np.zeros(shape=(1 + len(ADC_Voltage) - 1 + len(Temperatures), OutMaxLines))
CAL_Output[0, ] = TimeBase[0:OutMaxLines]
CAL_Output[1:(1+NoOfDUTs), ] = ADC_Voltage[0:NoOfDUTs, ]  # omit the fourth channel as the current is not needed
CAL_Output[(1+NoOfDUTs):(1+NoOfDUTs+NoOfTypeK), ] = Temperatures
CAL_Output = np.transpose(CAL_Output)

np.savetxt(FilePath + "\\" + DataFileNoExt + '_CALVoltages.txt',CAL_Output,
           delimiter='\t',
           fmt='%1.4e',
           newline='\n',
           header="Time\t" + str(CH_Names[0])
                  + "\t" + str(CH_Names[1])
                  + "\t" + str(CH_Names[2])
                  + "\tTC0"
                  + "\tTC1"
                  + "\tTC2"
                  + "\tTC3")

fig,axs = plt.subplots(nrows=2, layout="constrained")
axs[0].plot(TimeBase, ADC_Voltage[0, :], label=CH_Names[0])  # Plot some data on the axes.
axs[0].plot(TimeBase, ADC_Voltage[1, :], label=CH_Names[1])  # Plot some data on the axes.
axs[0].plot(TimeBase, ADC_Voltage[2, :], label=CH_Names[2])  # Plot some data on the axes.
# axs[0, 0].plot(TimeBaseTotal, PGA, label="PGA")  # Plot some data on the axes.
axs[0].set_title("Diode Voltages of the full measurement")
axs[0].set_ylabel('Diode Voltage / [V]')
axs[0].set_xlabel('Time / [s]')
axs[0].legend()
axs[0].grid(which='both')


axs[1].plot(TimeBase, Temperatures[0, :], label="Sensor 1")  # Plot some data on the axes.
axs[1].plot(TimeBase, Temperatures[1, :], label="Sensor 2")  # Plot some data on the axes.
axs[1].plot(TimeBase, Temperatures[2, :], label="Sensor 3")  # Plot some data on the axes.
axs[1].plot(TimeBase, Temperatures[3, :], label="Sensor 4")  # Plot some data on the axes.
axs[1].set_ylabel('Temperature / [°C]')
axs[1].set_xlabel('Sample')
axs[1].legend()
axs[1].grid(which='both')

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
