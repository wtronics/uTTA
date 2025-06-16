from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # matplotlib 3.9.2
from matplotlib.figure import Figure
import uTTA_data_import
import uTTA_data_processing
import numpy as np  # numpy 2.1.1
import numpy.dtypes  # numpy 2.1.0
import matplotlib  # matplotlib 3.9.2
import ttkbootstrap as ttk  # ttkbootstrap 1.13.5

matplotlib.use("TkAgg")

CalData_FileName = ''
TimeBaseTotal = []
ADC = []
Temp = []

DataFile = ''
G_Plots = []
FileOpened = False
MaxJUT_Channels = 3
NoOfDUTs = 3
MetaData = {}


class umf_viewer_App(ttk.Window):
    def __init__(self):
        super().__init__()
        # self.hdpi = False
        self.title("uTTA umf-Viewer")
        self.geometry("1480x900")
        self.minsize(1480, 900)
        screen_dpi = self.winfo_fpixels('1i')
        geometry = self.winfo_geometry()
        print("DPI: " + str(screen_dpi) + " Geometry: " + str(geometry))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        # widgets
        global G_Plots

        # Measurement File Button Frame
        self.frm_file_btns = ttk.Frame(master=self, width=350, height=60, style="secondary.TFrame")
        self.frm_file_btns.place(x=10, y=10)

        self.btn_measure_file = ttk.Button(master=self.frm_file_btns, text="Measurement File",
                                           command=self.read_measurement_file_callback, bootstyle="dark")
        self.btn_measure_file.place(x=10, y=10)

        # Measurement Meta Data Frame
        self.frm_meas_data = ttk.Frame(master=self, width=350, height=810, style="secondary.TFrame")
        self.frm_meas_data.place(x=10, y=80)

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

        self.fig = Figure(figsize=(11.1, 7.9), dpi=78)
        self.fig.subplots_adjust(left=0.06, bottom=0.075, right=0.97, top=0.96, wspace=0.212, hspace=0.54)
        G_Plots = self.fig.subplots(3, 2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1, rowspan=18, columnspan=5, padx=10, pady=10, sticky="ew")

        # Toolbar Frame
        toolbar_frame = ttk.Frame(master=self)
        toolbar_frame.place(x=370, y=850)
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

            # Calculate the average ambient temperature as starting point
            StartTempTC = np.mean(Temp[0, 0:10])
            print("Averaged start temperature form TC-Channel 3: {Tstart:.3f}°C".format(Tstart=StartTempTC))

            CoolingStartBlock = MetaData["CoolingStartBlock"]
            SampDecade = MetaData["SamplesPerDecade"]

            # Cut Timebase and measurement to cooling section
            TimeBase_Cooling, ADC_Cooling, MetaData = uTTA_data_processing.calculate_cooling_curve(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade, MetaData)

            # # Calculate the average heating current, voltage and power through the diode
            PDio_Heat, I_Heat = uTTA_data_processing.calculate_diode_heating(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade)

            UDio_Cold_Start = np.zeros((NoOfDUTs,), numpy.float32)
            UDio_Cold_End = np.zeros((NoOfDUTs,), numpy.float32)
            T_Monitor_Heated = np.zeros((NoOfDUTs,), numpy.float32)
            TDio = np.zeros(shape=ADC_Cooling.shape)
            for Ch in range(0, NoOfDUTs):
                ch_tsp = "TSP{Ch}".format(Ch=Ch)
                if MetaData[ch_tsp]["Name"] != "OFF":
                    # Calculate the average Diode voltage at the start of the measurement
                    # print ("Channel {Chan}, Min ADC: {MinADC}, Max ADC: {MaxADC}".format(Chan=Ch,MinADC=ADC[Ch, :].min(), MaxADC=ADC[Ch, :].max()))
                    UDio_Cold_Start[Ch] = np.mean(ADC[Ch, 0:SampDecade])
                    # Calculate the average Diode voltage at the end of the measurement
                    UDio_Cold_End[Ch] = np.mean(ADC[Ch, -SampDecade:-1])
                    # The TSP Offset is the average diode start voltage
                    MetaData[ch_tsp]["Offset"] = -UDio_Cold_Start[Ch]
                    TDio[Ch, :] = (ADC_Cooling[Ch, :] + MetaData[ch_tsp]["Offset"]) / MetaData[ch_tsp]["LinGain"]

                    # Calculate the start temperature of both monitoring channels to have a good starting point for Zth-Matrix
                    T_Monitor_Heated[Ch] = (np.mean(ADC[Ch, ((CoolingStartBlock - 2) * SampDecade):((CoolingStartBlock - 1) * SampDecade) - 1])
                                            + MetaData[ch_tsp]["Offset"]) / MetaData[ch_tsp]["LinGain"]
                    if Ch == 0:
                        print(
                            "COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C".format(
                                DUTno=Ch,
                                Ucold=UDio_Cold_Start[Ch],
                                UColdEnd=UDio_Cold_End[Ch],
                                dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
                                dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / MetaData[ch_tsp]["LinGain"])))
                    else:
                        print(
                            "COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C; "
                            "Heated Temp: {T_heated: 3.4f}°C".format(DUTno=Ch,
                                                                     Ucold=UDio_Cold_Start[Ch],
                                                                     UColdEnd=UDio_Cold_End[Ch],
                                                                     dU_DUT=UDio_Cold_Start[Ch] - UDio_Cold_End[Ch],
                                                                     dT_DUT=((UDio_Cold_End[Ch] - UDio_Cold_Start[Ch]) / MetaData[ch_tsp]["LinGain"]),
                                                                     T_heated=T_Monitor_Heated[Ch]))

            for Ch in range(0, NoOfDUTs):
                ch_tsp = "TSP{Ch}".format(Ch=Ch)
                if MetaData[ch_tsp]["Name"] != "OFF":
                    G_Plots[0, 0].plot(TimeBaseTotal, ADC[Ch, :], label=MetaData[ch_tsp]["Name"])  # Plot some data on the axes.

            G_Plots[0, 0].set_title("Diode Voltages of the full measurement", size=8)
            G_Plots[0, 0].set_ylabel('Diode Voltage / [V]', size=8)
            G_Plots[0, 0].set_xlabel('Time / [s]', size=8)
            G_Plots[0, 0].tick_params(axis='both', which='major', labelsize=7)
            G_Plots[0, 0].legend(prop={'size': 6})
            G_Plots[0, 0].grid(which='both')

            G_Plots[0, 1].plot(TimeBaseTotal, ADC[3, :], label="Current")  # Plot some data on the axes.
            G_Plots[0, 1].set_title("Drive current", size=8)
            G_Plots[0, 1].tick_params(axis='both', which='major', labelsize=7)
            G_Plots[0, 1].set_ylabel('Current / [A]', size=8)
            G_Plots[0, 1].set_xlabel('Time / [s]', size=8)
            G_Plots[0, 1].legend(prop={'size': 6})
            G_Plots[0, 1].grid(which='both')

            if not MetaData["TSP_Calibration_File"]:
                for Ch in range(0, NoOfDUTs):
                    ch_tsp = "TSP{Ch}".format(Ch=Ch)
                    if MetaData[ch_tsp]["Name"] != "OFF":
                        G_Plots[1, 0].semilogx(TimeBase_Cooling, ADC_Cooling[Ch, :], label=MetaData[ch_tsp]["Name"])  # Plot some data on the axes.

                G_Plots[1, 0].set_title("Diode Voltages of the cooling section", size=8)
                G_Plots[1, 0].set_ylabel('Diode Voltage / [V]', size=8)
                G_Plots[1, 0].set_xlabel('Time / [s]', size=8)
                G_Plots[1, 0].tick_params(axis='both', which='major', labelsize=7)
                G_Plots[1, 0].legend(prop={'size': 6})
                G_Plots[1, 0].grid(which='both')

                G_Plots[1, 1].semilogx(TimeBase_Cooling, ADC_Cooling[3, :], label="Current")  # Plot some data on the axes.
                G_Plots[1, 1].set_title("Drive current in cooling section", size=8)
                G_Plots[1, 1].set_ylabel('Current / [A]', size=8)
                G_Plots[1, 1].set_xlabel('Time / [s]', size=8)
                G_Plots[1, 1].tick_params(axis='both', which='major', labelsize=7)
                G_Plots[1, 1].legend(prop={'size': 6})
                G_Plots[1, 1].grid(which='both')

            G_Plots[2, 0].set_title("Thermocouple data of the full measurement", size=8)
            G_Plots[2, 0].plot(Temp[0, :], label="Sensor 1")  # Plot some data on the axes.
            G_Plots[2, 0].plot(Temp[1, :], label="Sensor 2")  # Plot some data on the axes.
            G_Plots[2, 0].plot(Temp[2, :], label="Sensor 3")  # Plot some data on the axes.
            G_Plots[2, 0].plot(Temp[3, :], label="Sensor 4")  # Plot some data on the axes.
            G_Plots[2, 0].set_ylabel('Temperature / [°C]', size=8)
            G_Plots[2, 0].set_xlabel('Sample', size=8)
            G_Plots[2, 0].tick_params(axis='both', which='major', labelsize=7)
            G_Plots[2, 0].legend(prop={'size': 6})
            G_Plots[2, 0].grid(which='both')

            MetaString = "File Name: " + DataFile + "\n"
            MetaString += "Measurement started: " + MetaData["StartDate"] + " " + MetaData["StartTime"] + "\n\n"

            if MetaData["TSP_Calibration_File"]:
                MetaString += "** TSP CALIBRATION MEASUREMENT **\n\n"
                MetaString += "Measurement Time:\t{preheat:.2f} min\n".format(preheat=MetaData["T_Preheat"] / 60)
            else:
                MetaString += "PreHeating Time:\t{preheat:.2f} min\n".format(preheat=MetaData["T_Preheat"] / 60)
                MetaString += "Heating Time:\t{heat:.2f} min\n".format(heat=MetaData["T_Heat"] / 60)
                MetaString += "Cooling Time:\t{cool:.2f} min\n\n".format(cool=MetaData["T_Cool"] / 60)

            MetaString += "No. Name\tOffset\t\tGain\n"
            MetaString += "00:  {name}\t{offs:.1f}mV\t\t{gain:.2f}mV/K\n".format(name=MetaData["TSP0"]["Name"],
                                                                                 offs=MetaData["TSP0"]["Offset"] * 1000,
                                                                                 gain=MetaData["TSP0"]["LinGain"] * 1000)
            if not "OFF" in MetaData["TSP1"]["Name"]:
                MetaString += "01:  {name}\t{offs:.1f}mV\t\t{gain:.2f}mV/K\n".format(name=MetaData["TSP1"]["Name"],
                                                                                     offs=MetaData["TSP1"]["Offset"] * 1000,
                                                                                     gain=MetaData["TSP1"]["LinGain"] * 1000)
            if not "OFF" in MetaData["TSP2"]["Name"]:
                MetaString += "02:  {name}\t{offs:.1f}mV\t\t{gain:.2f}mV/K\n".format(name=MetaData["TSP2"]["Name"],
                                                                                     offs=MetaData["TSP2"]["Offset"] * 1000,
                                                                                     gain=MetaData["TSP2"]["LinGain"] * 1000)

            MetaString += "\nSense Current:\t{Isen:.2f} mA\n".format(Isen=MetaData["ISEN"] * 1000)
            if not MetaData["TSP_Calibration_File"]:
                MetaString += "Heating Current:\t{Iheat:.3f} A\n".format(Iheat=I_Heat)
                MetaString += "Heating Power:\t{Pheat:.3f} W\n".format(Pheat=PDio_Heat)

            self.meas_meta_data.configure(text=MetaString)
            self.canvas.draw()

    def read_measurement_file_callback(self):
        global TimeBaseTotal, ADC, Temp, DataFile, MetaData, FileOpened
        measfilename = uTTA_data_import.select_file("Select the measurement file",
                                                    (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        if len(measfilename) > 0:  # check if string is not empty
            DataFile, data_file_no_ext, file_path = uTTA_data_import.split_file_path(measfilename)

            TimeBaseTotal, ADC, Temp, MetaData = uTTA_data_import.read_measurement_file(measfilename, 0)
            FileOpened = True
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
