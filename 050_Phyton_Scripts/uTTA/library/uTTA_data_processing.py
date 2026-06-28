#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    utta_data_processing.py
Description:    Combines all Zth curve and deconvolution related processing
                functions. 

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           28.09.2025 (moved)
Version:        $VERSION$

--------------------------------------------------------------------------
License:
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0)

You are free to share and adapt this material under the following terms:
- Attribution: You must give appropriate credit.
- NonCommercial: You may not use the material for commercial purposes.
- ShareAlike: You must distribute your contributions under the same license.

The full license text can be found at:
https://creativecommons.org/licenses/by-nc-sa/4.0/
--------------------------------------------------------------------------
"""

import tkinter.filedialog as fd
import os
import numpy as np              
import numpy.dtypes  
from scipy.optimize import nnls
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks          
import matplotlib.ticker as ticker
import library.uTTA_data_import as uTTA_data_import
import library.uTTA_data_export as uTTA_data_export
import library.uTTA_data_plotting as ud_plot
import library.uTTA_Reporting as utta_report
import configparser
import logging


class UttaZthProcessing:
    """Zth curve related processing functions
    """    
    def __init__(self, logger:logging.Logger|None=None):
        """Initializes the Zth processing class

        Args:
            logger (logging.Logger | None, optional): Logging Handle to log into a common log-file. Defaults to None.
        """        

        if logger is None:
            self.logger = logging.getLogger("dummy")
            self.logger.addHandler(logging.NullHandler())
            self.logger.propagate = False # Important: prevents forwarding to the root logger
        else:
            self.logger = logger

        self.time_full = np.array([])           # full measurement timebase
        self.udiode_full = np.array([])                 # full measurement ADC values scaled according to the calibration
        self.current_full = np.array([])        # full measurement current measurement values
        self.cooling_start_idx = 0              # first array index where the cooling curve starts
        self.udiode_cooling = np.array([])         # Cooling Section scaled ADC values
        self.current_cooling = np.array([])     # current measured during the cooling curve
        self.time_cooling = np.array([])        # Cooling Section timebase
        self.meta_data = uTTA_data_import.UTTAMetaData()    # all meta data generated during the measurement and postprocessing
        self.jut_imin = 0       # minimum measured current through the JUT
        self.jut_imax = 0       # maximum measured current through the JUT
        self.no_of_tsp = 3
        self.MaxDeltaT_StartEnd = 1.0

        # Parameters of the cooling curve
        self.cooling_start_idx = 0        # Index of the sample within the cooling section where zero current is reached
        self.cooling_start_idx_max_trsh = 150
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

        # Deconvolution settings
        self.deconv_method = "Bayes"
        self.deconv_samples_per_decade = 20

        # Setting especially for Lucy-Richardson (Bayes) Method
        self.lr_iterations = 1000
        self.lr_sharpening=0.0
        self.lr_pad_decades = 2
        self.z_raw = np.array([]) 

        # Variables for interpolated adc and TC-K values
        self.time_interp = np.array([])        # interpolated timebase, when ADC and TC-K are interpolated to each other
        self.adc_interp = np.array([])         # interpolated ADC-data, when ADC and TC-K are interpolated to each other
        self.tc_interp = np.array([])          # interpolated thermocouple data, when ADC and TC-K are interpolated to each other

        self.u_dio_cold_start = np.array([])
        self.u_dio_cold_end = np.array([])
        self.t_monitor_heated_offs = np.array([])
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

    def load_settings(self, gui_name: str):
        """Loads GUI settings from the ini-File into the class itself

        Args:
            gui_name (str): Name of the GUI to find the matching ini-file
        """        

        fileext = gui_name.split(".")[-1]
        filename = gui_name.replace(fileext, "ini")

        if os.path.isfile(filename):        # check if the config file exists
            config = configparser.ConfigParser()
            config.optionxform = str  # type: ignore # set configparser to Case-Sensitive
            config.read_file(open(filename))

            self.no_of_tsp = int(config.get("Settings", "NoOfTSP", fallback='3'))
            self.MaxDeltaT_StartEnd = float(config.get("Settings", "MaxDeltaT_StartEnd", fallback='1'))
            self.cooling_start_idx_max_trsh = int(config.get("Settings", "CoolingStartIndexMaxTrsh", fallback='150'))

            self.zero_current_detection_mode = config.get("Settings", "ZeroCurrentDetectionMode", fallback='Minimum')
            self.zero_current_detection_ratio = float(config.get("Settings", "ZeroCurrentDetectionRatio", fallback='0.312'))

            self.InterpolationAverageHW = int(config.get("Interpolation", "AvgHalfWidth", fallback='3'))
            self.InterpolationTStart = float(config.get("Interpolation", "Tstart", fallback='0.0001'))
            self.InterpolationTEnd = float(config.get("Interpolation", "Tend", fallback='0.0002'))

            self.Cth_Si = float(config.get("Materials", "Cth_Si", fallback='700.0'))
            self.rho_Si = float(config.get("Materials", "rho_Si", fallback='2330.0'))
            self.kappa_SI = float(config.get("Materials", "kappa_SI", fallback='148.0'))

            self.export_zth_samples_decade = int(config.get("Export", "Zth_SamplesDecade", fallback='10'))
            self.export_tdim_max_points = int(config.get("Export", "TDIM_MaxSamples", fallback='49999'))
            self.export_tdim_reduce_time = float(config.get("Export", "TDIM_ReduceTime", fallback='100.0'))
            
            self.deconv_samples_per_decade = int(config.get("Deconvolution_LucyRichardson", "SamplesDecade", fallback='20'))
            self.lr_pad_decades = int(config.get("Deconvolution_LucyRichardson", "Pre_Post_Pad_Decades", fallback='2'))
            self.lr_sharpening = float(config.get("Deconvolution_LucyRichardson", "LR_Peak_Sharpening", fallback='0.0'))
            self.lr_iterations = int(config.get("Deconvolution_LucyRichardson", "LR_Iterations", fallback='1000'))

    def save_settings(self, gui_name: str):
        """Saves the current GUI settings into an ini-file with the same name as the GUI.

        Args:
            gui_name (str): Name of the GUI Application. This name will be used as file name.
        """        

        fileext = gui_name.split(".")[-1]
        filename = gui_name.replace(fileext, "ini")

        config = configparser.ConfigParser()
        config.optionxform = str  # type: ignore # set configparser to Case-Sensitive
        config.add_section("Settings")
        config.set("Settings", "NoOfTSP", value=str(self.no_of_tsp))
        config.set("Settings", "MaxDeltaT_StartEnd", value=str(self.MaxDeltaT_StartEnd))
        config.set("Settings", "CoolingStartIndexMaxTrsh", value=str(self.cooling_start_idx_max_trsh))

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

        config.add_section("Deconvolution_LucyRichardson")
        config.set("Deconvolution_LucyRichardson", "SamplesDecade", value=str(self.deconv_samples_per_decade))
        config.set("Deconvolution_LucyRichardson", "Pre_Post_Pad_Decades", value=str(self.lr_pad_decades))
        config.set("Deconvolution_LucyRichardson", "LR_Peak_Sharpening", value=str(self.lr_sharpening))
        config.set("Deconvolution_LucyRichardson", "LR_Iterations", value=str(self.lr_iterations))

        with open(filename, 'w') as configfile:
            config.write(configfile)

    def import_data(self, file_nam: str) ->bool:
        """Imports the data from a utta measurement file (*.umf) an preprocesses the data into a usable format.
        The data will be stored within the class

        Args:
            file_nam (str): Path to the measurement file

        Returns:
            bool: True when import was completed without errors
        """        
        retval = False
        self.flag_import_successful = False
        if len(file_nam) > 1:
            self.time_full, adc, self.tc, self.meta_data = uTTA_data_import.read_measurement_file(file_nam, 0, logger=self.logger)
            if len(self.time_full) > 0:
                self.udiode_full = adc[0:3, :]
                self.current_full = adc[3, :]
                self.flag_import_successful = True
                self.logger.info(f"SUCCESS: File import <{file_nam}> completed")
                retval = True
            else:
                self.flag_import_successful = False
                self.logger.error("File import failed due to an unknown reason")
        else:
            self.flag_import_successful = False
            self.logger.error("No proper file selected")

        return retval

    ###################################################
    ######## DATA PROCESSING ##########################
    ###################################################
    
    def interpolate_to_common_timebase(self):
        """Interpolates the measurement data of ADCs and thermocouples to a common timebase.
           This interpolation helps when doing data postprocessing for a TSP calibration as ADC 
           values and Thermocouple values are now on a common timebase.
        """        

        if self.flag_import_successful:         # prevent interpolation in case no data is available
            self.logger.debug(f"Number of temperature samples: {len(self.tc[0])}, "
                             f"Duration of measurement: {self.time_full[-1]} = {len(self.tc[0]) / self.time_full[-1]} Samples/Second")

            timebase_int = np.linspace(0, stop=self.time_full[-1], num=int(self.time_full[-1]) + 1)

            num_adc = len(self.udiode_full)
            adc_int = np.zeros((num_adc, len(timebase_int)), numpy.float32)

            for ch_idx in range(0, num_adc):
                adc_int[ch_idx, :] = np.interp(timebase_int, self.time_full, self.udiode_full[ch_idx, :])

            num_tc = len(self.tc)
            timebase_tc = np.linspace(start=0, stop=self.time_full[-1], num=len(self.tc[0]))    # Create a dummy timebase for the thermocouples for interpolation
            tc_int = np.zeros((num_tc, len(timebase_int)), numpy.float32)
            for ch_idx in range(0, num_adc):
                tc_int[ch_idx, :] = np.interp(timebase_int, timebase_tc, self.tc[ch_idx, :])
        else:
            timebase_int = []
            adc_int = []
            tc_int = []

        self.time_interp = timebase_int
        self.adc_interp = adc_int
        self.tc_interp = tc_int

        return

    def calculate_cooling_curve(self):
        """ First step of postprocessing measurement data from uTTA device. 
            This procedure includes:
            - Identification of the first block of the cooling section
            - Analysis of current during cooling section, including measurement of min and max current (jut_imin and jut_imax)
            - Zero Heating Current Detection: Actual starting point of the cooling curve. There are two detection methods, of which one can be chosen:
                1. Minimum: Cooling Curve starts at the first sample which is equal to the minimum current
                2. Ratio: The cooling curve starts as soon as the heating current has dropped below "zero_current_detection_ratio * (jut_imax - jut_imin)". This method trys to account 
                   for the RC-filter between the current sense amplifier and the ADC. Therefore the real world heating current will be switched off a little bit earlier than
                   what the ADC readings indicate. 
            - Rescaling of the cooling timebase. t=0 is shifted to the sample detected by the zero heating current detection
            - Calculation of the heating current, voltage and power by averaging data from the last data block before the cooling section starts
        """
        if self.meta_data.FlagTSPCalibrationFile:
            self.logger.error("Unable to calculate power dissipation on a calibration file!")
            return

        if self.flag_import_successful:
            # Cut Timebase and measurement to cooling section
            pre_cooling_samples = self.meta_data.CoolingStartBlock * self.meta_data.SamplesPerDecade
            time_base_cooling = (self.time_full[pre_cooling_samples:] -
                                 self.time_full[pre_cooling_samples - 1])
            self.udiode_cooling = self.udiode_full[:, pre_cooling_samples:]
            self.current_cooling = self.current_full[pre_cooling_samples:]

            # Get Min and Max Values of the Full Cooling Curve
            self.jut_imin = min(self.current_cooling)
            self.jut_imax = max(self.current_cooling)
            zero_current_trsh = self.jut_imin

            self.logger.debug(f"Min Diode Current:  {self.jut_imin:.2f}A; Max Diode current: {self.jut_imax:.2f}A")
            self.logger.debug(f"Zero Current Detection Mode: {self.zero_current_detection_mode}.")

            if self.zero_current_detection_mode == "Ratio":
                zero_current_trsh = (self.jut_imax - self.jut_imin) * self.zero_current_detection_ratio
                self.cooling_start_idx = find_nearest(self.current_cooling, zero_current_trsh)

                self.logger.debug(f"Zero Current Detection Ratio: {self.zero_current_detection_ratio}. Threshold: {zero_current_trsh:.2f}A")
            else:
                self.cooling_start_idx = (np.where(np.isclose(self.current_cooling, zero_current_trsh)))[0][0]

                self.logger.debug(f"Index of closest value: {self.cooling_start_idx}")

            if self.cooling_start_idx > self.cooling_start_idx_max_trsh:      # An Index larger than that is an indicator of an unusual behaviour of the system
                                                    # The user should review the test setup and the system
                self.logger.error("The start index of the cooling curve is far out of the nominal range! \n"
                                  "Calculation is not feasible and will be stopped!")
                self.flag_zero_current_unfeasible = True

            # Cut the measurement data down to the starting point of the cooling phase
            self.udiode_cooling = self.udiode_cooling[:, self.cooling_start_idx:]
            self.current_cooling = self.current_cooling[self.cooling_start_idx:]
            self.time_cooling = time_base_cooling[self.cooling_start_idx:] - time_base_cooling[self.cooling_start_idx - 1]
            self.flag_cooling_curve_calculated = True

            # Calculate the average heating current, voltage and power through the diode 
            cooling_start_block = self.meta_data.CoolingStartBlock
            samp_decade = self.meta_data.SamplesPerDecade
            t_calc_start_idx = ((cooling_start_block - 2) * samp_decade)
            t_calc_end_idx = ((cooling_start_block - 1) * samp_decade) - 1
            i_heat = float(np.mean(self.current_full[t_calc_start_idx : t_calc_end_idx]))
            u_dio_heated = float(np.mean(self.udiode_full[0, t_calc_start_idx : t_calc_end_idx]))
            p_dio_heat = i_heat * u_dio_heated

            self.logger.debug(f"HEATING VALUES: Range: {self.time_full[t_calc_start_idx]:.2f}s to {self.time_full[t_calc_end_idx]:.2f}s,"
                            f"Current: {i_heat:.2f}A, Voltage: {u_dio_heated:.2f}V, Power: {p_dio_heat:.2f}W")
            self.i_heat = i_heat
            self.p_heat = p_dio_heat
            self.u_heat = u_dio_heated
            self.flag_heating_calculated = True
        else:
            self.logger.error("No file imported. Unable to calculate cooling curve and power dissipation!")
                
        return

    def calculate_tsp_start_voltages(self):
        """Calculates voltages at the start and end of each measurement. 
        This way the temperature difference between start and end of the measurement can be calculated.
        Too high differences in between these temperatures may indicate a problem during the measurement.
        """        
        u_dio_cold_start = np.zeros((self.no_of_tsp,), numpy.float32)
        u_dio_cold_end = np.zeros((self.no_of_tsp,), numpy.float32)
        t_monitor_heated = np.zeros((self.no_of_tsp,), numpy.float32)
        samp_decade = self.meta_data.SamplesPerDecade
        t_dio = np.zeros_like(self.udiode_cooling)
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = f"TSP{Ch}"

            chan_cal_data = self.meta_data.Channels[ch_tsp]
            if chan_cal_data["Name"] != "OFF":
                # Calculate the average Diode voltage at the start of the measurement
                u_dio_cold_start[Ch] = np.mean(self.udiode_full[Ch, 0:samp_decade])
                # Calculate the average Diode voltage at the end of the measurement
                u_dio_cold_end[Ch] = np.mean(self.udiode_full[Ch, -samp_decade:-1])
                # The TSP Offset is the average diode start voltage
                chan_cal_data["Offset"] = -u_dio_cold_start[Ch]
                t_dio[Ch, :] = (self.udiode_cooling[Ch, :] + chan_cal_data["Offset"]) / chan_cal_data["LinGain"]

                # Calculate the start temperature of both monitoring channels to have a good starting point for Zth-Matrix
                t_monitor_heated[Ch] = (np.mean(
                    self.udiode_full[Ch, ((self.meta_data.CoolingStartBlock - 2) * samp_decade):((self.meta_data.CoolingStartBlock - 1) * samp_decade) - 1])
                                        + chan_cal_data["Offset"]) / chan_cal_data["LinGain"]
                
                if Ch == 0:
                    self.logger.debug(f"COLD VOLTAGE: DUT{Ch} at Start: {u_dio_cold_start[Ch]: 3.4f}V; at End: {u_dio_cold_end[Ch]: 3.4f}V;" 
                                     f" Delta U: {u_dio_cold_start[Ch] - u_dio_cold_end[Ch]: 3.4f}V;"
                                     f" Delta T: {((u_dio_cold_end[Ch] - u_dio_cold_start[Ch]) / chan_cal_data["LinGain"]): 3.4f}°C")
                else:
                    self.logger.debug(f"COLD VOLTAGE: DUT{Ch} at Start: {u_dio_cold_start[Ch]: 3.4f}V; at End: {u_dio_cold_end[Ch]: 3.4f}V;"
                                     f" Delta U: {u_dio_cold_start[Ch] - u_dio_cold_end[Ch]: 3.4f}V;"
                                     f" Delta T: {((u_dio_cold_end[Ch] - u_dio_cold_start[Ch]) /chan_cal_data["LinGain"]): 3.4f}°C; "
                                     f"Heated Temp: {t_monitor_heated[Ch]: 3.4f}°C")
        self.u_dio_cold_start = u_dio_cold_start
        self.u_dio_cold_end = u_dio_cold_end
        self.t_monitor_heated_offs = t_monitor_heated
        self.t_monitor_heated = np.zeros((self.no_of_tsp,), numpy.float32)
        self.t_dio_raw = t_dio

    def interpolate_zth_curve_start(self):
        """Interpolation function to do the interpolation at the beginning of the cooling phase.
        This is needed to get rid of the electrical transient which occurs at the switch off of the heating current.
        """        
        interp_idx_start = find_nearest(self.time_cooling, self.InterpolationTStart)
        interp_idx_end = find_nearest(self.time_cooling, self.InterpolationTEnd)

        self.logger.debug(f"INTERPOLATION: Start: {self.InterpolationTStart:.6f}s; Index: {self.InterpolationTEnd:.0f};"
                         f" End: {interp_idx_start:.6f}s; Index: {interp_idx_end:.0f}")

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
        self.DieMaxThickness = np.sqrt((self.time_cooling[interp_idx_start] * 2 * self.kappa_SI) /
                                       (self.Cth_Si * self.rho_Si))  # Die thickness in METER

        self.logger.info(f"Maximum Die thickness based on current interpolation: {self.DieMaxThickness*1000*1000: .2f}µm")

        # Interpolated curve of the temperature.
        # self.t_dio_start_interpolation = (np.sqrt(self.adc_timebase_cooling) * self.InterpolationFactorM +
        #                                  self.InterpolationOffset)
        self.t_dio_start_interpolation = (np.sqrt(self.time_cooling[0:interp_idx_end]) * self.InterpolationFactorM +
                                          self.InterpolationOffset)

        # Build the final Zth-curve with interpolated start
        self.t_dio_interpolated = np.copy(self.t_dio_raw)         # take the raw input array
        

        #overwrite the beginning with the interpolated curve
        # the curves are stitched together at the LEFT interpolation marker
        self.t_dio_interpolated[0, 0:interp_idx_start] = self.t_dio_start_interpolation[0:interp_idx_start]
        self.logger.info(f"INTERPOLATION: Start: {interpol_y_start: .3f}K; End: {interpol_y_end: .3f}K; Factor M: {self.InterpolationFactorM: .4f}; "
                         f"Offset: {self.InterpolationOffset: .4f}; Estimated Die Size: {self.EstimatedDieSize: .2f}mm²")

        self.zth = np.zeros_like(self.udiode_cooling) * np.nan
        self.r_th_static = np.zeros(self.no_of_tsp)
        self.dT_diode = np.zeros(shape=(self.no_of_tsp, len(self.t_dio_interpolated[0, :])))
        # self.dT_diode = np.zeros(shape=(self.no_of_tsp, len(self.t_dio_interpolated[3, interp_idx_start:-1])))
        for Ch in range(0, self.no_of_tsp):
            ch_tsp = f"TSP{Ch}"
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                if Ch == 0:
                    # Do the Zth calculation for the driven channel
                    self.dT_diode[Ch, :] = self.t_dio_interpolated[Ch, :] - self.TDie_Start
                    self.zth[Ch, :] = self.dT_diode[Ch, :] / -self.p_heat
                    # take the last 100 samples to calculate the static Zth
                    self.r_th_static[Ch] = np.mean(self.zth[Ch, -100:-1])
                    self.logger.info(f"Static Zth for Channel{Ch}: {self.r_th_static[Ch]: .4f}K/W")
                else:
                    # Do the Zth calculation for the Monitor channels
                    # TODO: Check the correctness of this calculation

                    self.t_dio_interpolated[Ch, 0:interp_idx_start] = np.nan    # mask the electrical transient within the calculation
                    self.t_monitor_heated[Ch] = self.InterpolationOffset - self.t_monitor_heated_offs[Ch]

                    self.dT_diode[Ch,interp_idx_start:] = (self.t_dio_interpolated[Ch, interp_idx_start:] - self.t_dio_interpolated[0, interp_idx_start:] + self.t_monitor_heated[Ch])
                    
                    self.zth[Ch, interp_idx_start:] = self.dT_diode[Ch, interp_idx_start:] / self.p_heat
                    self.r_th_static[Ch] = np.mean(self.zth[Ch, -100:-1])
                    self.logger.info(f"Static Coupling-Zth for Channels 0-{Ch}: {self.r_th_static[Ch]: .4f}K/W")

    ###################################################
    ######## DECONVOLUTION ############################
    ###################################################

    def zth_deconvolution_bayes(self):
        """
        Prepares data for the upcoming deconvolution and does the deconvolution using the bayes / Lucy-Richardson method:
            - prepares a new, evenly spaced timebase in ln(t)-space
            - adds padding to the timebase and extrapolates the measure curve (to improve the bayes algorithm)
            - do the differentiation (da/dz) of the input curve
            - create the kernel function (greens function) for the deconvolution
            - do the deconvolution
            - remove 

        """
        z_raw = np.log(self.time_cooling)
        self.rth_stat = np.max(self.zth[0, :])
        
        self.logger.info(f"Zth end value: {self.rth_stat:.3f} K/W, Zth Curve Start Value {self.zth[0, 0]} K/W")

        # 1. Standardize the dz (log-interval)
        dz = 1.0 / self.deconv_samples_per_decade

        # 2. Resample onto a strictly even grid
        z = np.arange(z_raw[0], z_raw[-1] + dz/2, dz)
        a_z = np.interp(z, z_raw, self.zth[0, :])

        # 3. Create Padding
        z_left = np.arange(z[0] - self.lr_pad_decades * np.log(10), z[0], dz)
        z_right = np.arange(z[-1] + dz, z[-1] + self.lr_pad_decades * np.log(10), dz)
        
        # Extrapolate left (sqrt(t)) and right (flat)
        m_z = a_z[0] / np.sqrt(np.exp(z[0]))
        zth_left = m_z * np.sqrt(np.exp(z_left))
        zth_right = np.ones_like(z_right) * a_z[-1]
        
        z_padded = np.concatenate([z_left, z, z_right])
        zth_padded = np.concatenate([zth_left, a_z, zth_right])
        
        # 4. Gradient
        dadz_padded = np.maximum(np.gradient(zth_padded, dz), 1e-15)

        # 5. ASYMMETRIC KERNEL ALIGNMENT (Fixes the Right Shift)
        # The peak of exp(z - exp(z)) is exactly at z=0.
        # We MUST ensure z=0 is the center of the kernel array for 'same' mode.
        half_k = 10 # 10 decades range
        z_k = np.arange(-half_k, half_k, dz) 
        kernel = np.exp(z_k - np.exp(z_k))
        kernel /= (np.sum(kernel) * dz) # Sum to 1 ensures gain = 1
        k_adj = kernel[::-1]

        # 6. Bayes Iteration
        h = np.ones_like(dadz_padded) * (np.max(dadz_padded) * 0.1)
        for i in range(self.lr_iterations):
            pred = np.convolve(h, kernel, mode='same') * dz
            ratio = dadz_padded / (pred + 1e-15)
            h *= np.convolve(ratio, k_adj, mode='same')
            
            if self.lr_sharpening > 0 and i % 10 == 0:
                # Sharpening
                h = np.maximum(h + self.lr_sharpening * (h - gaussian_filter(h, 1.2)), 1e-15)

        # 7. Reverse Calculation
        # Use the standard kernel to see if we match the original dadz
        dadz_reconstructed_padded = np.convolve(h, kernel, mode='same') * dz
        
        # 8. Integration to Zth (Fixes the Level Issue)
        # Zth is the integral of dadz over dz
        self.zth_reconstructed_padded = np.cumsum(dadz_reconstructed_padded) * dz

        # 9. Final Calibration
        # Because Bayes is iterative, it might stop at 99% or 101%. 
        # We force the final level to match the physical measurement.

        zth_reconst_max = self.zth_reconstructed_padded[-1]
        zth_gain_correction = self.rth_stat / zth_reconst_max
        print(f"Zth Gain Correction factor: {zth_gain_correction}")
        
        # 10. Crop back to original scale
        start_idx = len(z_left)
        end_idx = start_idx + len(z)
        
        self.z = z
        self.a_z = a_z
        self.deconvolved_spectrum = h[start_idx:end_idx] * dz * dz
        self.zth_deconvolved = self.zth_reconstructed_padded[start_idx:end_idx] * zth_gain_correction
        
        # Final Level Check
        print(f"Final Zth Level: {self.zth_deconvolved[-1]:.4f} (Target: {self.rth_stat:.4f})")

        area_h = np.sum(h) * dz * dz
        print(f"Spectrum Total Resistance: {area_h:.4f}")
        print(f"Measured Total Resistance: {self.rth_stat:.4f}")

        return

    ###################################################
    ######## DATA EXPORT ##############################
    ###################################################

    def export_diode_voltages(self, filename: str):
        uTTA_data_export.write_diode_voltages(self.time_cooling, self.udiode_cooling,
                                              self.meta_data.Channels[str('TSP0')]["Name"],
                                              filename,)

    def export_t3i_file(self, filename: str):
        if not self.flag_zero_current_unfeasible:

            uTTA_data_export.export_t3i_file(self.time_cooling, self.zth,
                                             headername=(f'{self.meta_data.Channels["TSP0"]["Name"]}\t'
                                                         f'{self.meta_data.Channels["TSP1"]["Name"]}\t'
                                                         f'{self.meta_data.Channels["TSP2"]["Name"]}'),
                                             filename=filename)

    def export_tdim_master(self,fname: str):
        uTTA_data_export.export_tdim_master_file(self.time_cooling,
                                                 self.udiode_cooling,
                                                 self.meta_data,
                                                 self.p_heat,
                                                 fname, tdim_data_limit= self.export_tdim_max_points,
                                                 t_reduce_data=self.export_tdim_reduce_time)

    def export_zth_curve(self,fname: str):
        uTTA_data_export.export_zth_curve(self.time_cooling,
                                          self.zth,
                                          self.meta_data,
                                          self.export_zth_samples_decade,
                                          self.p_heat,
                                          fname)
        
    ###################################################
    ######## REPORT OUTPUT ############################
    ###################################################      
    def report_html(self, outfilename: str):
        utta_report.export(self, outfilename)
    
    ###################################################
    ######## PLOTTING #################################
    ###################################################

    def add_cooling_curve_start_plot(self):
        pre_cooling_samples = self.meta_data.CoolingStartBlock * self.meta_data.SamplesPerDecade
        addon_samples = 100
        start = self.cooling_start_idx + pre_cooling_samples
        start_time = self.time_full[start]
        before_start = pre_cooling_samples
        after_start = start + addon_samples

        prim_lines = [
            {'x_data': self.time_full[before_start:start] - start_time,
             'y_data': self.udiode_full[0, before_start:start],
             'label': f"{self.meta_data.Channels["TSP0"]["Name"]} before Zero-Current",
             'axis': 0,
             'style':{'color':'red', 'marker':'x'}},
            {'x_data': self.time_full[start:after_start] - start_time,
             'y_data': self.udiode_full[0, start:after_start],
             'label': f"{self.meta_data.Channels["TSP0"]["Name"]} after Zero-Current",
             'axis': 0,
             'style':{'color':'red'}}
        ]

        sec_lines = [
            {'x_data': self.time_full[before_start:start]-start_time,
             'y_data': self.current_full[before_start:start],
             'label': "Current before",
             'axis': 1,
             'style':{'color':'blue', 'marker':'x'}},
            {'x_data': self.time_full[start:after_start]-start_time,
             'y_data': self.current_full[start:after_start],
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
            ch_tsp = f"TSP{Ch}"
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                lines += [
                    {'x_data': self.time_full,
                     'y_data': self.udiode_full[Ch, :],
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
            ch_tsp = f"TSP{Ch}"
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                prim_lines += [
                    {'x_data': self.time_cooling,
                     'y_data': self.udiode_cooling[Ch, :],
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
            {'x_data': self.time_full,
             'y_data': self.current_full,
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
            {'x_data': self.time_cooling,
             'y_data': self.current_cooling,
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
            ch_tsp = f"TSP{Ch}"
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                lines += [
                    {'x_data': self.time_cooling,
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
                {'x_data': np.arange(0, n_samples),
                 'y_data': self.tc[Ch],
                 'label': f"Sensor {Ch}",
                 'axis': 0}
            ]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Sample / [N]',
                                             y_label='Temperature / [°C]',
                                             title=r'Measured thermocouple temperatures during the full measurement')

    def add_zth_curve_plot(self):
        lines = [
            {'x_data': self.time_cooling,
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
            ch_tsp = f'TSP{Ch}'
            if self.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                lines += [
                    {'x_data': self.time_cooling,
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
    
    ###################################################
    ######## DECONVOLUTION RELATED PLOTTING ###########
    ###################################################

    def add_deconv_tau_output_plot(self):
        lines = [
                {'x_data': self.z,
                 'y_data': self.deconvolved_spectrum,
                 'label': f"Deconvolved with {self.lr_iterations} Iterations",
                 'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Tau / [s]',
                                             y_label='Zth / [K/W]',
                                             title='Deconvolved Spectrum')
 
    def add_zth_deconvolution_error_plot(self):
        lines = [
                {'x_data': self.z,
                 'y_data': self.zth_deconvolved - self.a_z,
                 'label': f"Delta Zth {self.lr_iterations} Iterations",
                 'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             data=lines,
                                             x_label='Tau / [s]',
                                             y_label='Thermal Impedance / [K/W]',
                                             title='Deconvolved Thermal Impedance Error')

    def add_deconv_zth_output_plot(self):
        lines = [{'x_data': np.exp(self.z),
                  'y_data': self.zth_deconvolved,
                  'label': f"Reconstructed Zth {self.lr_iterations} Iterations",
                  'axis': 0},
                  {'x_data': np.exp(self.z),
                  'y_data': self.a_z,
                  'label': "Input Zth Curve",
                  'axis': 0}]

        return ud_plot.UttaPlotConfiguration(plot_type='line',
                                             x_scale='log',
                                             #y_scale='log',
                                             data=lines,
                                             x_label='Time / [s]',
                                             y_label='Thermal Impedance / [K/W]',
                                             title='Thermal Impedance')

def find_static_states(indata:list|np.ndarray, threshold: float=0.01, min_length: int=5):
    """ Detects static areas within a numpy-array where values stay within a certain threshold and have a minimum length.

    Args:
        indata (numpy.ndarray): Input data array
        threshold (float): Maximum absolute difference between values of the range.
        min_length (int): Minimum amount of consecutive values which must be within the threshold.

    Returns:
        list: a list of tuples which represent the start and end points of each area.
    """
    ranges = []

    end_idx =int(min_length)
    in_len = len(indata)

    while end_idx < in_len-min_length-1:
        start_idx = max(0, end_idx - min_length)
        comp_arr = indata[start_idx: end_idx]
        arr_pp = max(comp_arr) - min(comp_arr)
        
        if arr_pp <= threshold:
            ranges.append((start_idx, end_idx))
            # Advance by half the minimum steady state window width. This makes sure there is enough overlap to merge these windows later.
            end_idx += int(min_length/2)        
        else:
            end_idx +=1
    return ranges


def find_nearest(arr: np.ndarray, value: float):
    # Element in nd array `arr` closest to the scalar value `value`
    idx = np.abs(arr - value).argmin()
    return idx

def select_file(heading: str, file_filter: tuple):
    filename = fd.askopenfilename(
        title=heading,
        initialdir=os.path.realpath(__file__),
        filetypes=file_filter
    )
    return filename

def split_file_path(file_path: str):
    # get the filename including the file extension (should be the last value in the split tuple)
    data_file = os.path.basename(file_path).split('/')[-1]

    # get the file extension. Should be the last item when splitting the filename at the dots
    file_extension = data_file.split('.')[-1]

    data_file_no_ext = data_file.replace(f'.{file_extension}', '')
    file_path = os.path.dirname(file_path)

    # return the FileName with FileExtension, the bare filename and the directory to the file
    return data_file, data_file_no_ext, file_path

def write_tsp_cal_to_file(filename: str, tsp_cal):
    uTTA_data_import.write_tsp_cal_to_file(filename, tsp_cal)