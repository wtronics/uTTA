from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # matplotlib 3.9.2
from matplotlib.figure import Figure
import uTTA_data_import
import uTTA_data_processing
import numpy as np                  # numpy 2.1.1
import numpy.dtypes                 # numpy 2.1.0
import matplotlib                   # matplotlib 3.9.2
import ttkbootstrap as ttk          # ttkbootstrap 1.13.5

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
        self.title("uTTA umf-Viewver")
        self.geometry("1480x900")
        self.minsize(1480, 900)
        screen_dpi = self.winfo_fpixels('1i')
#        self.protocol("WM_DELETE_WINDOW", self.on_closing)      # window closing event

        # widgets
        global G_Plots

        self.grid_columnconfigure(6, weight=1)
        self.grid_rowconfigure(20, weight=1)

        self.frm_file_btns = ttk.Frame(master=self)
        self.frm_file_btns.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frm_file_btns.grid_rowconfigure(1, weight=1)
        self.frm_file_btns.grid_columnconfigure(21, weight=1)

        self.btn_measure_file = ttk.Button(master=self.frm_file_btns, text="Measurement File",
                                           command=self.read_measurement_file_callback, bootstyle="dark")
        self.btn_measure_file.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.frm_meas_data = ttk.Frame(master=self)
        self.frm_meas_data.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.frm_meas_data.grid_rowconfigure(index=6, weight=1)
        self.frm_meas_data.grid_columnconfigure(index=1, weight=1)

        self.frm_help_bar = ttk.Frame(master=self, bootstyle="info")
        self.frm_help_bar.grid(row=0, column=1, columnspan=5, padx=10, pady=10, sticky="ew")
        self.frm_help_bar.grid_rowconfigure(1, weight=1)
        self.frm_help_bar.grid_columnconfigure(1, weight=1)

        self.lbl_helpbar = ttk.Label(master=self.frm_help_bar, anchor="w", bootstyle="inverse-info")
        self.lbl_helpbar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.lbl_helpbar.configure(text="Welcome to the umf-Viewer GUI. Click 'Measurement File' and import a measurement")

        self.frm_plot_area = ttk.Frame(master=self)
        self.frm_plot_area.grid(row=1, column=1, columnspan=5, padx=10, pady=10, sticky="ew")
        self.fig = Figure(figsize=(8.4, 4.95), dpi=screen_dpi)
        self.fig.subplots_adjust(left=0.06, bottom=0.075, right=0.97, top=0.96, wspace=0.212, hspace=0.54)
        G_Plots = self.fig.subplots(3, 2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1, rowspan=18, columnspan=5, padx=10, pady=10, sticky="ew")
        # Toolbar #########
        toolbar_frame = ttk.Frame(master=self)
        toolbar_frame.grid(row=21, column=1, columnspan=5)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        self.update_plots()
        self.update()

    def update_plots(self):

        global G_Plots, Temp, MetaData, FileOpened
        if FileOpened:
            G_Plots[0, 0].clear()

            # Calculate the average ambient temperature as starting point
            StartTempTC = np.mean(Temp[3, 0:10])
            print("Averaged start temperature form TC-Channel 3: {Tstart:.3f}°C".format(Tstart=StartTempTC))

            CoolingStartBlock = MetaData["CoolingStartBlock"]
            SampDecade = MetaData["SamplesPerDecade"]

            # Cut Timebase and measurement to cooling section
            TimeBase_Cooling, ADC_Cooling = uTTA_data_processing.calculate_cooling_curve(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade)

            # # Calculate the average heating current, voltage and power through the diode
            PDio_Heat = uTTA_data_processing.calculate_diode_heating(TimeBaseTotal, ADC, CoolingStartBlock, SampDecade)

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
                        print("COLD VOLTAGE: DUT{DUTno} at Start: {Ucold: 3.4f}V; at End: {UColdEnd: 3.4f}V; Delta U: {dU_DUT: 3.4f}V; Delta T: {dT_DUT: 3.4f}°C; "
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

            self.canvas.draw()


    def read_measurement_file_callback(self):
        global TimeBaseTotal, ADC, Temp, DataFile, MetaData, FileOpened
        measfilename = uTTA_data_import.select_file("Select the measurement file",
                                                    (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        if len(measfilename) > 0:    # check if string is not empty
            DataFile, data_file_no_ext, file_path = uTTA_data_import.split_file_path(measfilename)

            TimeBaseTotal, ADC, Temp, MetaData = uTTA_data_import.read_measurement_file(measfilename, 0)
            FileOpened = True
            self.update_plots()


            self.lbl_helpbar.configure(text="File: " + DataFile + " was successfully imported. Now click on the magnifying glass below the plot and select "+
                                       "the first horizontal section in the upper plot.", bootstyle="inverse-success")
            self.frm_help_bar.configure(bootstyle="success")

        else:
            self.lbl_helpbar.configure(text="File: " + DataFile + " was not imported.", bootstyle="inverse-danger")
            self.frm_help_bar.configure(bootstyle="danger")


def on_closing(self):
    # if messagebox.askokcancel("Quit", "Do you want to quit?"):
    self.destroy()


app = umf_viewer_App()

app.mainloop()