import ttkbootstrap as ttk  # ttkbootstrap 1.13.5
from ttkbootstrap.tooltip import ToolTip
import library.uTTA_data_plotting as ud_plot
import tkinter

BTN_HEIGHT = 40

class MeasurementPlotsWidget(ttk.Frame):
    def __init__(self, parent, data, figwidth, figheight, screen_dpi):
        super().__init__(parent)
        self.parent = parent
        self.data = data

        self.plots = ud_plot.UttaPlotData(self.parent, (figwidth, figheight), 3, 2, dpi=screen_dpi)
        self._setup_plot_mapping()


    def _setup_plot_mapping(self):

        self.plots.plot_mapping=[
            (0, self.data.add_input_tsp_measure_curve_plot),
            (1, self.data.add_input_current_measure_curve_plot),
            (2, self.data.add_tsp_measure_cooling_curve_plot),
            (3, self.data.add_diode_dt_curve_plot),
            (4, self.data.add_cooling_curve_start_plot),
            (5, self.data.add_thermocouple_plot)
        ]


class MeasurementInfoWidget(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.frm_timing = ttk.LabelFrame(self.parent, text="Measurement Timing")
        self.frm_timing.place(x=10, y=10, width=200, height=215)
        self.lbl_tpreheat = ttk.Label(master=self.frm_timing, anchor="w", text="Preheating").place(x=10, y=10)
        self.out_tpreheat = ttk.Label(master=self.frm_timing, anchor="w", text="")
        self.out_tpreheat.place(x=105, y=10)

        self.lbl_theating = ttk.Label(master=self.frm_timing, anchor="w", text="Heating").place(x=10, y=40)
        self.out_theating = ttk.Label(master=self.frm_timing, anchor="w", text="")
        self.out_theating.place(x=105, y=40)

        self.lbl_tcooling = ttk.Label(master=self.frm_timing, anchor="w", text="Cooling").place(x=10, y=70)
        self.out_tcooling = ttk.Label(master=self.frm_timing, anchor="w", text="")
        self.out_tcooling.place(x=105, y=70)

        self.lbl_dstart = ttk.Label(master=self.frm_timing, anchor="w", text="Start Date").place(x=10, y=130)
        self.out_dstart = ttk.Label(master=self.frm_timing, anchor="w", text="")
        self.out_dstart.place(x=105, y=130)

        self.lbl_tstart = ttk.Label(master=self.frm_timing, anchor="w", text="Start Time").place(x=10, y=160)
        self.out_tstart = ttk.Label(master=self.frm_timing, anchor="w", text="")
        self.out_tstart.place(x=105, y=160)

        self.frm_device = ttk.LabelFrame(self.parent, text="Device Information")
        self.frm_device.place(x=10, y=235, width=200, height=115)
        self.lbl_device = ttk.Label(master=self.frm_device, anchor="w", text="Device").place(x=10, y=10)
        self.out_device = ttk.Label(master=self.frm_device, anchor="w", text="")
        self.out_device.place(x=105, y=10)

        self.lbl_fileversion = ttk.Label(master=self.frm_device, anchor="w", text="File Version").place(x=10, y=40)
        self.out_fileversion = ttk.Label(master=self.frm_device, anchor="w", text="")
        self.out_fileversion.place(x=105, y=40)

        self.frm_ch0set = ttk.LabelFrame(self.parent, text="CH0 Settings")
        self.frm_ch0set.place(x=220, y=10, width=200, height=65)

        self.lbl_ch0offset = ttk.Label(master=self.frm_ch0set, anchor="w", text="Offset").place(x=10, y=10)
        self.out_ch0offset = ttk.Label(master=self.frm_ch0set, anchor="w", text="")
        self.out_ch0offset.place(x=80, y=10)

        self.frm_ch13set = ttk.LabelFrame(self.parent, text="CH1-3 Settings")
        self.frm_ch13set.place(x=220, y=85, width=200, height=65)

        self.lbl_ch13offset = ttk.Label(master=self.frm_ch13set, anchor="w", text="Offset").place(x=10, y=10)
        self.out_ch13offset = ttk.Label(master=self.frm_ch13set, anchor="w", text="")
        self.out_ch13offset.place(x=80, y=10)

        self.frm_sense = ttk.LabelFrame(self.parent, text="Sense Current")
        self.frm_sense.place(x=220, y=160, width=200, height=65)

        self.lbl_isense = ttk.Label(master=self.frm_sense, anchor="w", text="I_Sense").place(x=10, y=10)
        self.out_isense = ttk.Label(master=self.frm_sense, anchor="w", text="")
        self.out_isense.place(x=80, y=10)


    def update_widget(self, data):
        self.out_tpreheat.configure(text="{tpreh:,} s".format(tpreh=data.meta_data.TPreheat))
        self.out_theating.configure(text="{theat:,} s".format(theat=data.meta_data.THeating))
        self.out_tcooling.configure(text="{tcool:,} s".format(tcool=data.meta_data.TCooling))
        self.out_isense.configure(text="{val:,} mA".format(val=data.meta_data.Isense * 1000))
        self.out_ch0offset.configure(text="{val:.4} mV".format(val=data.meta_data.Voffs[0] * 1000))
        self.out_ch13offset.configure(text="{val:.4} mV".format(val=data.meta_data.Voffs[1] * 1000))
        self.out_dstart.configure(text=data.meta_data.Measurement["StartDate"])
        self.out_tstart.configure(text=data.meta_data.Measurement["StartTime"])

        if "FileVersion" in data.meta_data.Measurement:
            self.out_fileversion.configure(text=data.meta_data.Measurement["FileVersion"])
        else:
            self.out_fileversion.configure(text="unknown")

        if "DeviceVersion" in data.meta_data.Measurement:
            self.out_device.configure(text=data.meta_data.Measurement["DeviceVersion"])
        else:
            self.out_device.configure(text="unknown")

class ZthPlotsWidget(ttk.Frame):
    def __init__(self, parent, data, figwidth, figheight, screen_dpi):
        super().__init__(parent)
        self.parent = parent
        self.data = data

        self.plots = ud_plot.UttaPlotData(self.parent, (figwidth, figheight), 3, 1, dpi=screen_dpi)
        self._setup_plot_mapping()

    def _setup_plot_mapping(self):

        self.plots.plot_mapping=[
            (0, self.data.add_diode_dt_curve_plot),
            (1, self.data.add_zth_curve_plot),
            (2, self.data.add_zth_coupling_curve_plot),
        ]

class SettingsWidget(ttk.Frame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.parent = parent
        self.data = data

        self.frm_zero_curr = ttk.LabelFrame(self.parent, text="Zero Current Detection")
        self.frm_zero_curr.place(x=10, y=10, width=200, height=160)

        self.frm_zero_curr_method = ttk.LabelFrame(self.frm_zero_curr, text="Detection Method")
        self.frm_zero_curr_method.place(x=5, y=5, width=188, height=80)

        self.ctrl_zero_curr_method_set = tkinter.StringVar(self)
        self.ctrl_zero_curr_method_set.set(self.data.zero_current_detection_mode)

        self.ctrl_zero_curr_method_min = ttk.Radiobutton(master=self.frm_zero_curr_method,
                                                  text="Minimum Current", variable=self.ctrl_zero_curr_method_set,
                                                  value="Minimum")
        self.ctrl_zero_curr_method_min.place(x=10, y=10)
        self.ctrl_zero_curr_method_rat = ttk.Radiobutton(master=self.frm_zero_curr_method,
                                                   text="Current Ratio", variable=self.ctrl_zero_curr_method_set,
                                                   value="Ratio")
        self.ctrl_zero_curr_method_rat.place(x=10, y=35)

        ttk.Label(master=self.frm_zero_curr, text="Current Ratio", anchor="w").place(x=10, y=110, width=160)

        self.spinb_zero_curr_ratio = ttk.Spinbox(master=self.frm_zero_curr, width=40,
                                                 from_=0.0, to=1.00, increment=0.01, state="readonly")
        self.spinb_zero_curr_ratio.place(x=112, y=105, width=80)
        self.spinb_zero_curr_ratio.set(value=self.data.zero_current_detection_ratio)
        ToolTip(self.spinb_zero_curr_ratio, text="Defines the ratio of the current step\n"
                                                 "(heating current - no current) where the\n"
                                                 "postprocessing algorithm considers the\n"
                                                 "heating current as switched off.\n"
                                                 "e.g. 0.3 = 30% of the heating current.")

        self.frm_material_const = ttk.LabelFrame(self.parent, text="Semiconductor Parameters")
        self.frm_material_const.place(x=220, y=10, width=200, height=160)

        ttk.Label(self.frm_material_const, text='C_th').place(x=10, y=15)
        ttk.Label(self.frm_material_const, text='J/(kg\u2219K)').place(x=135, y=15)
        ttk.Label(self.frm_material_const, text=u'\u03C1').place(x=10, y=55)
        ttk.Label(self.frm_material_const, text='kg/\u33A5').place(x=135, y=55)
        ttk.Label(self.frm_material_const, text=u'\u03BA').place(x=10, y=95)
        ttk.Label(self.frm_material_const, text=u'W/(m\u2219K)').place(x=135, y=95)

        self.spinb_material_cth = ttk.Spinbox(master=self.frm_material_const,width=70,
                                              from_=0.0, to=10000.00, increment=0.01, state="readonly")
        self.spinb_material_cth.place(x=45, y=10, width=85)
        self.spinb_material_cth.set(value=self.data.Cth_Si)
        ToolTip(self.spinb_material_cth, text="Thermal specific heat capacitance\n"
                                              "of the semiconductor in the active area.")

        self.spinb_material_rho = ttk.Spinbox(master=self.frm_material_const,width=70,
                                              from_=0.0, to=10000.00, increment=0.01, state="readonly")
        self.spinb_material_rho.place(x=45, y=50, width=85)
        self.spinb_material_rho.set(value=self.data.rho_Si)
        ToolTip(self.spinb_material_rho, text="Specific density of the semiconductor")

        self.spinb_material_kappa = ttk.Spinbox(master=self.frm_material_const,width=70,
                                              from_=0.0, to=10000.00, increment=0.01, state="readonly")
        self.spinb_material_kappa.place(x=45, y=90, width=85)
        self.spinb_material_kappa.set(value=self.data.kappa_SI)
        ToolTip(self.spinb_material_kappa, text="Specific heat transmissivity"
                                                " of the semiconductor")

        self.frm_zth_export = ttk.LabelFrame(self.parent, text="Zth Export Settings")
        self.frm_zth_export.place(x=640, y=10, width=200, height=80)

        ttk.Label(master=self.frm_zth_export, text="Samples/Decade", anchor="w").place(x=10, y=10, width=160)

        self.spinb_zth_export_samp_dec = ttk.Spinbox(master=self.frm_zth_export, width=40,
                                                     from_=1, to=50, increment=1, state="readonly")
        self.spinb_zth_export_samp_dec.place(x=132, y=5, width=60)
        self.spinb_zth_export_samp_dec.set(value=self.data.export_zth_samples_decade)

        self.frm_tdim_export = ttk.LabelFrame(self.parent, text="TDIM Export Settings")
        self.frm_tdim_export.place(x=640, y=100, width=200, height=80)

        self.btn_apply_settings = ttk.Button(master=self.parent,
                                               text="Apply Settings", command=self.apply_settings,
                                               style="dark")
        self.btn_apply_settings.place(x=1050, y=750 + BTN_HEIGHT, height=BTN_HEIGHT, width=180)

    def apply_settings(self):
        print("\033[94mSettings changed\033[0m")

        self.data.zero_current_detection_mode = self.ctrl_zero_curr_method_set.get()
        self.data.zero_current_detection_ratio = float(self.spinb_zero_curr_ratio.get())
        self.data.export_zth_samples_decade = int(self.spinb_zth_export_samp_dec.get())

        self.data.Cth_Si = float(self.spinb_material_cth.get())
        self.data.rho_Si = float(self.spinb_material_rho.get())
        self.data.kappa_SI = float(self.spinb_material_kappa.get())
