import tkinter.filedialog as fd
import os
import numpy as np              # numpy 2.1.0
import numpy.dtypes             # numpy 2.1.0
from scipy.signal import find_peaks
import matplotlib.pyplot as plt                 # matplotlib 3.9.2
from skimage import color, data, restoration    # scikit-image 0.24.0
import uTTA_data_import
import uTTA_data_export
import configparser  # part of python 3.12.5



class UttaZthProcessing:
    def __init__(self):
        self.print_to_console = True            # Variable for future use to switch off all the print statements
        self.data_imported = False
        self.adc_timebase = np.array([])        # full measurement timebase
        self.adc = np.array([])                 # full measurement ADC values scaled according to the calibration
        self.cooling_start_index = 0            # first array index where the cooling curve starts
        self.adc_cooling = np.array([])         # Cooling Section ADC values
        self.adc_timebase_cooling = np.array([])    # Cooling Section timebase
        self.meta_data = uTTA_data_import.UTTAMetaData()    # all meta data generated during the measurement and postprocessing
        self.jut_imin = 0       # minimun measured current through the JUT
        self.jut_imax = 0       # maximum measured current through the JUT
        self.no_of_tsp = 3
        self.MaxDeltaT_StartEnd = 1.0


        # Parameters of the cooling curve
        self.cooling_start_index = 0        # Index of the sample within the cooling section where zero current is reached
        self.cooling_start_index_max_trsh = 150

        # Heating paramter calculation results
        self.i_heat = 0.0
        self.u_heat = 0.0
        self.p_heat = 0.0
        self.flag_heating_calculated = False

        self.flag_zero_current_unfeasible = False  # a flag to disable downstream operations in case of a problem in zero current detection
        self.flag_cooling_curve_calculated = False # a flag to indicate that the cooling curve was extracted

        # Parameters for Interpolation
        self.InterpolationTStart = 0.00010
        self.InterpolationTEnd = 0.00020
        self.__InterpolationCurveMaxLen = 1 # All Interpolation curves will be calculated up to 1s
        self.InterpolationAverageHW = 3   # Should be the half width of the averaged area

        # Parameters for the interpolation depth estimation
        self.Cth_Si = 700.0  # Thermal capacity of silicon J*(kg*K)
        self.rho_Si = 2330.0  # Density of silicon kg/m3
        self.kappa_SI = 148.0  # Heat transmissivity of silicon W/(m*K)

        # Interpolation results
        # ToDo: Review calculation of k_therm, EstimatedDieSize and DieMaxThickness
        self.InterpolationFactorM = 0
        self.InterpolationOffset = 0
        self.k_therm = (2 / np.sqrt(self.Cth_Si * self.rho_Si * self.kappa_SI))
        self.EstimatedDieSize = 0
        self.TDie_Start = 0
        self.DieMaxThickness = 0

        self.tc = np.array([])      # measured thermocouple data

        # Variables for interpolated adc and TC-K values
        self.timebase_int = np.array([])        # interpolated timebase, when ADC and TC-K are interpolated to each other
        self.adc_int = np.array([])             # interpolated ADC-data, when ADC and TC-K are interpolated to each other
        self.tc_int = np.array([])              # interpolated thermocouple data, when ADC and TC-K are interpolated to each other

        self.u_dio_cold_start = np.array([])
        self.u_dio_cold_end = np.array([])
        self.t_monitor_heated = np.array([])
        self.t_dio_raw = np.array([])
        self.t_dio_interpolated = np.array([])
        self.t_dio_start_interpolation = np.array([])

        # Zth curve Data
        self.dT_diode = np.array([])    # delta T curve of each diode based on the interpolated diode voltage curve
        self.zth = np.array([])         # calculated zth curve with the interpolation at the beginning
        self.r_th_static = np.array([]) # static Rth end values of each curve

        # Zth curve export settings
        self.export_zth_samples_decade = 10     # Samples/Decade when exporting the Zth curve

        #general flags
        self.flag_import_successful = False

    def load_settings(self, gui_name):
        filename = gui_name.replace(".py", ".ini")
        if os.path.isfile(filename):        # check if the config file exists
            config = configparser.ConfigParser()
            config.optionxform = str        # set configparser to Case-Sensitive
            config.read_file(open(filename))

            self.no_of_tsp = int(config["Settings"]["NoOfTSP"])
            self.MaxDeltaT_StartEnd = float(config["Settings"]["MaxDeltaT_StartEnd"])
            self.cooling_start_index_max_trsh = int(config["Settings"]["CoolingStartIndexMaxTrsh"])
            self.export_zth_samples_decade = int(config["Settings"]["ExportZTHSamplesDecade"])

            self.InterpolationAverageHW = int(config["Interpolation"]["AvgHalfWidth"])
            self.InterpolationTStart = float(config["Interpolation"]["Tstart"])
            self.InterpolationTEnd = float(config["Interpolation"]["Tend"])

            self.Cth_Si = float(config["Materials"]["Cth_Si"])
            self.rho_Si = float(config["Materials"]["rho_Si"])
            self.kappa_SI = float(config["Materials"]["kappa_SI"])

    def save_settings(self, gui_name):
        filename = gui_name.replace(".py", ".ini")

        config = configparser.ConfigParser()
        config.optionxform = str  # set configparser to Case-Sensitive
        config.add_section("Settings")
        config.set("Settings", "NoOfTSP", value=str(self.no_of_tsp))
        config.set("Settings", "MaxDeltaT_StartEnd", value=str(self.MaxDeltaT_StartEnd))
        config.set("Settings", "CoolingStartIndexMaxTrsh", value=str(self.cooling_start_index_max_trsh))
        config.set("Settings", "ExportZTHSamplesDecade", value=str(self.export_zth_samples_decade))
        config.add_section("Interpolation")
        config.set("Interpolation", "AvgHalfWidth", value=str(self.InterpolationAverageHW))
        config.set("Interpolation", "Tstart", value=str(self.InterpolationTStart))
        config.set("Interpolation", "Tend", value=str(self.InterpolationTEnd))
        config.add_section("Materials")
        config.set("Materials", "Cth_Si", value=str(self.Cth_Si))
        config.set("Materials", "rho_Si", value=str(self.rho_Si))
        config.set("Materials", "kappa_SI", value=str(self.kappa_SI))

        with open(filename, 'w') as configfile:
            config.write(configfile)


    def import_data(self, file_nam):
        retval = False
        if len(file_nam) > 1:
            self.adc_timebase, self.adc, self.tc, self.meta_data = uTTA_data_import.read_measurement_file(file_nam, 0)
            if len(self.adc_timebase) > 0:
                self.data_imported = True
                self.flag_import_successful = True
                print("\033[92mSUCCESS: File import completed\033[0m")
                retval = True
            else:
                print("\033[91mERROR: File import failed due to an unknown reason\033[0m")
        else:
            print("\033[91mERROR: No proper file selected\033[0m")

        return retval

    def interpolate_to_common_timebase(self):
        if self.data_imported:
            print("Number of temperature samples: {TCsamp}, Duration of measurement: {tmeas} = {TCsS} Samples/Second".
                  format(TCsamp=len(self.tc[0]),
                         tmeas=self.adc_timebase[-1],
                         TCsS=len(self.tc[0]) / self.adc_timebase[-1]))

            timebase_int = np.linspace(0, stop=self.adc_timebase[-1], num=int(self.adc_timebase[-1]) + 1)

            num_adc = len(self.adc)
            adc_int = np.zeros((num_adc, len(timebase_int)), numpy.float32)

            for ch_idx in range(0, num_adc):
                adc_int[ch_idx, :] = np.interp(timebase_int, self.adc_timebase, self.adc[ch_idx, :])

            num_tc = len(self.tc)
            timebase_tc = np.linspace(start=0, stop=self.adc_timebase[-1], num=len(self.tc[0]))    # Create a dummy timebase for the thermocouples for interpolation
            tc_int = np.zeros((num_tc, len(timebase_int)), numpy.float32)
            for ch_idx in range(0, num_adc):
                tc_int[ch_idx, :] = np.interp(timebase_int, timebase_tc, self.tc[ch_idx, :])
        else:
            timebase_int = []
            adc_int = []
            tc_int = []

        self.timebase_int = timebase_int
        self.adc_int = adc_int
        self.tc_int = tc_int

        return

    def calculate_cooling_curve(self):

        if self.flag_import_successful:
            # Cut Timebase and measurement to cooling section
            pre_cooling_samples = self.meta_data.CoolingStartBlock * self.meta_data.SamplesPerDecade
            time_base_cooling = (self.adc_timebase[pre_cooling_samples:-1] -
                                 self.adc_timebase[pre_cooling_samples - 1])
            self.adc_cooling = self.adc[:, pre_cooling_samples:-1]

            # Get Min and Max Values of the Full Cooling Curve
            self.jut_imin = min(self.adc_cooling[3, :])
            self.jut_imax = max(self.adc_cooling[3, :])

            print("Min Diode Current:  {min:.2f}A; Max Diode current: {max:.2f}A".format(min=self.jut_imin,
                                                                                         max=self.jut_imax))
            self.cooling_start_index = (np.where(np.isclose(self.adc_cooling[3, :], self.jut_imin)))[0][0]
            print("Index of closest value: " + str(self.cooling_start_index))
            if self.cooling_start_index > self.cooling_start_index_max_trsh:      # An Index larger than that is an indicator of an unusual behaviour of the system
                                                    # The user should review the test setup and the system
                print("\033[91mERROR: The start index of the cooling curve is far out of the nominal range! \n"
                      "Calculation is not feasible and will be stopped!\033[0m")
                self.flag_zero_current_unfeasible = True

            # Cut the measurement data down to the starting point of the cooling phase
            self.adc_cooling = self.adc_cooling[:, self.cooling_start_index:-1]
            self.adc_timebase_cooling = time_base_cooling[self.cooling_start_index:-1] - time_base_cooling[self.cooling_start_index - 1]
            self.flag_cooling_curve_calculated = True

        return

    def add_cooling_curve_start_plot(self, plot_id):
        pre_cooling_samples = self.meta_data.CoolingStartBlock * self.meta_data.SamplesPerDecade
        addon_samples = 100
        start = self.cooling_start_index + pre_cooling_samples
        start_time = self.adc_timebase[start]
        before_start = pre_cooling_samples
        after_start = start + addon_samples

        plot_id.plot(self.adc_timebase[before_start:start]-start_time,
                     self.adc[0, before_start:start],
                     label=self.meta_data.Channels["TSP0"]["Name"] + " before Zero-Current",
                     linestyle="dotted",
                     marker='x',
                     color="blue")  # Plot some data on the axes.

        plot_id.plot(self.adc_timebase[start:after_start]-start_time,
                     self.adc[0, start:after_start],
                     label=self.meta_data.Channels["TSP0"]["Name"],
                     linestyle="solid", color="blue")  # Plot some data on the axes.
        plot_id.set_title("Cooling Curve Start section")
        plot_id.set_ylabel('Diode Voltage / [V]')
        plot_id.set_xlabel('Time / [s]')
        plot_id.grid(which='both')

        sec_plot = plot_id.twinx()
        sec_plot.plot(self.adc_timebase[before_start:start]-start_time,
                     self.adc[3, before_start:start],
                     label="Current before",
                     linestyle="dotted",
                     marker='x',
                     color="red")  # Plot some data on the axes.
        sec_plot.plot(self.adc_timebase[start:after_start]-start_time,
                     self.adc[3, start:after_start],
                     label="Current",
                     linestyle="solid", color="red")  # Plot some data on the axes.
        sec_plot.set_ylabel('Heating Current  / [A]')

        plot_id.legend()
        # sec_plot.legend()

        return


    def calculate_tsp_start_voltages(self):
        u_dio_cold_start = np.zeros((self.no_of_tsp,), numpy.float32)
        u_dio_cold_end = np.zeros((self.no_of_tsp,), numpy.float32)
        t_monitor_heated = np.zeros((self.no_of_tsp,), numpy.float32)
        samp_decade = self.meta_data.SamplesPerDecade
        t_dio = np.zeros(shape=self.adc_cooling.shape)
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)

            chan_cal_data = self.meta_data.Channels[ch_tsp]
            if chan_cal_data["Name"] != "OFF":
                # Calculate the average Diode voltage at the start of the measurement
                # print ("Channel {Chan}, Min ADC: {MinADC}, Max ADC: {MaxADC}".format(Chan=Ch,MinADC=ADC[Ch, :].min(), MaxADC=ADC[Ch, :].max()))
                u_dio_cold_start[Ch] = np.mean(self.adc[Ch, 0:samp_decade])
                # Calculate the average Diode voltage at the end of the measurement
                u_dio_cold_end[Ch] = np.mean(self.adc[Ch, -samp_decade:-1])
                # The TSP Offset is the average diode start voltage
                chan_cal_data["Offset"] = -u_dio_cold_start[Ch]
                t_dio[Ch, :] = (self.adc_cooling[Ch, :] + chan_cal_data["Offset"]) / chan_cal_data["LinGain"]

                # Calculate the start temperature of both monitoring channels to have a good starting point for Zth-Matrix
                t_monitor_heated[Ch] = (np.mean(
                    self.adc[Ch, ((self.meta_data.CoolingStartBlock - 2) * samp_decade):((self.meta_data.CoolingStartBlock - 1) * samp_decade) - 1])
                                        + chan_cal_data["Offset"]) / chan_cal_data["LinGain"]
                if Ch == 0:
                    print(
                        "COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C".format(
                            DUTno=Ch,
                            Ucold=u_dio_cold_start[Ch],
                            UColdEnd=u_dio_cold_end[Ch],
                            dU_DUT=u_dio_cold_start[Ch] - u_dio_cold_end[Ch],
                            dT_DUT=((u_dio_cold_end[Ch] - u_dio_cold_start[Ch]) / chan_cal_data["LinGain"])))
                else:
                    print(
                        "COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C; "
                        "Heated Temp: {T_heated: 3.4f}°C".format(DUTno=Ch,
                                                                 Ucold=u_dio_cold_start[Ch],
                                                                 UColdEnd=u_dio_cold_end[Ch],
                                                                 dU_DUT=u_dio_cold_start[Ch] - u_dio_cold_end[Ch],
                                                                 dT_DUT=((u_dio_cold_end[Ch] - u_dio_cold_start[Ch]) /
                                                                         chan_cal_data["LinGain"]),
                                                                 T_heated=t_monitor_heated[Ch]))
        self.u_dio_cold_start = u_dio_cold_start
        self.u_dio_cold_end = u_dio_cold_end
        self.t_monitor_heated = t_monitor_heated
        self.t_dio_raw = t_dio

    def calculate_diode_heating(self):
        # Calculate the average heating current, voltage and power through the diode
        if not self.flag_import_successful:
            print("\033[93mWARNING: No file imported. Unable to calculate power dissipation!\033[0m")
            return
        if self.meta_data.FlagTSPCalibrationFile:
            print("\033[91mERROR: Unable to calculate power dissipation on a calibration file!\033[0m")
            return

        cooling_start_block = self.meta_data.CoolingStartBlock
        samp_decade = self.meta_data.SamplesPerDecade
        t_calc_start_idx = ((cooling_start_block - 2) * samp_decade)
        t_calc_end_idx = ((cooling_start_block - 1) * samp_decade) - 1
        i_heat = np.mean(self.adc[3, t_calc_start_idx : t_calc_end_idx])
        u_dio_heated = np.mean(self.adc[0, t_calc_start_idx : t_calc_end_idx])
        p_dio_heat = i_heat * u_dio_heated
        print("HEATING VALUES: Range: {tstart:.2f}s to {tend:.2f}s, Current: {curr:.2f}A, Voltage: {volts:.2f}V, Power: {pow:.2f}W".format(
            tstart=self.adc_timebase[t_calc_start_idx],
            tend=self.adc_timebase[t_calc_end_idx],
            curr=i_heat,
            volts=u_dio_heated,
            pow=p_dio_heat))
        self.i_heat = i_heat
        self.p_heat = p_dio_heat
        self.u_heat = u_dio_heated
        self.flag_heating_calculated = True

        return

    def interpolate_zth_curve_start(self):
        interp_points_idx_start = find_nearest(self.adc_timebase_cooling, self.InterpolationTStart)
        interp_points_idx_end = find_nearest(self.adc_timebase_cooling, self.InterpolationTEnd)

        print(
            "INTERPOLATION: Start: {IntStart: .6f}s; Index: {IdxStart:3d}; End: {IntEnd: .6f}s; Index: {IdxEnd:3d}".format(
                IntStart=self.InterpolationTStart,
                IntEnd=self.InterpolationTEnd,
                IdxStart=interp_points_idx_start,
                IdxEnd=interp_points_idx_end))

        interpol_sq_t_start = np.sqrt(self.InterpolationTStart)
        interpol_sq_t_end = np.sqrt(self.InterpolationTEnd)

        # Get the measured temperatures at the interpolation points
        interpol_y_start = np.mean(
            self.t_dio_raw[0, interp_points_idx_start - self.InterpolationAverageHW:interp_points_idx_start + self.InterpolationAverageHW])
        interpol_y_end = np.mean(
            self.t_dio_raw[0, interp_points_idx_end - self.InterpolationAverageHW:interp_points_idx_end + self.InterpolationAverageHW])

        # Calculation of the interpolation parameters
        self.InterpolationFactorM = (interpol_y_end - interpol_y_start) / (interpol_sq_t_end - interpol_sq_t_start)
        self.InterpolationOffset = interpol_y_start - (self.InterpolationFactorM * interpol_sq_t_start)
        self.k_therm = (2 / np.sqrt(self.Cth_Si * self.rho_Si * self.kappa_SI))
        self.EstimatedDieSize = 1000000 * (self.k_therm * (-self.p_heat / self.InterpolationFactorM))
        self.TDie_Start = self.InterpolationOffset  # Starting temperature of the Die at the moment of switch off

        # Calculate the maximum thickness the Die can have until the calculation method becomes unusable
        # dchip = sqrt(t_valid * 2*lambda/(cth*rho))
        self.DieMaxThickness = np.sqrt((self.adc_timebase_cooling[interp_points_idx_start] * 2 * self.kappa_SI) /
                                       (self.Cth_Si * self.rho_Si))  # Die thickness in METER

        print("Maximum Die thickness based on current interpolation: {MaxThick: .2f}µm".
              format(MaxThick=self.DieMaxThickness*1000*1000))

        # Interpolated curve of the temperature.
        self.t_dio_start_interpolation = (np.sqrt(self.adc_timebase_cooling[0:interp_points_idx_end]) * self.InterpolationFactorM +
                                          self.InterpolationOffset)

        # Build the final Zth-curve with interpolated start
        self.t_dio_interpolated = np.copy(self.t_dio_raw)         # take the raw input array

        #overwrite the beginning with the interpolated curve
        self.t_dio_interpolated[0, 0:interp_points_idx_start] = self.t_dio_start_interpolation[0:interp_points_idx_start]
        print("INTERPOLATION: Start: {StartY: .3f}K; End: {EndY: .3f}K; Factor M: {IntFactM: .4f}; "
              "Offset: {IntOffs: .4f}; Estimated Die Size: {DieSize: .2f}mm²".format(StartY=interpol_y_start,
                                                                                     EndY=interpol_y_end,
                                                                                     IntFactM=self.InterpolationFactorM,
                                                                                     IntOffs=self.InterpolationOffset,
                                                                                     DieSize=self.EstimatedDieSize))

        self.zth = np.zeros(shape=self.adc_cooling.shape)
        self.r_th_static = np.zeros(self.no_of_tsp)
        self.dT_diode = np.zeros(shape=(self.no_of_tsp, len(self.t_dio_interpolated[3, :])))
        # self.dT_diode = np.zeros(shape=(self.no_of_tsp, len(self.t_dio_interpolated[3, interp_points_idx_start:-1])))
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                if Ch == 0:
                    # Do the Zth calculation for the driven channel
                    self.dT_diode[Ch, :] = self.t_dio_interpolated[Ch, :] - self.TDie_Start
                    self.zth[Ch, :] = self.dT_diode[Ch, :] / -self.p_heat
                    # take the last 100 samples to calculate the static Zth
                    self.r_th_static[Ch] = np.mean(self.zth[Ch, -100:-1])
                    print("Static Zth for Channel{ChNo}: {ZthStat: .4f}K/W".format(ChNo=Ch, ZthStat=self.r_th_static[Ch]))
                else:
                    # Do the Zth calculation for the Monitor channels
                    # ToDo: Check the correctness of this calculation
                    self.t_monitor_heated[Ch] = self.InterpolationOffset - self.t_monitor_heated[Ch]

                    self.dT_diode[Ch, :] = (self.t_dio_interpolated[Ch, :] -
                                            self.t_dio_interpolated[0, :] +
                                            self.t_monitor_heated[Ch])

                    self.zth[Ch, :] = self.dT_diode[Ch, :] / self.p_heat
                    self.r_th_static[Ch] = np.mean(self.zth[Ch, -100:-1])
                    print("Static Coupling-Zth for Channels 0-{ChNo}: {RthStat: .4f}K/W".
                          format(ChNo=Ch, RthStat=self.r_th_static[Ch]))

    def export_diode_voltages(self, filename):
        uTTA_data_export.write_diode_voltages(self.adc_timebase_cooling, self.adc_cooling,
                                              self.meta_data.Channels["TSP0"]["Name"],
                                              filename,)

    def export_t3i_file(self, filename):
        if not self.flag_zero_current_unfeasible:
            uTTA_data_export.export_t3i_file(self.adc_timebase_cooling, self.zth,
                                             headername=str(self.meta_data.Channels["TSP0"]["Name"]) + "\t" +
                                                        str(self.meta_data.Channels["TSP1"]["Name"]) + "\t" +
                                                        str(self.meta_data.Channels["TSP2"]["Name"]),
                                             filename=filename)

    def export_tdim_master(self,fname):
        uTTA_data_export.export_tdim_master_file(self.adc_timebase_cooling,
                                                 self.adc_cooling,
                                                 self.meta_data,
                                                 fname)

    def export_zth_curve(self,fname):
        uTTA_data_export.export_zth_curve(self.adc_timebase_cooling,
                                          self.adc_cooling,
                                          self.meta_data,
                                          self.export_zth_samples_decade ,
                                          fname)

    def add_input_tsp_measure_curve_plot(self, plot_id):

        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                plot_id.plot(self.adc_timebase, self.adc[Ch, :], label=self.meta_data.Channels[ch_tsp]["Name"])  # Plot some data on the axes.

        plot_id.set_title("Diode Voltages of the full measurement")
        plot_id.set_ylabel('Diode Voltage / [V]')
        plot_id.set_xlabel('Time / [s]')
        plot_id.legend()
        plot_id.grid(which='both')

    def add_tsp_measure_cooling_curve_plot(self, plot_id):

        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                plot_id.semilogx(self.adc_timebase_cooling, self.adc_cooling[Ch, :], label=self.meta_data.Channels[ch_tsp]["Name"])  # Plot some data on the axes.

        plot_id.set_title("Diode Voltages of the cooling section")
        plot_id.set_ylabel('Diode Voltage / [V]')
        plot_id.set_xlabel('Time / [s]')
        plot_id.legend()
        plot_id.grid(which='both')

    def add_input_current_measure_curve_plot(self, plot_id):
        plot_id.plot(self.adc_timebase, self.adc[3, :], label="Current")  # Plot some data on the axes.
        plot_id.set_title("Drive current")
        plot_id.set_ylabel('Current / [A]')
        plot_id.set_xlabel('Time / [s]')
        plot_id.legend()
        plot_id.grid(which='both')

    def add_current_measure_cooling_curve_plot(self, plot_id):
        plot_id.plot(self.adc_timebase_cooling, self.adc_cooling[3, :], label="Current")  # Plot some data on the axes.
        plot_id.set_title("Drive current in the cooling section")
        plot_id.set_ylabel('Current / [A]')
        plot_id.set_xlabel('Time / [s]')
        plot_id.legend()
        plot_id.grid(which='both')

    def add_diode_dt_curve_plot(self, plot_id):
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                plot_id.semilogx(self.adc_timebase_cooling, self.t_dio_interpolated[Ch, :], label=self.meta_data.Channels[ch_tsp]["Name"])  # Plot some data on the axes.

        plot_id.set_title(r'Calculated Diode $\Delta$T of the cooling section')
        plot_id.set_ylabel(r'$\Delta$T Diode / [K]')
        plot_id.set_xlabel('Time / [s]')
        plot_id.legend()
        plot_id.grid(which='both')

    def add_thermocouple_plot(self, plot_id):
        for Ch in range(0, 4):
            plot_id.plot(self.tc[Ch, :], label="Sensor {no}".format(no=Ch))  # Plot some data on the axes.
        plot_id.set_ylabel('Temperature / [°C]')
        plot_id.set_xlabel('Sample')
        plot_id.set_title(r'Measured thermocouple temperatures during the full measurement')
        plot_id.legend()
        plot_id.grid(which='both')

    def add_zth_curve_plot(self, plot_id):

        plot_id.loglog(self.adc_timebase_cooling, self.zth[0, :], label=self.meta_data.Channels["TSP0"]["Name"])  # Plot some data on the axes.
        plot_id.set_title("Thermal Impedance of the driven JUT")
        plot_id.set_ylabel('Thermal Impedance / [K/W]')
        plot_id.set_xlabel('Time / [s]')
        plot_id.legend()
        plot_id.grid(which='both')

    def add_zth_coupling_curve_plot(self, plot_id):
        channels_plotted = 0
        for Ch in range(1, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                plot_id.loglog(self.adc_timebase_cooling, self.zth[Ch, :], label=self.meta_data.Channels[ch_tsp]["Name"])  # Plot some data on the axes.
                channels_plotted += 1

        if channels_plotted:
            plot_id.set_title("Thermal Impedance of the monitored JUT")
            plot_id.set_ylabel('Thermal Impedance / [K/W]')
            plot_id.set_xlabel('Time / [s]')
            plot_id.legend()
            plot_id.grid(which='both')


class UttaDeconvolution:

    def __init__(self):
        # Variables for the Zth deconvolution with Lucy-Richardson Algorithm
        self.rth_stat = 0
        self.deconv_samples_per_decade = 50
        self.z_raw = np.array([])       # the raw converted cooling time base, basically just ln(t)
        self.zth_raw = np.array([])  # the raw converted cooling time base, basically just ln(t)
        self.z = np.array([])           # interpolated, equidistant linear ln(t)-timebase

        self.a_z = np.array([])         # interpolated input Zth-curve with timebase z
        self.dadz = np.array([])        # differentiated input Zth-curve
        self.w_z = np.array([])         # weighing function  --> exp(z - exp(z)), needed for interpolation
        self.deconv_z_shift = 0         # deconv_z_shift = -2.82660000000
        self.deconvolved = np.array([])
        self.dadz_deconvolved = np.array([])
        self.zth_deconvolved = np.array([])
        self.peaks = np.array([])

        # Additional experimental curves
        self.ref_z = np.array([])       # reference curve with a known reference RC Element of 1Ohm and 1F = 1tau
        self.ref_dadz = np.array([])    # differentiated reference curve
        self.ref_peaks = np.array([])
        self.ref_deconv = np.array([])

    def import_zth_input_data(self, timebase, zth):
        self.z_raw = np.log(timebase)
        self.zth_raw = zth

    def prepare_zth_deconvolution(self):

        no_sample_points = int((self.z_raw[-1] - self.z_raw[0]) * self.deconv_samples_per_decade)
        no_sample_points_log = int(np.power(2, np.ceil(np.log2(no_sample_points))))
        print("Number of SamplePoints: {NoSampPoints} SamplePoints power of 2: {NoSampPnts}".format(NoSampPoints=no_sample_points, NoSampPnts=no_sample_points_log))

        log_samp_point_intervall = (self.z_raw[-1] - self.z_raw[0]) / no_sample_points_log
        print("SamplePoint Intervall: {SampInt}".format(SampInt=log_samp_point_intervall))

        z = np.linspace(start=self.z_raw[0], stop=self.z_raw[-1], num=no_sample_points_log) # create constant step width timebase
        self.a_z = np.interp(z, self.z_raw, self.zth_raw)
        self.rth_stat = np.mean(self.a_z[int(0.98 * len(self.a_z)):-1])
        print("Zth end value: {ZthEnd:.3f}, Zth Curve Start Value {Rth_start}K/W".format(ZthEnd=self.rth_stat, Rth_start=self.zth_raw[0]))

        self.dadz = np.diff(self.a_z) / np.diff(z)
        # sum_dadz = np.sum(dadz)
        # dadz = dadz / np.sum(dadz)
        self.w_z = np.exp(z - np.exp(z))
        self.z = z

        self.create_zth_reference_curve()       # for trials generate the Zth reference curve
        return

    def create_zth_reference_curve(self):

        self.ref_z = (1-np.exp(-np.exp(self.z)))     # for testing: create a reference curve with a known reference RC Element of 1Ohm and 1F = 1tau
        self.ref_dadz = np.diff(self.ref_z) / np.diff(self.z)
        return

    def add_deconv_plot_input_zth_curve(self, plot_id):

        plot_id.loglog(np.exp(self.z), self.a_z, label="Input Zth Curve")  # Input curve to be deconvolved
        plot_id.set_title("Input Zth Curve")
        plot_id.set_ylabel('Zth / [K/W]')
        plot_id.set_xlabel('Time / [ln(s)]')
        plot_id.legend()
        plot_id.grid(which='both')
        return

    def add_deconv_input_dadz_plot(self, plot_id):

        plot_id.plot(self.z[:-1], self.dadz, label="da/dz", linestyle='dashed')  # Plot some data on the axes.
        plot_id.set_title("Interpolated and differentiated Zth Curve")
        plot_id.set_ylabel('Derivative of Zth / [K/W/ln(s)')
        plot_id.set_xlabel('Time / [ln(s)]')
        plot_id.legend()
        plot_id.grid(which='both')
        return

    def deconvolve_reference_zth_lucy_richardson(self, iterations):

        self.ref_deconv, self.ref_peaks = self.deconvolve_get_peaks(self.ref_dadz, self.w_z, iterations)

        print("1Ohm + 1F Reference peak height: {PHeight:.4f}, peak location: {ploc:5f}".format(
              PHeight=np.max(self.ref_deconv), ploc=self.deconv_z_shift))
        return

    def deconvolve_get_peaks(self, dadz, w_z, iterations):

        deconv = restoration.richardson_lucy(dadz, self.w_z[:-1] / np.sum(w_z[:-1]),
                                             num_iter=iterations,
                                             clip=False)  # * sum_ref_dadz
        peaks, _ = find_peaks(deconv)

        # ToDo: find a better way to determine the zshift. at the moment this relies on having the ref curve deconvolved first.
        if self.deconv_z_shift == 0:
            self.deconv_z_shift = self.z[peaks[0]]

        return deconv, peaks

    def add_reference_deconv_output_plot(self, plot_id,  iterations):
        plot_id.plot(self.z[:-1] - self.deconv_z_shift, self.ref_deconv,
                     label="Reference deconv with {iter} Iterations".format(iter=iterations))  # Plot some data on the axes.

    def add_deconv_output_plot(self, plot_id,  iterations):
        plot_id.plot(self.z[:-1] - self.deconv_z_shift, self.deconvolved,
                     label="Deconvolved with {iter} Iterations".format(iter=iterations))  #

    def add_dadz_deconv_output_plot(self, plot_id, iterations):
        plot_id.plot(self.z, self.dadz_deconvolved,
                     label="da/dz {iter} Iterations".format(iter=iterations))  #

    def add_dadz_deconv_error_plot(self, plot_id, iterations):
        plot_id.plot(self.z[:-1] - self.deconv_z_shift, self.dadz - self.dadz_deconvolved[:-1],
                     label="Delta da/dz {iter} Iterations".format(iter=iterations))  #

    def add_zth_deconvolution_error_plot(self, plot_id, iterations):
        plot_id.plot(self.z - self.deconv_z_shift, self.zth_deconvolved - self.a_z,
                     label="Delta Zth {iter} Iterations".format(iter=iterations))  # Plot some data on the axes.

    def add_deconv_zth_output_plot(self, plot_id, iterations):
        plot_id.loglog(np.exp(self.z), self.zth_deconvolved,
                       label="Reconstructed Zth {iter} Iterations".format(iter=iterations))  #

    def deconvolve_zth_lucy_richardson(self, iterations):
        self.deconvolved, self.peaks = self.deconvolve_get_peaks(self.dadz, self.w_z, iterations)

        self.report_peaks_to_console(self.peaks)

        # dadz_conv = (np.convolve(deconvolved, w_z, "same") / np.sum(deconvolved)) * (z[2] - z[1])
        self.dadz_deconvolved = (np.convolve(self.deconvolved, self.w_z, "same")) * (self.z[2] - self.z[1])
        self.zth_deconvolved = (np.cumsum(self.dadz_deconvolved) / np.sum(self.deconvolved)) * self.rth_stat + self.a_z[0]
        return

    def report_peaks_to_console(self, peaks):
        outp = ""
        print("Deconvolvable to {n_peaks} peaks".format(n_peaks=len(peaks)))
        for peak in peaks:
            outp = outp + "{tim:.4f};{R:.4f};".format(tim=self.z[peak] - self.deconv_z_shift, R=self.deconvolved[peak])
        print(outp)
        return

    def deconvolve_zth_full(self, iterations, do_plot):
        #print("z-Base Timestep: " + str(self.z[2] - self.z[1]))
        #peaks = []

        self.deconvolve_reference_zth_lucy_richardson(iterations)  # for trials, do the zth reference deconvolution to get the real z-shift
        self.deconvolve_zth_lucy_richardson(iterations)

        fig, axs = plt.subplots(nrows=3, ncols=2, layout="constrained")
        self.add_deconv_plot_input_zth_curve(axs[0 ,0])
        self.add_deconv_zth_output_plot(axs[0, 0], iterations)

        self.add_deconv_input_dadz_plot(axs[0 ,1])
        self.add_dadz_deconv_output_plot(axs[0, 1], iterations)

        self.add_reference_deconv_output_plot(axs[1, 0],  iterations)
        self.add_deconv_output_plot( axs[1, 0],  iterations)

        self.add_dadz_deconv_error_plot(axs[1, 1], iterations)

        self.add_zth_deconvolution_error_plot(axs[2, 0], iterations)

        axs[0, 0].legend()
        axs[0, 0].grid(which='both')

        axs[0, 1].grid(which='both')
        axs[0, 1].legend()

        axs[1, 0].legend()
        axs[1, 0].grid(which='both')

        axs[2, 0].grid(which='both')
        axs[2, 0].legend()

        plt.show()

        return


def find_static_states(indata, threshold=0.01, min_length=5):
    """ Generated with Google Gemini
    Detects static areas within a numpy-array where values stay within a certain threshold and have a minimum length.

    Args:
        indata (numpy.ndarray): Input data array
        threshold (float): Maximum absolute difference between values of the range.
        min_length (int): Minimum amount of consecutive values which must be within the threshold.

    Returns:
        list: a list of tuples which represent the start and end points of each area.
    """

    ranges = []
    start = None

    for i in range(len(indata)):
        if start is None:
            start = i
        elif abs(indata[i] - indata[start]) > threshold:
            if i - start >= min_length:
                ranges.append((start, i - 1))
            start = i

    # checking if the last range is long enough
    if len(indata) - start >= min_length:
        ranges.append((start, len(indata) - 1))

    return ranges

def find_nearest(arr, value):
    # Element in nd array `arr` closest to the scalar value `value`
    idx = np.abs(arr - value).argmin()
    return idx

def select_file(heading, file_filter):
    filename = fd.askopenfilename(
        title=heading,
        initialdir=os.path.realpath(__file__),
        filetypes=file_filter
    )
    return filename

def split_file_path(file_path):
    # get the filename including the file extension (should be the last value in the split tuple)
    data_file = os.path.basename(file_path).split('/')[-1]

    # get the file extension. Should be the last item when splitting the filename at the dots
    file_extension = data_file.split('.')[-1]

    data_file_no_ext = data_file.replace('.' + file_extension, '')
    file_path = os.path.dirname(file_path)
    return data_file, data_file_no_ext, file_path

def write_tsp_cal_to_file(filename, tsp_cal):
    uTTA_data_import.write_tsp_cal_to_file(filename, tsp_cal)