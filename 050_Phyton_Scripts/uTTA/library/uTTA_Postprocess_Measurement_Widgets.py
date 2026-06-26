import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip
import library.uTTA_data_plotting as ud_plot
import library.uTTA_data_processing as udProc
import tkinter as tk
import tkinter
import logging


class MeasurementPlotsWidget(ttk.Frame):
    def __init__(self, parent:ttk.Frame, data:udProc.UttaZthProcessing, figwidth:int, figheight:int, screen_dpi:float):
        super().__init__(parent)
        self.parent = parent
        self.data = data

        self.plots = ud_plot.UttaPlotData(self.parent, (figwidth, figheight), 3, 2, dpi=screen_dpi)
        self._setup_plot_mapping()

    def _setup_plot_mapping(self):

        self.plots.add_plot_mapping(row=0, col=0, config_func=self.data.add_input_tsp_measure_curve_plot)
        self.plots.add_plot_mapping(row=0, col=1, config_func=self.data.add_input_current_measure_curve_plot)
        self.plots.add_plot_mapping(row=1, col=0, config_func=self.data.add_tsp_measure_cooling_curve_plot)
        self.plots.add_plot_mapping(row=1, col=1, config_func=self.data.add_diode_dt_curve_plot)
        self.plots.add_plot_mapping(row=2, col=0, config_func=self.data.add_cooling_curve_start_plot)
        self.plots.add_plot_mapping(row=2, col=1, config_func=self.data.add_thermocouple_plot)


class MeasurementInfoWidget(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.parent.grid_columnconfigure([0,1,2,3], minsize=250)

        self.frm_timing = ttk.Labelframe(self.parent, text="Measurement Timing")
        self.frm_timing.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky='nwe')
        ttk.Label(master=self.frm_timing, text="Preheating").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.out_tpreheat = ttk.Label(master=self.frm_timing, text="")
        self.out_tpreheat.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        ttk.Label(master=self.frm_timing, text="Heating").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.out_theating = ttk.Label(master=self.frm_timing, text="")
        self.out_theating.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        ttk.Label(master=self.frm_timing, text="Cooling").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.out_tcooling = ttk.Label(master=self.frm_timing, text="")
        self.out_tcooling.grid(row=2, column=1, padx=10, pady=10, sticky='w')

        ttk.Label(master=self.frm_timing, text="Start Date").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.out_dstart = ttk.Label(master=self.frm_timing, text="")
        self.out_dstart.grid(row=3, column=1, padx=10, pady=10, sticky='w')

        ttk.Label(master=self.frm_timing, text="Start Time").grid(row=4, column=0, padx=10, pady=10, sticky='w')
        self.out_tstart = ttk.Label(master=self.frm_timing, text="")
        self.out_tstart.grid(row=4, column=1, padx=10, pady=10, sticky='w')

        # Info section about the measurement file and its file version
        self.frm_device = ttk.Labelframe(self.parent, text="Device Information")
        self.frm_device.grid(row=4, column=0, padx=10, pady=10, sticky='nwe')
        ttk.Label(master=self.frm_device, text="Device").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.out_device = ttk.Label(master=self.frm_device, text="")
        self.out_device.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        ttk.Label(master=self.frm_device, text="File Version").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.out_fileversion = ttk.Label(master=self.frm_device, text="")
        self.out_fileversion.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        # Info section for Offset Values of Channel 0
        self.frm_ch0set = ttk.Labelframe(self.parent, text="CH0 Settings")
        self.frm_ch0set.grid(row=0, column=1, padx=10, pady=10, sticky='nwe')

        ttk.Label(master=self.frm_ch0set, text="Offset").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.out_ch0offset = ttk.Label(master=self.frm_ch0set, text="")
        self.out_ch0offset.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        # Info section for Offset Values of Channel 1-3
        self.frm_ch13set = ttk.Labelframe(self.parent, text="CH1-3 Settings")
        self.frm_ch13set.grid(row=1, column=1, padx=10, pady=10, sticky='nwe')

        ttk.Label(master=self.frm_ch13set, text="Offset").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.out_ch13offset = ttk.Label(master=self.frm_ch13set, text="")
        self.out_ch13offset.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        # Info section for sense current
        self.frm_sense = ttk.Labelframe(self.parent, text="Sense Current")
        self.frm_sense.grid(row=2, column=1, padx=10, pady=10, sticky='nwe')

        ttk.Label(master=self.frm_sense, text="I_Sense").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.out_isense = ttk.Label(master=self.frm_sense, text="")
        self.out_isense.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        ####################################################################
        #### Info Sections with calibration values of each junction ########
        ####################################################################

        self.frm_dut_calibration = ttk.Labelframe(self.parent, text="DUT Calibration Values")
        self.frm_dut_calibration.grid(row=0, column=2, rowspan=4, columnspan=3, padx=10, pady=10, sticky='nwe')

        self.out_ch_cal_name = [None] * 3
        self.out_ch_cal_offs = [None] * 3
        self.out_ch_cal_lin = [None] * 3
        self.out_ch_cal_quad = [None] * 3

        for idx in range(0,3):      # TODO: Add scalability to this

            self.frm_dut_cal_ch = ttk.Labelframe(self.frm_dut_calibration, text=f"Channel CH{idx}")
            self.frm_dut_cal_ch.grid(row=0, column=idx, padx=5, pady=5, sticky='nswe')

            ttk.Label(master=self.frm_dut_cal_ch, text="Name").grid(row=0, column=0, padx=10, pady=10, sticky='w')
            self.out_ch_cal_name[idx] = ttk.Label(master=self.frm_dut_cal_ch, text="") # type: ignore
            self.out_ch_cal_name[idx].grid(row=0, column=1, padx=10, pady=10, sticky='w') # type: ignore

            ttk.Label(master=self.frm_dut_cal_ch, text="Offset").grid(row=1, column=0, padx=10, pady=10, sticky='w')
            self.out_ch_cal_offs[idx] = ttk.Label(master=self.frm_dut_cal_ch, text="") # type: ignore
            self.out_ch_cal_offs[idx].grid(row=1, column=1, padx=10, pady=10, sticky='w') # type: ignore

            ttk.Label(master=self.frm_dut_cal_ch, text="Lin. Gain").grid(row=2, column=0, padx=10, pady=10, sticky='w')
            self.out_ch_cal_lin[idx] = ttk.Label(master=self.frm_dut_cal_ch, text="") # type: ignore
            self.out_ch_cal_lin[idx].grid(row=2, column=1, padx=10, pady=10, sticky='w') # type: ignore

            ttk.Label(master=self.frm_dut_cal_ch, text="Quad. Gain").grid(row=3, column=0, padx=10, pady=10, sticky='w')
            self.out_ch_cal_quad[idx] = ttk.Label(master=self.frm_dut_cal_ch, text="") # type: ignore
            self.out_ch_cal_quad[idx].grid(row=3, column=1, padx=10, pady=10, sticky='w') # type: ignore


        ####################################################################
        #### Info Sections with values calculated from the measurements ####
        ####################################################################
        self.frm_heating_info = ttk.Labelframe(self.parent, text="Heating Values")
        self.frm_heating_info.grid(row=4, column=1, rowspan=3, padx=10, pady=10, sticky='nwe')
        ttk.Label(master=self.frm_heating_info, text="Current").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.out_i_heat = ttk.Label(master=self.frm_heating_info, text='')
        self.out_i_heat.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        ttk.Label(master=self.frm_heating_info, text="Voltage").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.out_u_heat = ttk.Label(master=self.frm_heating_info, text='')
        self.out_u_heat.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        ttk.Label(master=self.frm_heating_info, text="Power").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.out_p_heat = ttk.Label(master=self.frm_heating_info, text='')
        self.out_p_heat.grid(row=2, column=1, padx=10, pady=10, sticky='w')

    def update_widget(self, data):
        self.out_tpreheat.configure(text=f"{data.meta_data.TPreheat:,} s")
        self.out_theating.configure(text=f"{data.meta_data.THeating:,} s")
        self.out_tcooling.configure(text=f"{data.meta_data.TCooling:,} s")
        self.out_isense.configure(text=f"{data.meta_data.Isense * 1000:,} mA")
        self.out_ch0offset.configure(text=f"{data.meta_data.Voffs[0] * 1000:.4} mV")
        self.out_ch13offset.configure(text=f"{data.meta_data.Voffs[1] * 1000:.4} mV")
        self.out_dstart.configure(text=data.meta_data.Measurement["StartDate"])
        self.out_tstart.configure(text=data.meta_data.Measurement["StartTime"])

        self.out_fileversion.configure(text=data.meta_data.Measurement.get("FileVersion", "unknown"))
        self.out_device.configure(text=data.meta_data.Measurement.get("DeviceVersion", "unknown"))

        for idx in range(0,3):
            ch = f"TSP{idx}"
            self.out_ch_cal_name[idx].configure(text=data.meta_data.Channels[ch]['Name']) # type: ignore
            self.out_ch_cal_offs[idx].configure(text=f'{data.meta_data.Channels[ch]['Offset']:.5} V') # type: ignore
            self.out_ch_cal_lin[idx].configure(text=f'{data.meta_data.Channels[ch]['LinGain']:.5} V/K') # type: ignore
            self.out_ch_cal_quad[idx].configure(text=f'{data.meta_data.Channels[ch]['QuadGain']:.5} V/K²') # type: ignore

        self.out_i_heat.configure(text=f"{data.i_heat:.4} A")
        self.out_u_heat.configure(text=f"{data.u_heat:.4} V")
        self.out_p_heat.configure(text=f"{data.p_heat:.4} W")

class ZthPlotsWidget(ttk.Frame):
    def __init__(self, parent, data, figwidth:int, figheight:int, screen_dpi:float):
        super().__init__(parent)
        self.parent = parent
        self.data = data

        self.plots = ud_plot.UttaPlotData(self.parent, (figwidth, figheight), 2, 1, dpi=screen_dpi)
        self._setup_plot_mapping()

    def _setup_plot_mapping(self):

        self.plots.add_plot_mapping(row=0, col=0, config_func=self.data.add_zth_curve_plot)
        self.plots.add_plot_mapping(row=1, col=0, config_func=self.data.add_zth_coupling_curve_plot)


class SettingsWidget(ttk.Frame):
    def __init__(self, parent_frm:ttk.Frame, parent_app, data, logger:logging.Logger|None):
        super().__init__(parent_frm)

        if logger is None:
            self.logger = logging.getLogger("dummy")
            self.logger.addHandler(logging.NullHandler())
            self.logger.propagate = False # Important: prevents forwarding to the root logger
        else:
            self.logger = logger
        
        self._parent = parent_frm
        self._parent_app = parent_app
        self._data = data
        self._parent.grid_columnconfigure([0,1,2,3], minsize=250)


        # Zero Current Detection
        self.frm_zero_curr = ttk.Labelframe(self._parent, text="Zero Current Detection")
        self.frm_zero_curr.grid(row=0, column=0, padx=10, pady=10, sticky='nwe')

        self.frm_zero_curr_method = ttk.Labelframe(self.frm_zero_curr, text="Detection Method")
        self.frm_zero_curr_method.grid(row=0, column=0, columnspan=2 ,padx=10, pady=10, sticky='nwe')

        self.ctrl_zero_curr_method_set = tkinter.StringVar(self)
        self.ctrl_zero_curr_method_set.set(self._data.zero_current_detection_mode)

        self.ctrl_zero_curr_method_min = ttk.Radiobutton(master=self.frm_zero_curr_method,
                                                  text="Minimum Current", variable=self.ctrl_zero_curr_method_set,
                                                  value="Minimum")
        self.ctrl_zero_curr_method_min.grid(row=0, column=0, padx=10, pady=10, sticky='nwe')
        self.ctrl_zero_curr_method_rat = ttk.Radiobutton(master=self.frm_zero_curr_method,
                                                   text="Current Ratio", variable=self.ctrl_zero_curr_method_set,
                                                   value="Ratio")
        self.ctrl_zero_curr_method_rat.grid(row=1, column=0, padx=10, pady=10, sticky='nwe')

        ttk.Label(master=self.frm_zero_curr, text="Current Ratio", anchor="w").grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.spinb_zero_curr_ratio = ttk.Spinbox(master=self.frm_zero_curr, width=5,
                                                 from_=0.0, to=1.00, increment=0.01, state="readonly")
        self.spinb_zero_curr_ratio.grid(row=1, column=1, padx=10, pady=10, sticky='e')
        self.spinb_zero_curr_ratio.set(value=self._data.zero_current_detection_ratio)
        ToolTip(self.spinb_zero_curr_ratio, text="Defines the ratio of the current step\n"
                                                 "(heating current - no current) where the\n"
                                                 "postprocessing algorithm considers the\n"
                                                 "heating current as switched off.\n"
                                                 "e.g. 0.3 = 30% of the heating current.")

        # Semiconductor Parameters
        self.frm_material_const = ttk.Labelframe(self._parent, text="Semiconductor Parameters")
        self.frm_material_const.grid(row=0, column=1, padx=10, pady=10, sticky='nwe')

        ttk.Label(self.frm_material_const, text='C_th').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        ttk.Label(self.frm_material_const, text='J/(kg\u2219K)').grid(row=0, column=2, padx=1, pady=10, sticky='w')
        ttk.Label(self.frm_material_const, text=u'\u03C1').grid(row=1, column=0, padx=10, pady=10, sticky='w')
        ttk.Label(self.frm_material_const, text='kg/\u33A5').grid(row=1, column=2, padx=1, pady=10, sticky='w')
        ttk.Label(self.frm_material_const, text=u'\u03BA').grid(row=2, column=0, padx=10, pady=10, sticky='w')
        ttk.Label(self.frm_material_const, text=u'W/(m\u2219K)').grid(row=2, column=2, padx=1, pady=10, sticky='w')

        self.spinb_material_cth = ttk.Spinbox(master=self.frm_material_const,width=8,
                                              from_=0.0, to=10000.00, increment=0.01, state="readonly")
        self.spinb_material_cth.grid(row=0, column=1, padx=1, pady=10, sticky='w')
        self.spinb_material_cth.set(value=self._data.Cth_Si)
        ToolTip(self.spinb_material_cth, text="Thermal specific heat capacitance\n"
                                              "of the semiconductor in the active area.")

        self.spinb_material_rho = ttk.Spinbox(master=self.frm_material_const,width=8,
                                              from_=0.0, to=10000.00, increment=0.01, state="readonly")
        self.spinb_material_rho.grid(row=1, column=1, padx=1, pady=10, sticky='w')
        self.spinb_material_rho.set(value=self._data.rho_Si)
        ToolTip(self.spinb_material_rho, text="Specific density of the semiconductor")

        self.spinb_material_kappa = ttk.Spinbox(master=self.frm_material_const,width=8,
                                              from_=0.0, to=10000.00, increment=0.01, state="readonly")
        self.spinb_material_kappa.grid(row=2, column=1, padx=1, pady=10, sticky='w')
        self.spinb_material_kappa.set(value=self._data.kappa_SI)
        ToolTip(self.spinb_material_kappa, text="Specific heat transmissivity"
                                                " of the semiconductor")

        # Zth Eport Settings
        self.frm_zth_export = ttk.Labelframe(self._parent, text="Zth Export Settings")
        self.frm_zth_export.grid(row=0, column=2, padx=10, pady=10, sticky='nwe')

        ttk.Label(master=self.frm_zth_export, text="Samples/Decade", anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.spinb_zth_export_samp_dec = ttk.Spinbox(master=self.frm_zth_export, width=5,
                                                     from_=1, to=100, increment=1, state="readonly")
        self.spinb_zth_export_samp_dec.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        self.spinb_zth_export_samp_dec.set(value=self._data.export_zth_samples_decade)

        # TDIM Export Settings
        self.frm_tdim_export = ttk.Labelframe(self._parent, text="TDIM Export Settings")
        self.frm_tdim_export.grid(row=0, column=3, padx=10, pady=10, sticky='nwe')

        ttk.Label(master=self.frm_tdim_export, text="Max. Points", anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.spinb_max_points = ttk.Spinbox(master=self.frm_tdim_export, width = 7,
                                            from_=10000, to=1000000, increment=1)
        self.spinb_max_points.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        self.spinb_max_points.set(value=self._data.export_tdim_max_points)
        ToolTip(self.spinb_max_points, text="The maximum number of samples the\n"
                                            "TDIM-Export file shall contain.")

        ttk.Label(master=self.frm_tdim_export, text="Reduce above", anchor="w").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        ttk.Label(master=self.frm_tdim_export, text="s", anchor="w").grid(row=1, column=2, padx=1, pady=10, sticky='w')
        self.spinb_reduce = ttk.Spinbox(master=self.frm_tdim_export, width=7,
                                        from_=10.0, to=1000.0, increment=1)
        self.spinb_reduce.set(value=self._data.export_tdim_reduce_time)
        self.spinb_reduce.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        # Deconvolution Settings
        self.frm_deconv_settings = ttk.Labelframe(self._parent, text="Deconvolution Settings")
        self.frm_deconv_settings.grid(row=5, column=0, rowspan=4, columnspan=3, padx=5, pady=5, sticky='nwe')

        self.frm_deconv_method = ttk.Labelframe(self.frm_deconv_settings, text='Method')
        self.frm_deconv_method.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky='nwe')

        self.deconv_method_set = tkinter.StringVar(self)
        self.deconv_method_set.set(self._data.deconv_method)

        self.ctrl_deconv_method_bayes = ttk.Radiobutton(master=self.frm_deconv_method,
                                                  text="Bayes Iteration", variable=self.deconv_method_set,
                                                  value="Bayes")
        self.ctrl_deconv_method_bayes.grid(row=0, column=0, padx=5, pady=5, sticky='nwe')
        self.ctrl_deconv_method_fft = ttk.Radiobutton(master=self.frm_deconv_method,
                                                   text="FFT", variable=self.deconv_method_set,
                                                   value="FFT")
        self.ctrl_deconv_method_fft.grid(row=1, column=0, padx=5, pady=5, sticky='nwe')

        self.frm_deconv_bayes_settings = ttk.Labelframe(self.frm_deconv_settings, text="Bayes Iteration")
        self.frm_deconv_bayes_settings.grid(row=0, column=1, rowspan=4, padx=5, pady=5, sticky='nwe')

        ttk.Label(master=self.frm_deconv_bayes_settings, text="Points/Decade", anchor='w').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.spinb_bayes_sampdecade = ttk.Spinbox(master=self.frm_deconv_bayes_settings, width=7,
                                        from_=10.0, to=1000.0, increment=1)
        self.spinb_bayes_sampdecade.set(value=self._data.deconv_samples_per_decade)
        self.spinb_bayes_sampdecade.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(master=self.frm_deconv_bayes_settings, text="Iterations", anchor='w').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.spinb_bayes_iterations = ttk.Spinbox(master=self.frm_deconv_bayes_settings, width=7,
                                        from_=10.0, to=5000.0, increment=1)
        self.spinb_bayes_iterations.set(value=self._data.lr_iterations)
        self.spinb_bayes_iterations.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(master=self.frm_deconv_bayes_settings, text="Peak Sharpening Factor", anchor='w').grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.spinb_bayes_sharpening = ttk.Spinbox(master=self.frm_deconv_bayes_settings, width=7,
                                        from_=0.0, to=5.0, increment=0.01)
        self.spinb_bayes_sharpening.set(value=self._data.lr_sharpening)
        self.spinb_bayes_sharpening.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # APPLY SETTINGS Button
        self.btn_apply_settings = ttk.Button(master=self._parent,
                                               text="Apply Settings", command=self.apply_settings,
                                               style="dark")
        self.btn_apply_settings.grid(row=5, column=4, padx=10, pady=10, sticky='se')

    def apply_settings(self):
        self.logger.info("GUI Settings changed")

        self._data.zero_current_detection_mode = self.ctrl_zero_curr_method_set.get()
        self._data.zero_current_detection_ratio = float(self.spinb_zero_curr_ratio.get())
        self._data.export_zth_samples_decade = int(self.spinb_zth_export_samp_dec.get())

        self._data.Cth_Si = float(self.spinb_material_cth.get())
        self._data.rho_Si = float(self.spinb_material_rho.get())
        self._data.kappa_SI = float(self.spinb_material_kappa.get())

        self._data.export_tdim_max_points = int(self.spinb_max_points.get())
        self._data.export_tdim_reduce_time = float(self.spinb_reduce.get())


        self._data.deconv_method = self.deconv_method_set.get()

        self._data.deconv_samples_per_decade = int(self.spinb_bayes_sampdecade.get())
        self._data.lr_iterations = int(self.spinb_bayes_iterations.get())
        self._data.lr_sharpening = float(self.spinb_bayes_sharpening.get())

        self._parent_app.update_calculations()

class DeconvPlotsWidget(ttk.Frame):
    def __init__(self, parent, data, figwidth:int, figheight:int, screen_dpi:float):
        super().__init__(parent)
        self.parent = parent
        self.data = data

        self.plots = ud_plot.UttaPlotData(self.parent, (figwidth, figheight), 3, 1, dpi=screen_dpi)
        self._setup_plot_mapping()

    def _setup_plot_mapping(self):

        self.plots.add_plot_mapping(row=0, col=0, config_func=self.data.add_deconv_zth_output_plot)
        self.plots.add_plot_mapping(row=1, col=0, config_func=self.data.add_deconv_tau_output_plot)
        self.plots.add_plot_mapping(row=2, col=0, config_func=self.data.add_zth_deconvolution_error_plot)


