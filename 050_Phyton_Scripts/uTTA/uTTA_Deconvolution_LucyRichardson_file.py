from numpy import genfromtxt                    # numpy 2.1.0
import library.uTTA_Deconvolution as ud_deconv
import library.uTTA_data_processing as udi
import time                                     # part of python 3.12.5


FileNam = ""

# FileNam = os.path.abspath(r"..\..\060_Example_Measurement_Data\Simulated_Measurement_1RC.t3i")
if len(FileNam) < 5:
    FileNam = udi.select_file('Open a t3i-File', (('T3I Measurement Files', '*.t3i'), ('All files', '*.*')))

DataFile, DataFileNoExt, FilePath = udi.split_file_path(FileNam)

start = time.time()

Zth_Import = genfromtxt(FileNam, delimiter='\t', dtype=float, names=True)
Cols = Zth_Import.dtype.names

if len(Cols) > 1:
    deconv = ud_deconv.UttaDeconvolution()
    deconv.import_zth_input_data(Zth_Import[Cols[0]] , Zth_Import[Cols[1]])

    deconv.prepare_zth_deconvolution()

    deconv.deconvolve_zth_full(1000, do_plot=0)

end = time.time()
print("Execution Time: {time:.3f}s".format(time=end - start))
