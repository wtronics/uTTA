import numpy as np
import matplotlib.pyplot as plt
from numpy import genfromtxt
from tkinter import filedialog as fd
import os

FilePath = os.path.realpath(__file__)


def select_file():
    filetypes = (('T3I Measurement Files', '*.t3i'), ('All files', '*.*'))

    filename = fd.askopenfilename(
        title='Open a T3R-File',
        initialdir=FilePath,
        filetypes=filetypes
    )
    return filename


LogLogPlot = 0
NumCurves = int(input("Please enter the number of Curves you want to compare: "))

fig, axs = plt.subplots(nrows=3, ncols=1, layout="constrained")
for CurveIdx in range(0, int(NumCurves)):
    FileNam = select_file()
    DataFile = os.path.basename(FileNam).split('/')[-1]
    DataFileNoExt = DataFile.replace('.t3i', '')

    Zth_Import = genfromtxt(FileNam, delimiter='\t', dtype=float, names=True)
    Cols = Zth_Import.dtype.names
    FirstValIdx = np.argmax(Zth_Import[Cols[2]] > 0)
    Timebase = Zth_Import[Cols[0]]
    Driver = Zth_Import[Cols[1]]
    Monitor1 = Zth_Import[Cols[2]]
    Monitor2 = Zth_Import[Cols[3]]
    if LogLogPlot == 1:
        axs[0].loglog(Timebase, Driver, label=DataFileNoExt + " " + Cols[1])  # Plot some data on the axes.
        axs[1].loglog(Timebase[FirstValIdx:-1], Monitor1[FirstValIdx:-1], label=DataFileNoExt + " " + Cols[2])  # Plot some data on the axes.
        axs[2].loglog(Timebase[FirstValIdx:-1], Monitor2[FirstValIdx:-1], label=DataFileNoExt + " " + Cols[3])  # Plot some data on the axes.
    else:
        axs[0].semilogx(Timebase, Driver, label=DataFileNoExt + " " + Cols[1])  # Plot some data on the axes.
        axs[1].semilogx(Timebase[FirstValIdx:-1], Monitor1[FirstValIdx:-1], label=DataFileNoExt + " " + Cols[2])  # Plot some data on the axes.
        axs[2].semilogx(Timebase[FirstValIdx:-1], Monitor2[FirstValIdx:-1], label=DataFileNoExt + " " + Cols[3])  # Plot some data on the axes.

axs[0].set_title("Zth Curve of driver element")
axs[0].set_ylabel('Zth / [K/W]')
axs[0].set_xlabel('Time / [s]')
axs[0].legend()
axs[0].grid(which='both')

axs[1].set_title("Zth Curve of monitor element 1")
axs[1].set_ylabel('Zth / [K/W]')
axs[1].set_xlabel('Time / [s]')
axs[1].legend()
axs[1].grid(which='both')

axs[2].set_title("Zth Curve of monitor element 2")
axs[2].set_ylabel('Zth / [K/W]')
axs[2].set_xlabel('Time / [s]')
axs[2].legend()
axs[2].grid(which='both')

plt.show()