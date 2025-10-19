import tkinter.filedialog as fd
import os
import numpy as np              # numpy 2.1.0
import numpy.dtypes             # numpy 2.1.0
# from scipy.signal import find_peaks
# import matplotlib.pyplot as plt                 # matplotlib 3.9.2
# from skimage import restoration    # scikit-image 0.24.0
import matplotlib.ticker as ticker
import library.uTTA_data_import as uTTA_data_import
import library.uTTA_data_export as uTTA_data_export
import library.uTTA_data_plotting as ud_plot
import library.uTTA_Reporting as utta_report
import configparser  # part of python 3.12.5


class UttaZthProcessing:
    def __init__(self):
        self.print_to_console = True            # Variable for future use to switch off all the print statements

        self.adc_timebase = np.array([])        # full measurement timebase
        self.adc = np.array([])                 # full measurement ADC values scaled according to the calibration
        self.cooling_start_index = 0            # first array index where the cooling curve starts
        self.adc_cooling = np.array([])         # Cooling Section ADC values
        self.adc_timebase_cooling = np.array([])    # Cooling Section timebase
        self.meta_data = uTTA_data_import.UTTAMetaData()    # all meta data generated during the measurement and postprocessing
        self.jut_imin = 0       # minimum measured current through the JUT
        self.jut_imax = 0       # maximum measured current through the JUT
        self.no_of_tsp = 3
        self.MaxDeltaT_StartEnd = 1.0

        # Parameters of the cooling curve
        self.cooling_start_index = 0        # Index of the sample within the cooling section where zero current is reached
        self.cooling_start_index_max_trsh = 150
        self.zero_current_detection_mode = "Minimum"        # select the mode of detecting were zero current is flowing
        self.zero_current_detection_ratio = 0.312            # Percentag of the current (Max-Min)*Ratio where zero current is considered

        # Heating parameter calculation results
        self.i_heat = 0.0
        self.u_heat = 0.0
        self.p_heat = 0.0

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

        # TDIM Master export settings
        self.export_tdim_reduce_time = 100
        self.export_tdim_max_points = 49999

        # general flags
        self.flag_import_successful = False
        self.flag_heating_calculated = False
        self.flag_zero_current_unfeasible = False  # a flag to disable downstream operations in case of a problem in zero current detection
        self.flag_cooling_curve_calculated = False # a flag to indicate that the cooling curve was extracted

    def load_settings(self, gui_name):

        fileext = gui_name.split(".")[-1]
        filename = gui_name.replace(fileext, "ini")

        if os.path.isfile(filename):        # check if the config file exists
            config = configparser.ConfigParser()
            config.optionxform = str  # type: ignore # set configparser to Case-Sensitive
            config.read_file(open(filename))

            self.no_of_tsp = int(config["Settings"]["NoOfTSP"])
            self.MaxDeltaT_StartEnd = float(config["Settings"]["MaxDeltaT_StartEnd"])
            self.cooling_start_index_max_trsh = int(config["Settings"]["CoolingStartIndexMaxTrsh"])

            self.zero_current_detection_mode = config["Settings"]["ZeroCurrentDetectionMode"]
            self.zero_current_detection_ratio = float(config["Settings"]["ZeroCurrentDetectionRatio"])

            self.InterpolationAverageHW = int(config["Interpolation"]["AvgHalfWidth"])
            self.InterpolationTStart = float(config["Interpolation"]["Tstart"])
            self.InterpolationTEnd = float(config["Interpolation"]["Tend"])

            self.Cth_Si = float(config["Materials"]["Cth_Si"])
            self.rho_Si = float(config["Materials"]["rho_Si"])
            self.kappa_SI = float(config["Materials"]["kappa_SI"])

            self.export_zth_samples_decade = int(config["Export"]["Zth_SamplesDecade"])
            self.export_tdim_max_points = int(config["Export"]["TDIM_MaxSamples"])
            self.export_tdim_reduce_time = float(config["Export"]["TDIM_ReduceTime"])

    def save_settings(self, gui_name):

        fileext = gui_name.split(".")[-1]
        filename = gui_name.replace(fileext, "ini")

        config = configparser.ConfigParser()
        config.optionxform = str  # type: ignore # set configparser to Case-Sensitive
        config.add_section("Settings")
        config.set("Settings", "NoOfTSP", value=str(self.no_of_tsp))
        config.set("Settings", "MaxDeltaT_StartEnd", value=str(self.MaxDeltaT_StartEnd))
        config.set("Settings", "CoolingStartIndexMaxTrsh", value=str(self.cooling_start_index_max_trsh))

        config.set("Settings", "ZeroCurrentDetectionMode", value=str(self.zero_current_detection_mode))
        config.set("Settings", "ZeroCurrentDetectionRatio", value=str(self.zero_current_detection_ratio))
        config.add_section("Interpolation")
        config.set("Interpolation", "AvgHalfWidth", value=str(self.InterpolationAverageHW))
        config.set("Interpolation", "Tstart", value=str(self.InterpolationTStart))
        config.set("Interpolation", "Tend", value=str(self.InterpolationTEnd))
        config.add_section("Materials")
        config.set("Materials", "Cth_Si", value=str(self.Cth_Si))
        config.set("Materials", "rho_Si", value=str(self.rho_Si))
        config.set("Materials", "kappa_SI", value=str(self.kappa_SI))

        config.add_section("Export")
        config.set("Export", "Zth_SamplesDecade", value=str(self.export_zth_samples_decade))
        config.set("Export", "TDIM_MaxSamples", value=str(self.export_tdim_max_points))
        config.set("Export", "TDIM_ReduceTime", value=str(self.export_tdim_reduce_time))


        with open(filename, 'w') as configfile:
            config.write(configfile)

    def import_data(self, file_nam):
        retval = False
        if len(file_nam) > 1:
            self.adc_timebase, self.adc, self.tc, self.meta_data = uTTA_data_import.read_measurement_file(file_nam, 0)
            if len(self.adc_timebase) > 0:
                self.flag_import_successful = True
                print("\033[92mSUCCESS: File import completed\033[0m")
                retval = True
            else:
                print("\033[91mERROR: File import failed due to an unknown reason\033[0m")
        else:
            print("\033[91mERROR: No proper file selected\033[0m")

        return retval

    def interpolate_to_common_timebase(self):
        if self.flag_import_successful:
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
            zero_current_trsh = self.jut_imin

            print("Min Diode Current:  {min:.2f}A; Max Diode current: {max:.2f}A".format(min=self.jut_imin,
                                                                                         max=self.jut_imax))
            print("Zero Current Detection Mode: {mode}.".format(mode=self.zero_current_detection_mode))
            if self.zero_current_detection_mode == "Ratio":
                zero_current_trsh = (self.jut_imax - self.jut_imin) * self.zero_current_detection_ratio
                print("Zero Current Detection Ratio: {ratio}. Threshold: {trsh:.2f}A".format(ratio=self.zero_current_detection_ratio, trsh=zero_current_trsh))
                self.cooling_start_index = find_nearest(self.adc_cooling[3, :], zero_current_trsh)
            else:
                self.cooling_start_index = (np.where(np.isclose(self.adc_cooling[3, :], zero_current_trsh)))[0][0]
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
        i_heat = float(np.mean(self.adc[3, t_calc_start_idx : t_calc_end_idx]))
        u_dio_heated = float(np.mean(self.adc[0, t_calc_start_idx : t_calc_end_idx]))
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
        interp_idx_start = find_nearest(self.adc_timebase_cooling, self.InterpolationTStart)
        interp_idx_end = find_nearest(self.adc_timebase_cooling, self.InterpolationTEnd)

        print(
            "INTERPOLATION: Start: {IntStart: .6f}s; Index: {IdxStart:3d}; End: {IntEnd: .6f}s; Index: {IdxEnd:3d}".format(
                IntStart=self.InterpolationTStart,
                IntEnd=self.InterpolationTEnd,
                IdxStart=interp_idx_start,
                IdxEnd=interp_idx_end))

        interpol_sq_t_start = np.sqrt(self.InterpolationTStart)
        interpol_sq_t_end = np.sqrt(self.InterpolationTEnd)

        # Get the measured temperatures at the interpolation points
        interpol_y_start = float(np.mean(
            self.t_dio_raw[0, interp_idx_start - self.InterpolationAverageHW:interp_idx_start + self.InterpolationAverageHW]))
        interpol_y_end = float(np.mean(
            self.t_dio_raw[0, interp_idx_end - self.InterpolationAverageHW:interp_idx_end + self.InterpolationAverageHW]))

        # Calculation of the interpolation parameters
        # ToDo: Review calculation of k_therm, EstimatedDieSize and DieMaxThickness
        #         dT_J(t_cut)
        #    m = --------------
        #         sqrt(t_cut)
        self.InterpolationFactorM = (interpol_y_end - interpol_y_start) / (interpol_sq_t_end - interpol_sq_t_start)
        self.InterpolationOffset = interpol_y_start - (self.InterpolationFactorM * interpol_sq_t_start)

        # k_therm is calculated from the silicon material constants
        #                       2                    C_th:  Thermal capacity of silicon J*(kg*K)
        #  k_therm = -----------------------------   rho:   Density of silicon kg/m3
        #             +------------------------+     kappa: Heat transmissivity of silicon W/(m*K)
        #         \  / pi * C_th * rho * kappa
        #          \/
        self.k_therm = 2 / np.sqrt(np.pi * self.Cth_Si * self.rho_Si * self.kappa_SI)

        # Approximate area of the active silicon area
        #            P_Heating                  P_Heating: The steady state power of the heating current
        #   A_Chip = ----------- * k_therm
        #                m
        self.EstimatedDieSize = 1000000 * (self.k_therm * (-self.p_heat / self.InterpolationFactorM))
        self.TDie_Start = self.InterpolationOffset  # Starting temperature of the Die at the moment of switch off

        # Calculate the maximum thickness the Die can have until the calculation method becomes unusable
        #                +--------------------+
        #          _    /          2*lambda
        # dchip =   \  /t_valid * ----------
        #            \/            cth*rho
        self.DieMaxThickness = np.sqrt((self.adc_timebase_cooling[interp_idx_start] * 2 * self.kappa_SI) /
                                       (self.Cth_Si * self.rho_Si))  # Die thickness in METER



        print("Maximum Die thickness based on current interpolation: {MaxThick: .2f}µm".
              format(MaxThick=self.DieMaxThickness*1000*1000))

        # Interpolated curve of the temperature.
        # self.t_dio_start_interpolation = (np.sqrt(self.adc_timebase_cooling) * self.InterpolationFactorM +
        #                                  self.InterpolationOffset)
        self.t_dio_start_interpolation = (np.sqrt(self.adc_timebase_cooling[0:interp_idx_end]) * self.InterpolationFactorM +
                                          self.InterpolationOffset)

        # Build the final Zth-curve with interpolated start
        self.t_dio_interpolated = np.copy(self.t_dio_raw)         # take the raw input array

        #overwrite the beginning with the interpolated curve
        # the curves are stitched together at the LEFT interpolation marker
        self.t_dio_interpolated[0, 0:interp_idx_start] = self.t_dio_start_interpolation[0:interp_idx_start]
        print("INTERPOLATION: Start: {StartY: .3f}K; End: {EndY: .3f}K; Factor M: {IntFactM: .4f}; "
              "Offset: {IntOffs: .4f}; Estimated Die Size: {DieSize: .2f}mm²".format(StartY=interpol_y_start,
                                                                                     EndY=interpol_y_end,
                                                                                     IntFactM=self.InterpolationFactorM,
                                                                                     IntOffs=self.InterpolationOffset,
                                                                                     DieSize=self.EstimatedDieSize))

        self.zth = np.zeros(shape=self.adc_cooling.shape)
        self.r_th_static = np.zeros(self.no_of_tsp)
        self.dT_diode = np.zeros(shape=(self.no_of_tsp, len(self.t_dio_interpolated[3, :])))
        # self.dT_diode = np.zeros(shape=(self.no_of_tsp, len(self.t_dio_interpolated[3, interp_idx_start:-1])))
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
                                              self.meta_data.Channels[str('TSP0')]["Name"],
                                              filename,)

    def export_t3i_file(self, filename):
        if not self.flag_zero_current_unfeasible:

            uTTA_data_export.export_t3i_file(self.adc_timebase_cooling, self.zth,
                                             headername=str(self.meta_data.Channels[str("TSP0")]["Name"]) + "\t" +
                                                        str(self.meta_data.Channels[str("TSP1")]["Name"]) + "\t" +
                                                        str(self.meta_data.Channels[str("TSP2")]["Name"]),
                                             filename=filename)
            
    def report_html(self, outfilename):
        utta_report.export(self, outfilename)

    def export_tdim_master(self,fname):
        uTTA_data_export.export_tdim_master_file(self.adc_timebase_cooling,
                                                 self.adc_cooling,
                                                 self.meta_data,
                                                 self.p_heat,
                                                 fname, tdim_data_limit= self.export_tdim_max_points,
                                                 t_reduce_data=self.export_tdim_reduce_time)

    def export_zth_curve(self,fname):
        uTTA_data_export.export_zth_curve(self.adc_timebase_cooling,
                                          self.adc_cooling,
                                          self.meta_data,
                                          self.export_zth_samples_decade,
                                          self.p_heat,
                                          fname)

    def add_cooling_curve_start_plot(self):
        pre_cooling_samples = self.meta_data.CoolingStartBlock * self.meta_data.SamplesPerDecade
        addon_samples = 100
        start = self.cooling_start_index + pre_cooling_samples
        start_time = self.adc_timebase[start]
        before_start = pre_cooling_samples
        after_start = start + addon_samples

        prim_lines = [
            {'x_data': self.adc_timebase[before_start:start] - start_time,
             'y_data': self.adc[0, before_start:start],
             'label': self.meta_data.Channels["TSP0"]["Name"] + " before Zero-Current",
             'axis': 0,
             'style':{'color':'red', 'marker':'x'}},
            {'x_data': self.adc_timebase[start:after_start] - start_time,
             'y_data': self.adc[0, start:after_start],
             'label': self.meta_data.Channels["TSP0"]["Name"] + " after Zero-Current",
             'axis': 0,
             'style':{'color':'red'}}
        ]

        sec_lines = [
            {'x_data': self.adc_timebase[before_start:start]-start_time,
             'y_data': self.adc[3, before_start:start],
             'label': "Current before",
             'axis': 1,
             'style':{'color':'blue', 'marker':'x'}},
            {'x_data': self.adc_timebase[start:after_start]-start_time,
             'y_data': self.adc[3, start:after_start],
             'label': "Current after",
             'axis': 1,
             'style':{'color':'blue'}}
        ]

        formatter = ticker.EngFormatter(unit='s')

        return ud_plot.UttaPlotConfiguration(plot_type='dual_y_axis',
                                                   data=prim_lines,
                                                   secondary_data=sec_lines,
                                                   x_label='Time / [s]',
                                                   x_scale_formatter=formatter,
                                                   y_label='Diode Voltage / [V]',
                                                   secondary_y_label='Heating Current  / [A]',
                                                   title="Cooling Curve Start section")

    def add_input_tsp_measure_curve_plot(self):

        lines = []
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                lines += [
                    {'x_data': self.adc_timebase,
                     'y_data': self.adc[Ch, :],
                     'label': self.meta_data.Channels[ch_tsp]["Name"],
                     'axis': 0}
                ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label='Diode Voltage / [V]',
                                             title="Diode Voltages of the full measurement")


    def add_tsp_measure_cooling_curve_plot(self):

        prim_lines = []
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                prim_lines += [
                    {'x_data': self.adc_timebase_cooling,
                     'y_data': self.adc_cooling[Ch, :],
                     'label': self.meta_data.Channels[ch_tsp]["Name"],
                     'axis': 0}
                ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             x_scale='log',
                                             data=prim_lines,
                                             x_label='Time / [s]',
                                             y_label='Diode Voltage / [V]',
                                             title="Diode Voltages of the cooling section")

    def add_input_current_measure_curve_plot(self):

        lines = [
            {'x_data': self.adc_timebase,
             'y_data': self.adc[3, :],
             'label': "Current",
             'axis': 0}
            ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label='Current / [A]',
                                             title="Drive current")

    def add_current_measure_cooling_curve_plot(self):
        lines = [
            {'x_data': self.adc_timebase_cooling,
             'y_data': self.adc_cooling[3, :],
             'label': "Current",
             'axis': 0}
            ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label='Current / [A]',
                                             title="Drive current in the cooling section")

    def add_diode_dt_curve_plot(self):

        lines = []
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = "TSP{Ch}".format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                lines += [
                    {'x_data': self.adc_timebase_cooling,
                     'y_data': self.t_dio_interpolated[Ch, :],
                     'label': self.meta_data.Channels[ch_tsp]["Name"],
                     'axis': 0}
                ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             x_scale='log',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label=r'$\Delta$T Diode / [K]',
                                             title=r'Calculated Diode $\Delta$T of the cooling section')

    def add_thermocouple_plot(self):
        lines = []
        n_samples = len(self.tc[0])
        for Ch in range(0, 4):
            lines += [
                {'x_data': np.arange(1, n_samples+1),
                 'y_data': self.tc[Ch],
                 'label': "Sensor {no}".format(no=Ch),
                 'axis': 0}
            ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Sample / [N]',
                                             y_label='Temperature / [°C]',
                                             title=r'Measured thermocouple temperatures during the full measurement')

    def add_zth_curve_plot(self):
        lines = [
            {'x_data': self.adc_timebase_cooling,
             'y_data': self.zth[0, :],
             'label': self.meta_data.Channels["TSP0"]["Name"],
             'axis': 0}
        ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             x_scale='log',
                                             y_scale='log',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label='Thermal Impedance / [K/W]',
                                             title=r'Thermal Impedance of the driven JUT')

    def add_zth_coupling_curve_plot(self):
        lines = []

        for Ch in range(1, self.no_of_tsp):
            ch_tsp = 'TSP{Ch}'.format(Ch=Ch)
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                lines += [
                    {'x_data': self.adc_timebase_cooling,
                     'y_data': self.zth[Ch, :],
                     'label': self.meta_data.Channels[ch_tsp]["Name"],
                     'axis': 0}
                ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             x_scale='log',
                                             y_scale='log',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label='Thermal Impedance / [K/W]',
                                             title=r'Thermal Impedance of the monitored JUT')


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
    start = -1

    for i in range(len(indata)):
        if start is -1:
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

    # return the FileName with FileExtension, the bare filename and the directory to the file
    return data_file, data_file_no_ext, file_path

def write_tsp_cal_to_file(filename, tsp_cal):
    uTTA_data_import.write_tsp_cal_to_file(filename, tsp_cal)