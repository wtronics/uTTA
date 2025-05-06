import numpy as np                              # numpy 2.1.0
from numpy import genfromtxt                    # numpy 2.1.0
import matplotlib.pyplot as plt                 # matplotlib 3.9.2
import uTTA_data_processing

import os                                       # part of python 3.12.5
import time                                     # part of python 3.12.5
import uTTA_data_import

NoOfMonitors = 2
find_peaks = 1
SamplesPerDecade = 50
IterationSteps = np.array([2500], dtype=int)

FileNam = "C:\\temp\\Eigenentwicklungen\\GitHub\\uTTA\\060_Example_Measurement_Data\\Simulated_Measurement_1RC.t3i"
if len(FileNam) < 5:
    FileNam = uTTA_data_import.select_file('Open a t3i-File', (('T3I Measurement Files', '*.t3i'), ('All files', '*.*')))

DataFile, DataFileNoExt, FilePath = uTTA_data_import.split_file_path(FileNam)

start = time.time()

Zth_Import = genfromtxt(FileNam, delimiter='\t', dtype=float, names=True)
Cols = Zth_Import.dtype.names

t = Zth_Import[Cols[0]]
Zth_Drive = Zth_Import[Cols[1]]

uTTA_data_processing.deconvolve_zth_lucy_richardson(t, Zth_Drive, samp_decade=SamplesPerDecade, get_peaks=find_peaks, iterations=IterationSteps)

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))
