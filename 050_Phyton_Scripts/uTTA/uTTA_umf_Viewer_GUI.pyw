import matplotlib # matplotlib 3.9.2
import ttkbootstrap as ttk  # ttkbootstrap 1.13.5
import library.uTTA_data_processing as udProc
import library.uTTA_data_plotting as udPlot

matplotlib.use("TkAgg")

DataFile = ''

class UmfViewerApp(ttk.Window):
    def __init__(self):
        super().__init__()
        # self.hdpi = False
        self.title("uTTA umf-Viewer")
        self.geometry("1480x960")
        self.minsize(1480, 960)
        screen_dpi = self.winfo_fpixels('1i')
        geometry = self.winfo_geometry()
        print("DPI: " + str(screen_dpi) + " Geometry: " + str(geometry))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        self.utta_data = udProc.UttaZthProcessing()

        # Measurement File Button Frame
        self.frm_file_btns = ttk.Frame(master=self, width=350, height=60, style="secondary.TFrame")
        self.frm_file_btns.place(x=10, y=10)

        self.btn_measure_file = ttk.Button(master=self.frm_file_btns, text="Measurement File",
                                           command=self.read_measurement_file_callback, bootstyle="dark")
        self.btn_measure_file.place(x=10, y=10)

        # Measurement Meta Data Frame
        self.frm_meas_data = ttk.Frame(master=self, width=350, height=860, style="secondary.TFrame")
        self.frm_meas_data.place(x=10, y=80)

        self.meas_meta_dummy = ttk.Frame(master=self.frm_meas_data, width=336, height=846, style="info.TFrame")
        self.meas_meta_dummy.place(x=7, y=7)
        self.meas_meta_data = ttk.Label(master=self.frm_meas_data, anchor="w", bootstyle="inverse-info", width=41, wraplength=330)
        self.meas_meta_data.configure(text="")
        self.meas_meta_data.place(x=10, y=10)

        # Helper Bar Frame
        self.frm_help_bar = ttk.Frame(master=self, width=1100, height=60, style='info.TFrame')
        self.frm_help_bar.place(x=370, y=10)

        self.lbl_helpbar = ttk.Label(master=self.frm_help_bar, anchor="w", bootstyle="inverse-info", wraplength=1080)
        self.lbl_helpbar.place(x=10, y=10)
        self.lbl_helpbar.configure(text="Welcome to the umf-Viewer GUI. Click 'Measurement File' and import a measurement")

        # Plot Area
        self.frm_plot_area = ttk.Frame(master=self)
        self.frm_plot_area.place(x=370, y=80)

        matplotlib.rcParams['axes.labelsize'] = 8
        matplotlib.rcParams['legend.fontsize'] = 7
        #matplotlib.rcParams['axes.grid'] = 'both'
        matplotlib.rcParams['font.size'] = 11
        matplotlib.rcParams['xtick.labelsize'] = 8
        matplotlib.rcParams['ytick.labelsize'] = 8

        self.view_plots = udPlot.UttaPlotData(self.frm_plot_area, (1090, 810), 3, 2)
        self._setup_plot_mapping()

        self.update_all_plots()
        self.update()


    def _setup_plot_mapping(self):
        # defines a flexible mapping of callback functions (which return data and plot configurations) to the subplots

        # (Axis-Index, Config Callback function)
        self.view_plots.plot_mapping = [
            (0, self.utta_data.add_input_tsp_measure_curve_plot),
            (1, self.utta_data.add_input_current_measure_curve_plot),
            (4, self.utta_data.add_cooling_curve_start_plot),
            (5, self.utta_data.add_thermocouple_plot)
        ]

        if not self.utta_data.meta_data.FlagTSPCalibrationFile:
            self.view_plots.plot_mapping += [ (2, self.utta_data.add_tsp_measure_cooling_curve_plot),
                                              (3, self.utta_data.add_current_measure_cooling_curve_plot)]

    def update_all_plots(self):

        if self.utta_data.flag_import_successful:
            # Updates all Plots based on their PlotConfiguration.
            self.view_plots.update_plots()

            MetaString = "File Name: " + DataFile + "\n"
            MetaString += "Measurement started: " + self.utta_data.meta_data.Measurement["StartDate"] + " " + self.utta_data.meta_data.Measurement["StartTime"] + "\n\n"

            if self.utta_data.meta_data.FlagTSPCalibrationFile:
                MetaString += "** TSP CALIBRATION MEASUREMENT **\n\n"
                MetaString += "Measurement Time:\t{preheat:.2f} min\n".format(preheat=self.utta_data.meta_data.TPreheat / 60)
            else:
                MetaString += "PreHeating Time:\t{preheat:.2f} min\n".format(preheat=self.utta_data.meta_data.TPreheat / 60)
                MetaString += "Heating Time:\t{heat:.2f} min\n".format(heat=self.utta_data.meta_data.THeating / 60)
                MetaString += "Cooling Time:\t{cool:.2f} min\n\n".format(cool=self.utta_data.meta_data.TCooling / 60)

            MetaString += "No. Name\tOffset\t\tGain\n"
            MetaString += "00:  {name:17s}{offs:.1f}mV\t{gain:.2f}mV/K\n".format(name=self.utta_data.meta_data.Channels["TSP0"]["Name"],
                                                                                 offs=self.utta_data.meta_data.Channels["TSP0"]["Offset"] * 1000,
                                                                                 gain=self.utta_data.meta_data.Channels["TSP0"]["LinGain"] * 1000)
            if not "OFF" in self.utta_data.meta_data.Channels["TSP1"]["Name"]:
                MetaString += "01:  {name:17s}{offs:.1f}mV\t{gain:.2f}mV/K\n".format(name=self.utta_data.meta_data.Channels["TSP1"]["Name"],
                                                                                     offs=self.utta_data.meta_data.Channels["TSP1"]["Offset"] * 1000,
                                                                                     gain=self.utta_data.meta_data.Channels["TSP1"]["LinGain"] * 1000)
            if not "OFF" in self.utta_data.meta_data.Channels["TSP2"]["Name"]:
                MetaString += "02:  {name:17s}{offs:.1f}mV\t{gain:.2f}mV/K\n".format(name=self.utta_data.meta_data.Channels["TSP2"]["Name"],
                                                                                     offs=self.utta_data.meta_data.Channels["TSP2"]["Offset"] * 1000,
                                                                                     gain=self.utta_data.meta_data.Channels["TSP2"]["LinGain"] * 1000)

            MetaString += "\nSense Current:\t{Isen:.2f} mA\n".format(Isen=self.utta_data.meta_data.Isense * 1000)
            if not self.utta_data.meta_data.FlagTSPCalibrationFile:
                MetaString += "Heating Current:\t{Iheat:.3f} A\n".format(Iheat=self.utta_data.i_heat)
                MetaString += "Heating Power:\t{Pheat:.3f} W\n".format(Pheat=self.utta_data.p_heat)

            self.meas_meta_data.configure(text=MetaString)

    def read_measurement_file_callback(self):
        global DataFile
        measfilename = udProc.select_file("Select the measurement file",
                                          (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        if len(measfilename) > 0:  # check if string is not empty
            DataFile, data_file_no_ext, file_path = udProc.split_file_path(measfilename)
            self.utta_data.import_data(measfilename)
            if self.utta_data.flag_import_successful:

                self.lbl_helpbar.configure(text="File: " + DataFile + " was successfully imported.", bootstyle="inverse-success")
                self.frm_help_bar.configure(bootstyle="success")

                if not self.utta_data.meta_data.FlagTSPCalibrationFile:
                    self.utta_data.calculate_cooling_curve()

                    self.utta_data.calculate_diode_heating()

                    self.utta_data.calculate_tsp_start_voltages()

                    self.utta_data.interpolate_zth_curve_start()

                self.update_all_plots()
        else:
            self.lbl_helpbar.configure(text="File: " + DataFile + " was not imported.", bootstyle="inverse-danger")
            self.frm_help_bar.configure(bootstyle="danger")

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.destroy()


app = UmfViewerApp()

app.mainloop()
