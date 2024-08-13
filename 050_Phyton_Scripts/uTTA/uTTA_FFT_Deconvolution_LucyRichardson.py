import numpy as np
# import scipy.signal
import matplotlib.pyplot as plt
import time
import scipy.signal as scip
from skimage import color, data, restoration
import os

tStart = 1e-6
tEnd = 10e4
StepsPerDecade = 200
AddNoise = 0
# Simulated foster RC-model
Rth_Foster = np.array([0.4,     1.5,   3.5,  4.0, 5.5, 5.7], dtype=float)
Cth_Foster = np.array([0.00055, 0.006, 0.05, 0.3, 1.4, 15.0], dtype=float)


z = np.linspace(np.log(tStart), np.log(tEnd), int((np.log(tEnd)-np.log(tStart))*StepsPerDecade+1))
t = np.exp(z)
Zth = np.zeros(shape=t.shape)
taus = np.zeros(shape=Rth_Foster.shape)
# run through the RC-element array and create the RC-charging curve
for Rank in range(0, len(Cth_Foster)):
    Zth = Zth + Rth_Foster[Rank] * (1-np.exp(-t/(Rth_Foster[Rank] * Cth_Foster[Rank])))
    taus[Rank] = Rth_Foster[Rank] * Cth_Foster[Rank]
    print("Created RC-Element with R {Rth}K/W and C {Cth}Ws/K tau {Ctau} and ln_tau {lntau}".format(Rth=Rth_Foster[Rank], Cth=Cth_Foster[Rank],
                                                                                                    Ctau=Rth_Foster[Rank]*Cth_Foster[Rank],
                                                                                                    lntau=np.log(Rth_Foster[Rank]*Cth_Foster[Rank])))
start = time.time()


print("Simulated static thermal impedance {Rth}K/W. Zth Curve Start Value {Rth_start}K/W".format(Rth=Rth_Stat, Rth_start=Zth[0]))
if AddNoise == 1:
    Zth = Zth + (np.random.rand(len(Zth))*0.001)

dadz = np.diff(Zth)/np.diff(z)
sum_dadz = np.sum(dadz)
dadz = dadz/sum_dadz
w_z = np.exp(z - np.exp(z))

print("z-Base Timestep: " + str(z[2]-z[1]))

fig, axs = plt.subplots(nrows=5, layout="constrained")
axs[0].plot(z[:-1], dadz, label="da/dz")  # Plot some data on the axes.
axs[3].loglog(np.exp(z), Zth, label="Input Zth Curve")  # Plot some data on the axes.
Rth_Stat = np.mean(Zth[int(0.98*len(Zth)):-1])
IterationSteps = np.array([1000, 2500], dtype=int)

for Step in IterationSteps:
    deconvolved = restoration.richardson_lucy(dadz, w_z, num_iter=Step)*sum_dadz

    peaks, props = scip.find_peaks(deconvolved)

    taus = np.sort(taus)
    peaks = np.sort(peaks)
    delta_tau = 0
    sum_deltaTau = 0
    for Idx, fpeak in enumerate(peaks):
        delta_tau = np.log(taus[Idx])-z[int(fpeak)]
        sum_deltaTau += delta_tau
        print("Peak: " + str(z[int(fpeak)]) + " vs. Original:" + str(np.log(taus[Idx])) + " Delta: " + str(delta_tau))

    print("Average offset: " + str(sum_deltaTau/(Idx + 1)))

    axs[2].plot(z[:-1], deconvolved, label="Deconvolved with " + str(Step) + " Iterations")  # Plot some data on the axes.

    PeakSum = np.sum(deconvolved)*(z[2]-z[1])
    print("Total deconvolved Rth {Rth}K/W vs. Original Rth {RthOrig}K/W".format(Rth=PeakSum, RthOrig=Rth_Stat))

    dadz_conv = (np.convolve(deconvolved, w_z, "same") / np.sum(deconvolved)) * (z[2]-z[1])
    Zth_Conv = np.cumsum(dadz_conv) * Rth_Stat + Zth[0]
    StructureFunc = np.exp(np.cumsum(deconvolved) * np.diff(z))

    axs[0].plot(z, dadz_conv, label="da/dz " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[1].plot(z[:-1], dadz-dadz_conv[:-1], label="Delta da/dz " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[3].loglog(np.exp(z), Zth_Conv, label="Reconstructed Zth " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[4].semilogx(np.exp(z), Zth_Conv-Zth, label="Delta Zth " + str(Step) + " Iterations")  # Plot some data on the axes.


axs[0].legend()
axs[0].grid(which='both')

axs[1].legend()
axs[1].grid(which='both')

axs[2].legend()
axs[2].grid(which='both')

axs[3].grid(which='both')
axs[3].legend()

axs[4].grid(which='both')
axs[4].legend()
end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
