import numpy as np                  # numpy 2.1.0
from numpy import genfromtxt        # numpy 2.1.0
import matplotlib.pyplot as plt     # matplotlib 3.9.2
import time                         # part of python 3.12.5
import os                           # part of python 3.12.5
import uTTA_data_import


FileNam = uTTA_data_import.select_file('Open a t3i-File', (('T3I Measurement Files', '*.t3i'), ('All files', '*.*')))
DataFile, DataFileNoExt, FilePath = uTTA_data_import.split_file_path(FileNam, '.t3i')

NoOfMonitors = 2
SamplesPerDecade = 10

Phi0 = 0.9
rho = 0.1

start = time.time()

Zth_Import = genfromtxt(FileNam, delimiter='\t', dtype=float, names=True)
Cols = Zth_Import.dtype.names

t = Zth_Import[Cols[0]]
Zth_Drive = Zth_Import[Cols[1]]
print("Zth end value: {ZthEnd:.3f}".format(ZthEnd=Zth_Drive[-1]))
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
a_z_pad = np.pad(a_z, (NoSamplePointsLog, ))
da_dz = (np.diff(a_z)) / LogSampPointIntervall
da_dz_pad = np.append(da_dz, 0.0)
da_dz_pad = np.pad(da_dz_pad, (NoSamplePointsLog, ))

wz = np.exp(z - np.exp(z))
wz_pad = np.pad(wz, (NoSamplePointsLog,))
wzRoll = -zStart*NoSamplePointsLog #/(zEnd-zStart)
print("Start Time {tstart:3.3f} ln(s), EndTime {tend:3.3f} ln(s) Span: {tspan:3.3f} ln(s) ".format(tstart=zStart, tend=zEnd, tspan=zEnd-zStart))
print("Rolling Array wz_pad by {roll:3.3f} elements".format(roll=wzRoll))
wz_pad = np.roll(wz_pad, int(wzRoll))


M_In_PHI = np.fft.fft(da_dz_pad)
W_PHI = np.fft.fft(wz_pad)
PHI = np.fft.fftfreq(len(M_In_PHI), d=LogSampPointIntervall/2)

F_PHI = 1 / (np.exp((np.abs(PHI)-Phi0) / rho) + 1)
MF_PHI = M_In_PHI * F_PHI
M_PHI = MF_PHI / W_PHI

r_filt_z = np.fft.ifft(MF_PHI)
r_z = np.fft.ifft(M_PHI)
print(" r(z) sum: {rzsum}, r_filz(z) sum: {rzfsum}".format(rzsum=r_z[0:NoSamplePointsLog].real.sum(), rzfsum=r_filt_z[0:NoSamplePointsLog].real.sum()))

r_z *= r_z.sum()
Zth_Drv_Filt = (np.cumsum(r_filt_z.real[len(z):2*len(z)]) * LogSampPointIntervall) + Zth_Drive[0]
Zth_Int = ((np.cumsum(r_z.real[0:len(z)])) + Zth_Drive[0])
print("Zth filtered {Zthfilt} Zth Integral: {zthint}K/W".format(Zthfilt=Zth_Drv_Filt, zthint=Zth_Int))
print("Min r(z):{RzMin:3.3f}, Max r(z):{RzMax:3.3f}".format(RzMin=np.min(r_z.real[0:NoSamplePointsLog]), RzMax=np.max(r_z.real[0:NoSamplePointsLog])))


fig, axs = plt.subplots(nrows=3, ncols=2, layout="constrained")
LineIdx = 0
axs[LineIdx, 0].plot(z_raw, Zth_Drive, label="Driver")  # Plot some data on the axes.
axs[LineIdx, 0].plot(z, Zth_Drv_Filt, label="Driver")  # Plot some data on the axes.
axs[LineIdx, 0].xaxis.set_ticks(np.arange(min(z), max(z)+1, 1.0))
axs[LineIdx, 0].set_title("Input Zth Curve")
axs[LineIdx, 0].set_ylabel('Zth / [K/W]')
axs[LineIdx, 0].set_xlabel('Time / [ln(s)]')
axs[LineIdx, 0].legend()
axs[LineIdx, 0].grid(which='both')

axs[LineIdx, 1].plot(da_dz_pad, label="Monitor1")  # Plot some data on the axes.
axs[LineIdx, 1].set_title("Interpolated and differentiated Zth Curve")
axs[LineIdx, 1].set_ylabel('Derivative of Zth / [K/W/ln(s)')
axs[LineIdx, 1].set_xlabel('Time / [ln(s)]')
axs[LineIdx, 1].legend()
axs[LineIdx, 1].grid(which='both')

LineIdx = LineIdx + 1
axs[LineIdx, 0].plot(PHI, M_In_PHI.real, label="FFT re of M*")  # Plot some data on the axes.
axs[LineIdx, 0].plot(PHI, F_PHI*100.0, label="Filter Function")  # Plot some data on the axes.
axs[LineIdx, 0].set_title("Spectral Deconvolution")
axs[LineIdx, 0].set_ylabel('Level / [a.u.]')
axs[LineIdx, 0].legend()
axs[LineIdx, 0].grid(which='both')

axs[LineIdx, 1].plot(wz_pad, label="Weighing function")  # Plot some data on the axes.
axs[LineIdx, 1].legend()
axs[LineIdx, 1].grid(which='both')
LineIdx = LineIdx + 1

axs[LineIdx, 0].plot(z, r_filt_z.real[len(z):2*len(z)], label="Filtered Output")  # Plot some data on the axes.
axs[LineIdx, 0].plot(z, r_z.real[0:len(z)]*10, label="RE Deconvolved Input")  # Plot some data on the axes.
axs[LineIdx, 0].set_title("Interpolated and differentiated Zth Curve")
axs[LineIdx, 0].set_ylabel('Diode Voltage / [V]')
axs[LineIdx, 0].set_xlabel('Time / [s]')
axs[LineIdx, 0].xaxis.set_ticks(np.arange(min(z), max(z)+1, 1.0))
axs[LineIdx, 0].legend()
axs[LineIdx, 0].grid(which='both')

# axs[LineIdx, 1].plot(z, Zth_Drv_Filt-a_z, label="RE recovered input")  # Plot some data on the axes.
# axs[LineIdx, 1].set_title("Error between filtered and raw interpolated curve")
# axs[LineIdx, 1].legend()
# axs[LineIdx, 1].grid(which='both')
# axs[LineIdx, 1].set_xlabel('Time / [ln(s)]')''

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
