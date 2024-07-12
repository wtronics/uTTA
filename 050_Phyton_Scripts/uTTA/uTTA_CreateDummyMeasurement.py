import numpy as np
import matplotlib.pyplot as plt
import time
from tkinter.filedialog import askdirectory

OutputPath = '{}'.format(askdirectory(title="Select a folder for the file to be exported", mustexist=True, initialdir=r'os.path.realpath(__file__)'))
start = time.time()

# Internal constants which are normally provided by the t3r-file
MCU_Clock = 72000000
TimerPrescaler = 9
TimerClock = MCU_Clock/TimerPrescaler
TsampFast = (1000000 * 4)/TimerClock
MaxDivider = 17
SampDecade = 250

# End time of the simulated curve
SimulatedEndTime = 7200

# Simulated foster RC-model
Rth_Foster = np.array([0.4,     1.5,   3.5,  4.0, 5.5, 5.7], dtype=float)
Cth_Foster = np.array([0.00055, 0.006, 0.05, 0.3, 1.4, 15.0], dtype=float)

# Create Timebase for all measurements
BlockIdx = 0
Timebase = np.zeros(shape=(1, 1))
while True:
    TB_start = Timebase[-1]  # get the last element of the already existing timebase
    TB_Increment = TsampFast * pow(2, (min(MaxDivider, BlockIdx)))
    TB_Add = np.arange(TB_start+TB_Increment, TB_start + (TB_Increment * (SampDecade + 1)), TB_Increment)

    Timebase = np.append(Timebase, TB_Add)
    BlockIdx += 1
    if (np.max(Timebase) / 1000000) >= SimulatedEndTime:
        break

Timebase = Timebase / 1000000.0
Zth = np.zeros(shape=Timebase.shape)
# run through the RC-element array and create the RC-charging curve
for Rank in range(0, len(Cth_Foster)):
    Zth = Zth + Rth_Foster[Rank] * (1-np.exp(-Timebase/(Rth_Foster[Rank] * Cth_Foster[Rank])))
    print("Created RC-Element with R {Rth}K/W and C {Cth}Ws/K tau {Ctau} and ln_tau {lntau}".format(Rth=Rth_Foster[Rank], Cth=Cth_Foster[Rank],
                                                                                                    Ctau=Rth_Foster[Rank]*Cth_Foster[Rank],
                                                                                                    lntau=np.log(Rth_Foster[Rank]*Cth_Foster[Rank])))

# Create the output array which is one element shorter than the existing array
# because the first timebase element is 0 which is not existing in the real measurements.
Zth_output = np.zeros(shape=(2, len(Zth)-1))
Zth_output[0, :] = Timebase[1:]
Zth_output[1, :] = Zth[1:]
Zth_output = np.transpose(Zth_output)
np.savetxt(OutputPath + '\\Simulated_Measurement.t3i', Zth_output,
           delimiter='\t',
           fmt='%1.6e',
           newline='\n',
           header="Time\tZ_th_Simulated")
del Zth_output

fig, axs = plt.subplots()
axs.loglog(Timebase[1:], Zth[1:], label="Simulated")  # Plot some data on the axes.
axs.set_title("Diode Voltages of the full measurement")
axs.set_ylabel('Diode Voltage / [V]')
axs.set_xlabel('Time / [s]')
axs.legend()
axs.grid(which='both')

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
