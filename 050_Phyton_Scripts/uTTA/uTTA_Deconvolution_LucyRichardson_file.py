import numpy as np
# import scipy.signal
import matplotlib.pyplot as plt
import time
import scipy.signal as scip
from skimage import color, data, restoration
import os
from numpy import genfromtxt
from tkinter import filedialog as fd

StartFilePath = os.path.realpath(__file__)

def select_file():
    filetypes = (('T3I Measurement Files', '*.t3i'), ('All files', '*.*'))

    filename = fd.askopenfilename(
        title='Open a T3R-File',
        initialdir=StartFilePath,
        filetypes=filetypes
    )
    return filename


FileNam = select_file()

DataFile = os.path.basename(FileNam).split('/')[-1]
DataFileNoExt = DataFile.replace('.t3i', '')
FilePath = os.path.dirname(FileNam)

NoOfMonitors = 2
SamplesPerDecade = 100

Phi0 = 0.9
rho = 0.1

start = time.time()

Zth_Import = genfromtxt(FileNam, delimiter='\t', dtype=float, names=True)
Cols = Zth_Import.dtype.names

t = Zth_Import[Cols[0]]
Zth_Drive = Zth_Import[Cols[1]]
print("Zth end value: {ZthEnd:.3f}, Zth Curve Start Value {Rth_start}K/W".format(ZthEnd=Zth_Drive[-1], Rth_start=Zth_Drive[0]))
if Cols[1] != "Z_th_Simulated":
    Zth_Monitor = np.zeros(shape=(len(t), NoOfMonitors))
    Zth_Monitor[:, 0] = Zth_Import[Cols[2]]
    Zth_Monitor[:, 1] = Zth_Import[Cols[3]]

z_raw = np.log(t)
zStart = z_raw[0]
zEnd = z_raw[-1]

NoSamplePoints = int((zEnd-zStart)*SamplesPerDecade)
NoSamplePointsLog = int(np.power(2, np.ceil(np.log2(NoSamplePoints))))
NoSamplePointsLogPad = NoSamplePointsLog*2
LogSampPointIntervall = (zEnd-zStart)/NoSamplePointsLog
print("Number of SamplePoints: {NoSampPoints} SamplePoints power of 2: {NoSampPnts}".format(NoSampPoints=NoSamplePoints, NoSampPnts=NoSamplePointsLog))
print("SamplePoint Intervall: {SampInt}".format(SampInt=LogSampPointIntervall))
z = np.linspace(start=zStart, stop=zEnd, num=NoSamplePointsLog)

a_z = np.interp(z, z_raw, Zth_Drive)

dadz = np.diff(a_z)/np.diff(z)
sum_dadz = np.sum(dadz)
dadz = dadz/sum_dadz
w_z = np.exp(z - np.exp(z))

fig, axs = plt.subplots(nrows=3, ncols=2, layout="constrained")
LineIdx = 0
axs[0, 0].loglog(np.exp(z), a_z, label="Input Zth Curve")  # Plot some data on the axes.
# axs[LineIdx, 0].plot(z, Zth_Drv_Filt, label="Driver")  # Plot some data on the axes.

axs[0, 0].set_title("Input Zth Curve")
axs[0, 0].set_ylabel('Zth / [K/W]')
axs[0, 0].set_xlabel('Time / [ln(s)]')


axs[0, 1].plot(z[:-1], dadz, label="da/dz")  # Plot some data on the axes.
axs[0, 1].set_title("Interpolated and differentiated Zth Curve")
axs[0, 1].set_ylabel('Derivative of Zth / [K/W/ln(s)')
axs[0, 1].set_xlabel('Time / [ln(s)]')


print("z-Base Timestep: " + str(z[2]-z[1]))


Rth_Stat = np.mean(a_z[int(0.98*len(a_z)):-1])
IterationSteps = np.array([1000], dtype=int)

for Step in IterationSteps:
    deconvolved = restoration.richardson_lucy(dadz, w_z, num_iter=Step)*sum_dadz

    axs[1, 0].plot(z[:-1], deconvolved, label="Deconvolved with " + str(Step) + " Iterations")  # Plot some data on the axes.

    PeakSum = np.sum(deconvolved)*(z[2]-z[1])
    print("Total deconvolved Rth {Rth}K/W vs. Original Rth {RthOrig}K/W".format(Rth=PeakSum, RthOrig=Rth_Stat))

    dadz_conv = (np.convolve(deconvolved, w_z, "same") / np.sum(deconvolved)) * (z[2]-z[1])
    Zth_Conv = np.cumsum(dadz_conv) * Rth_Stat + a_z[0]
    StructureFunc = np.exp(np.cumsum(deconvolved) * np.diff(z))

    axs[0, 1].plot(z, dadz_conv, label="da/dz " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[1, 1].plot(z[:-1], dadz-dadz_conv[:-1], label="Delta da/dz " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[0, 0].loglog(np.exp(z), Zth_Conv, label="Reconstructed Zth " + str(Step) + " Iterations")  # Plot some data on the axes.
    axs[2, 0].semilogx(np.exp(z), Zth_Conv-a_z, label="Delta Zth " + str(Step) + " Iterations")  # Plot some data on the axes.


axs[0, 0].legend()
axs[0, 0].grid(which='both')

axs[1, 0].legend()
axs[1, 0].grid(which='both')

axs[2, 0].legend()
axs[2, 0].grid(which='both')

axs[0, 1].grid(which='both')
axs[0, 1].legend()

axs[1, 1].grid(which='both')
axs[1, 1].legend()

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()