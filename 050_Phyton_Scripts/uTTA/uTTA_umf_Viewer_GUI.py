from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # matplotlib 3.9.2
from matplotlib.figure import Figure
import matplotlib # matplotlib 3.9.2
import ttkbootstrap as ttk  # ttkbootstrap 1.13.5
import uTTA_data_processing as udpc

matplotlib.use("TkAgg")

CalData_FileName = ''

DataFile = ''
G_Plots = []
FileOpened = False

class umf_viewer_App(ttk.Window):
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

        # widgets
        global G_Plots

        self.utta_data = udpc.UttaZthProcessing()

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

        self.fig = Figure(figsize=(1090/screen_dpi, 810/screen_dpi), dpi=96)
        # self.fig = Figure(figsize=(11.1, 7.5), dpi=96)
        self.fig.subplots_adjust(left=0.06, bottom=0.075, right=0.97, top=0.96, wspace=0.212, hspace=0.54)
        G_Plots = self.fig.subplots(3, 2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1, rowspan=18, columnspan=5, padx=10, pady=10, sticky="ew")

        # Toolbar Frame
        toolbar_frame = ttk.Frame(master=self)
        toolbar_frame.place(x=370, y=900)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        self.update_plots()
        self.update()

    def update_plots(self):

        global G_Plots, Temp, MetaData, FileOpened
        if FileOpened:
            G_Plots[0, 0].clear()
            G_Plots[1, 0].clear()
            G_Plots[2, 0].clear()
            G_Plots[0, 1].clear()
            G_Plots[1, 1].clear()
            G_Plots[2, 1].clear()

            self.utta_data.add_input_tsp_measure_curve_plot(G_Plots[0, 0])

            self.utta_data.add_input_current_measure_curve_plot(G_Plots[0, 1])

            if not self.utta_data.meta_data["TSP_Calibration_File"]:
                self.utta_data.calculate_cooling_curve()

                self.utta_data.calculate_diode_heating()

                self.utta_data.calculate_tsp_start_voltages()

                self.utta_data.interpolate_zth_curve_start()

                self.utta_data.add_tsp_measure_cooling_curve_plot(G_Plots[1, 0])

                self.utta_data.add_current_measure_cooling_curve_plot(G_Plots[1, 1])

            self.utta_data.add_thermocouple_plot(G_Plots[2, 1])

            MetaString = "File Name: " + DataFile + "\n"
            MetaString += "Measurement started: " + self.utta_data.meta_data["StartDate"] + " " + self.utta_data.meta_data["StartTime"] + "\n\n"

            if self.utta_data.meta_data["TSP_Calibration_File"]:
                MetaString += "** TSP CALIBRATION MEASUREMENT **\n\n"
                MetaString += "Measurement Time:\t{preheat:.2f} min\n".format(preheat=self.utta_data.meta_data["T_Preheat"] / 60)
            else:
                MetaString += "PreHeating Time:\t{preheat:.2f} min\n".format(preheat=self.utta_data.meta_data["T_Preheat"] / 60)
                MetaString += "Heating Time:\t{heat:.2f} min\n".format(heat=self.utta_data.meta_data["T_Heat"] / 60)
                MetaString += "Cooling Time:\t{cool:.2f} min\n\n".format(cool=self.utta_data.meta_data["T_Cool"] / 60)

            MetaString += "No. Name\tOffset\t\tGain\n"
            MetaString += "00:  {name}\t{offs:.1f}mV\t\t{gain:.2f}mV/K\n".format(name=self.utta_data.meta_data["TSP0"]["Name"],
                                                                                 offs=self.utta_data.meta_data["TSP0"]["Offset"] * 1000,
                                                                                 gain=self.utta_data.meta_data["TSP0"]["LinGain"] * 1000)
            if not "OFF" in self.utta_data.meta_data["TSP1"]["Name"]:
                MetaString += "01:  {name}\t{offs:.1f}mV\t\t{gain:.2f}mV/K\n".format(name=self.utta_data.meta_data["TSP1"]["Name"],
                                                                                     offs=self.utta_data.meta_data["TSP1"]["Offset"] * 1000,
                                                                                     gain=self.utta_data.meta_data["TSP1"]["LinGain"] * 1000)
            if not "OFF" in self.utta_data.meta_data["TSP2"]["Name"]:
                MetaString += "02:  {name}\t{offs:.1f}mV\t\t{gain:.2f}mV/K\n".format(name=self.utta_data.meta_data["TSP2"]["Name"],
                                                                                     offs=self.utta_data.meta_data["TSP2"]["Offset"] * 1000,
                                                                                     gain=self.utta_data.meta_data["TSP2"]["LinGain"] * 1000)

            MetaString += "\nSense Current:\t{Isen:.2f} mA\n".format(Isen=self.utta_data.meta_data["ISEN"] * 1000)
            if not self.utta_data.meta_data["TSP_Calibration_File"]:
                MetaString += "Heating Current:\t{Iheat:.3f} A\n".format(Iheat=self.utta_data.meta_data["I_Heat"])
                MetaString += "Heating Power:\t{Pheat:.3f} W\n".format(Pheat=self.utta_data.meta_data["P_Heat"])

            self.meas_meta_data.configure(text=MetaString)
            self.canvas.draw()

    def read_measurement_file_callback(self):
        global DataFile, FileOpened
        measfilename = udpc.select_file("Select the measurement file",
                                                    (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        if len(measfilename) > 0:  # check if string is not empty
            DataFile, data_file_no_ext, file_path = udpc.split_file_path(measfilename)

            FileOpened = self.utta_data.import_data(measfilename)
            self.update_plots()

            self.lbl_helpbar.configure(text="File: " + DataFile + " was successfully imported.", bootstyle="inverse-success")
            self.frm_help_bar.configure(bootstyle="success")

        else:
            self.lbl_helpbar.configure(text="File: " + DataFile + " was not imported.", bootstyle="inverse-danger")
            self.frm_help_bar.configure(bootstyle="danger")

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.destroy()


app = umf_viewer_App()

app.mainloop()
