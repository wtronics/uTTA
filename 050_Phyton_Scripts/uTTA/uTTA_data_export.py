import numpy as np              # numpy 2.1.0
import numpy.dtypes             # numpy 2.1.0


def write_diode_voltages(timebase, adc, headername, filename):
    dio_voltage_max_lines = len(timebase)
    diode_output = np.zeros(shape=(2, dio_voltage_max_lines))
    diode_output[0, ] = timebase[0:dio_voltage_max_lines]
    diode_output[1, ] = adc[0, 0:dio_voltage_max_lines]
    diode_output = np.transpose(diode_output)

    np.savetxt(filename, diode_output,
               delimiter='\t',
               fmt='%1.4e',
               newline='\n',
               header="Time\t" + str(headername))


def export_t3i_file(timebase, zth, headername, filename):
    zth_output = np.zeros(shape=(len(zth), len(zth[0])))
    zth_output[0, :] = timebase
    zth_output[1, :] = zth[0, :]
    zth_output[2, :] = zth[1, :]
    zth_output[3, :] = zth[2, :]
    zth_output = np.transpose(zth_output)
    np.savetxt(filename, zth_output,
               delimiter='\t',
               fmt='%1.6e',
               newline='\n',
               header="Time\t" + str(headername))
    del zth_output
