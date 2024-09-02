import numpy as np                              # numpy 2.1.0
import matplotlib.pyplot as plt                 # matplotlib 3.9.2
import scipy.signal as scip                     # scipy 1.14.1
from skimage import restoration                 # scikit-image 0.24.0
import time                                     # part of python 3.12.5

tStart = 1e-6
tEnd = 10e4
StepsPerDecade = 100

NoRC_Pairs = 90

AddNoise = 0

# deconv_zShift = 1.144472988
deconv_zShift = 1.138+0.017091077755321222
IterationSteps = np.array([1000, 2500], dtype=int)
# Simulated foster RC-model
Rth_Foster = np.array([0.1,      0.5,      0.1,      0.3,   1.2,   0.4,  3.7, 4.0, 5.5, 5.7,  2.0, 2.0], dtype=float)
Cth_Foster = np.array([0.0002, 0.000055, 0.00025,  0.006, 0.001, 0.002, 0.01, 0.3, 4.4, 45.0, 90,  200], dtype=float)

# Rth_Foster = np.array([4.0], dtype=float)
# Cth_Foster = np.array([0.3], dtype=float)
# Rth_Foster = np.array([0.4, 5.7], dtype=float)
# Cth_Foster = np.array([0.000055, 45.0], dtype=float)

z = np.linspace(np.log(tStart), np.log(tEnd), int((np.log(tEnd)-np.log(tStart))*StepsPerDecade+1))
SampPerPair = np.floor(len(z)/NoRC_Pairs)
print("Total samples for this experiment {NSamp}, with a z-Base timestep of {Tstep}, Samples per RC-Pair {SampRC}".format(
    NSamp=len(z),
    Tstep=z[2]-z[1],
    SampRC=SampPerPair))

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

Rth_Stat = sum(Rth_Foster)
print("Simulated static thermal impedance {Rth}K/W. Zth Curve Start Value {Rth_start}K/W".format(Rth=Rth_Stat, Rth_start=Zth[0]))
if AddNoise == 1:
    Zth = Zth + (np.random.rand(len(Zth))*0.001)

dadz = np.diff(Zth)/np.diff(z)
sum_dadz = np.sum(dadz)
dadz = dadz/sum_dadz
w_z = np.exp(z - np.exp(z))

fig, axs = plt.subplots(nrows=5, layout="constrained")
axs[1].plot(z[:-1], dadz, label="da/dz")  # Plot some data on the axes.
axs[3].stem(np.log(taus), Rth_Foster, label="Input")
axs[0].loglog(np.exp(z), Zth, label="Input Zth Curve")  # Plot some data on the axes.
Rth_Stat = np.mean(Zth[int(0.98*len(Zth)):-1])


for Step in IterationSteps:
    deconvolved = restoration.richardson_lucy(dadz, w_z, num_iter=Step)*sum_dadz

    peaks, props = scip.find_peaks(deconvolved)

    taus = np.sort(taus)
    peaks = np.sort(peaks)
    delta_tau = 0
    sum_deltaTau = 0
    Idx = 0
    for Idx, fpeak in enumerate(peaks):
        delta_tau = np.log(taus[Idx])-z[int(fpeak)]-deconv_zShift
        sum_deltaTau += delta_tau
        print("Peak: " + str(z[int(fpeak)]+deconv_zShift) + " vs. Original:" + str(np.log(taus[Idx])) + " Delta: " + str(delta_tau))

    print("Average offset: " + str(sum_deltaTau/(Idx + 1)))

    axs[3].plot(z[:-1]+deconv_zShift, deconvolved, label="Deconvolved with " + str(Step) + " Iterations")  # Plot some data on the axes.

    PeakSum = np.sum(deconvolved)*(z[2]-z[1])
    print("Total deconvolved Rth {Rth}K/W vs. Original Rth {RthOrig}K/W".format(Rth=PeakSum, RthOrig=Rth_Stat))

    dadz_conv = (np.convolve(deconvolved, w_z, "same") / np.sum(deconvolved)) * (z[2]-z[1])
    Zth_Conv = np.cumsum(dadz_conv) * Rth_Stat + Zth[0]

    axs[1].plot(z, dadz_conv, label="da/dz " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[2].plot(z[:-1], dadz-dadz_conv[:-1], label="Delta " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[0].loglog(np.exp(z), Zth_Conv, label="Reconstructed " + str(Step) + " Iterations", linestyle='dashed')  # Plot some data on the axes.

    Rth_FostRecovered = np.zeros(shape=int(len(z)/SampPerPair))
    Cth_FostRecovered = np.zeros(shape=int(len(z)/SampPerPair))
    for SampIdx, Rth in enumerate(Rth_FostRecovered):

        Rth_FostRecovered[SampIdx] = np.sum(deconvolved[int(SampIdx*SampPerPair):int((SampIdx*SampPerPair)+SampPerPair)])*(z[2]-z[1])*SampPerPair
        if Rth_FostRecovered[SampIdx] < 1e-9:
            Cth_FostRecovered[SampIdx] = 0
        else:
            Cth_FostRecovered[SampIdx] = np.exp((np.sum(z[int(SampIdx*SampPerPair):
                                                          int((SampIdx*SampPerPair)+SampPerPair)])/SampPerPair)/Rth_FostRecovered[SampIdx]
                                                )
        print("Index {Idx}: Rth:{Rth}K/W Cth {Cth}Ws/K".format(Idx=SampIdx, Rth=Rth_FostRecovered[SampIdx], Cth=Cth_FostRecovered[SampIdx]))

    CSF_Rth = np.cumsum(Rth_FostRecovered)
    CSF_Cth = np.cumsum(Cth_FostRecovered)

    axs[4].loglog(CSF_Rth, CSF_Cth, label="Delta " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[4].set_xlim([1e-6, np.max(CSF_Rth)+1])
    # axs[4].semilogx(np.exp(z), Zth_Conv-Zth, label="Delta " + str(Step) + " Iterations")  # Plot some data on the axes.

axs[0].set_title("Zth Curves a(t)")
axs[0].legend()
axs[0].grid(which='both')

axs[1].set_title("Differentiated Zth Curves da/dz")
axs[1].legend()
axs[1].grid(which='both')

axs[2].set_title("Difference between input da/dz and output da/dz")
axs[2].legend()
axs[2].grid(which='both')

axs[3].set_title("Time constant spectrum observed by Lucy-Richardson deconvolution")
axs[3].grid(which='both')
axs[3].legend()

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
