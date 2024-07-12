import numpy as np
# import scipy.signal
import matplotlib.pyplot as plt
import time
from numpy import genfromtxt
from tkinter import filedialog as fd
import os

StartFilePath = os.path.realpath(__file__)


def select_file():
    filetypes = (('T3I Measurement Files', '*.t3i'),('All files', '*.*'))

    filename = fd.askopenfilename(
        title='Open a T3R-File',
        initialdir=StartFilePath,
        filetypes=filetypes
    )
    return filename


FileNam = select_file()

DataFile = os.path.basename(FileNam).split('/')[-1]
DataFileNoExt = DataFile.replace('.t3i','')
FilePath = os.path.dirname(FileNam)

NoOfMonitors = 2
SamplesPerDecade = 50

Phi0 = 0.45
rho = 0.05


start = time.time()

Zth_Import = genfromtxt(FileNam, delimiter='\t', dtype=float, names=True)
Cols = Zth_Import.dtype.names

t = Zth_Import[Cols[0]]
Zth_Drive = Zth_Import[Cols[1]]
print("Zth end value: {ZthEnd:.3f}".format(ZthEnd=Zth_Drive[-1]))
# Zth_Monitor = np.zeros(shape=(len(t), NoOfMonitors))
# Zth_Monitor[:, 0] = Zth_Import[Cols[2]]
# Zth_Monitor[:, 1] = Zth_Import[Cols[3]]

z_raw = np.log(t)
zStart = z_raw[0]
zEnd = z_raw[-1]

NoSamplePoints = int((zEnd-zStart)*SamplesPerDecade)
z = np.linspace(start=zStart, stop=zEnd, num=NoSamplePoints)

z_pad = np.linspace(start=zStart, stop=zEnd+(zEnd-zStart), num=NoSamplePoints*2-1)

a_z = np.interp(z, z_raw, Zth_Drive)
dz = np.diff(z)
da_dz = (np.diff(a_z)) / dz

da_dz_pad = np.zeros(shape=NoSamplePoints*2-1)
da_dz_pad[0:len(da_dz)] = da_dz
# da_dz_pad[0:len(da_dz)] = da_dz

wz = np.exp(z - np.exp(z))
wz_pad = np.zeros(shape=NoSamplePoints*2-1)
wz_pad[0:len(wz)] = wz

wz_pad = (np.roll(wz_pad, int(zStart*SamplesPerDecade)))

M_In_PHI = np.fft.fft(da_dz_pad)
W_PHI = np.fft.fft(wz_pad)
Timestep = z_pad[1]-z_pad[0]
PHI = np.fft.fftfreq(z_pad.shape[-1], d=Timestep)

F_PHI = 1 / (np.exp((np.abs(PHI)-Phi0) / rho) + 1)
MF_PHI = M_In_PHI * F_PHI
M_PHI = MF_PHI / W_PHI

m_filt = np.fft.ifft(MF_PHI)
m_rec = np.fft.ifft(M_PHI)

Zth_Drv_Filt = (np.cumsum(m_filt.real[0:len(z)]) * np.diff(z_pad[0:len(z)+1])) + Zth_Drive[0]
Zth_Int = ((np.cumsum(m_filt.real[0:-1]) * np.diff(z_pad)) + Zth_Drive[0])
print("Total Zth: {Zth_Total:3.3f}K/W compared to total integral {Zth:.3f}K/W".format(Zth_Total=np.sum(m_rec.real), Zth=Zth_Int[-1]))

mrec_pos = np.copy(m_rec)
mrec_neg = np.copy(m_rec)
mrec_pos[mrec_pos < 0] = 0
mrec_neg[mrec_neg > 0] = 0

Zth_pos = np.sum(mrec_pos.real[0:len(z)])
Zth_neg = np.sum(mrec_neg.real[0:len(z)])
print("Positive Zth: {ZthPos:.3f}K/W negative Zth: {ZthNeg:.3f}K/W".format(ZthPos=Zth_pos, ZthNeg=Zth_neg))

Zth_output = np.zeros(shape=(2, len(z)))
Zth_output[0, :] = np.exp(z_pad[0:len(z)])
Zth_output[1, :] = Zth_Int[0:len(z)]
Zth_output = np.transpose(Zth_output)
np.savetxt(FilePath + "\\" + DataFileNoExt + '_Output.tsv',
           Zth_output,
           delimiter='\t',
           fmt='%1.6e',
           newline='\n',
           header="Time\t"+ str(Cols[1]))

fig, axs = plt.subplots(nrows=3, ncols=2, layout="constrained")
LineIdx = 0
axs[LineIdx, 0].plot(z_raw, Zth_Drive, label="Driver")  # Plot some data on the axes.
axs[LineIdx, 0].plot(z, Zth_Drv_Filt, label="Filtered")  # Plot some data on the axes.
axs[LineIdx, 0].xaxis.set_ticks(np.arange(min(z), max(z)+1, 1.0))
axs[LineIdx, 0].set_title("Input Zth Curve")
axs[LineIdx, 0].set_ylabel('Zth / [K/W]')
axs[LineIdx, 0].set_xlabel('Time / [ln(s)]')
axs[LineIdx, 0].legend()
axs[LineIdx, 0].grid(which='both')

axs[LineIdx, 1].plot(z[0:-1], da_dz, label="Monitor1")  # Plot some data on the axes.
axs[LineIdx, 1].plot(z_pad[0:len(z)], m_filt.real[0:len(z)], label="Filtered input signal")  # Plot some data on the axes.
axs[LineIdx, 1].set_title("Interpolated and differentiated Zth Curve")
axs[LineIdx, 1].set_ylabel('Derivative of Zth / [K/W/ln(s)')
axs[LineIdx, 1].set_xlabel('Time / [ln(s)]')
axs[LineIdx, 1].legend()
axs[LineIdx, 1].grid(which='both')
LineIdx = LineIdx + 1
axs[LineIdx, 0].plot(PHI, M_In_PHI.real, label="FFT re of M*")  # Plot some data on the axes.
axs[LineIdx, 0].plot(PHI, F_PHI*100.0, label="Filter Function")  # Plot some data on the axes.
axs[LineIdx, 0].set_title("Interpolated and differentiated Zth Curve")
axs[LineIdx, 0].set_ylabel('Diode Voltage / [V]')
axs[LineIdx, 0].set_xlabel('Time / [s]')
axs[LineIdx, 0].legend()
axs[LineIdx, 0].grid(which='both')

axs[LineIdx, 1].plot(z_pad, wz_pad, label="Weighing function")  # Plot some data on the axes.
axs[LineIdx, 1].plot(z, wz, label="Orig, Weighing function")  # Plot some data on the axes.
axs[LineIdx, 1].legend()
axs[LineIdx, 1].grid(which='both')
LineIdx = LineIdx + 1
axs[LineIdx, 0].plot(z_pad[0:len(z)], m_rec.real[0:len(z)], label="RE recovered input")  # Plot some data on the axes.
axs[LineIdx, 0].legend()
axs[LineIdx, 0].set_xlabel('Time / [ln(s)]')
axs[LineIdx, 0].grid(which='both')
axs[LineIdx, 0].xaxis.set_ticks(np.arange(min(z), max(z), 1.0))

axs[LineIdx, 1].plot(z, Zth_Drv_Filt-a_z, label="RE recovered input")  # Plot some data on the axes.
axs[LineIdx, 1].set_title("Error between filtered and raw interpolated curve")
axs[LineIdx, 1].legend()
axs[LineIdx, 1].grid(which='both')
axs[LineIdx, 1].set_xlabel('Time / [ln(s)]')

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))

plt.show()
