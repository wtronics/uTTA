from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # matplotlib 3.9.2
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import messagebox  # part of python 3.12.5
from tksheet import (  # tksheet 7.2.16
    Sheet)
from quantiphy import Quantity      # quantiphy 2.20
import uTTA_data_import
import uTTA_data_processing
import numpy as np                  # numpy 2.1.1
import matplotlib                   # matplotlib 3.9.2
import customtkinter                # customtkinter 5.2.2
import customtkinter as ctk         # customtkinter 5.2.2

matplotlib.use("TkAgg")

PGA_Calibration = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], dtype=float)
ADC_Calibration = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], dtype=float)

CalData_FileName = ''
CH_Names = []
Diode_Calibration = []
TimeBaseTotal = []
ADC = []
Temp = []
TableValues = []
CoolingStartBlock = 0
MaxDeltaT_StartEnd = 1.0
DataFile = ''
G_Plots = []


class CalApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        global G_Plots

        self.geometry("1480x750")
        screen_dpi = self.winfo_fpixels('1i')
        ctk.deactivate_automatic_dpi_awareness()
        print("DPI: " + str(screen_dpi))
        self.minsize(1480, 750)
        self.title("uTTA Calibration Factor Calculation Tool")
        self.update()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)      # window closing event
        self.grid_columnconfigure(6, weight=1)
        self.grid_rowconfigure(20, weight=1)

        self.frm_file_btns = ctk.CTkFrame(master=self)
        self.frm_file_btns.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frm_file_btns.grid_rowconfigure(1, weight=1)
        self.frm_file_btns.grid_columnconfigure(1, weight=1)

        self.btn_measure_file = ctk.CTkButton(master=self.frm_file_btns,
                                              text="Measurement File", fg_color="blue",
                                              command=self.read_measurement_file_callback
                                              )
        self.btn_measure_file.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.frm_help_bar = ctk.CTkFrame(master=self)
        self.frm_help_bar.grid(row=0, column=1, columnspan=5, padx=10, pady=10, sticky="ew")
        self.frm_help_bar.grid_rowconfigure(1, weight=1)
        self.frm_help_bar.grid_columnconfigure(1, weight=1)

        self.lbl_helpbar = ctk.CTkLabel(master=self.frm_help_bar,
                                        fg_color="blue", width=1050, anchor="w", padx=10)
        self.lbl_helpbar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.lbl_helpbar.configure(text="Welcome to the calibration GUI v2. Click 'Measurement File' and import a calibration measurement")

        frm_tstep_entry = ctk.CTkFrame(master=self)
        frm_tstep_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        frm_tstep_entry.grid_rowconfigure(index=1, weight=1)
        frm_tstep_entry.grid_columnconfigure(index=3, weight=1)
        self.btn_add_steps = ctk.CTkButton(master=frm_tstep_entry,
                                           text="Add Step", fg_color="blue",
                                           command=self.add_calibration_step,
                                           state="disabled")
        self.btn_add_steps.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        lbl_no_steps = ctk.CTkLabel(master=frm_tstep_entry,
                                    text_color="white",
                                    text="Step Temperature:", justify="right")
        lbl_no_steps.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.ent_step_temp = ctk.CTkEntry(master=frm_tstep_entry,
                                          fg_color="blue",
                                          placeholder_text="°C", width=60)
        self.ent_step_temp.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

        frm_step_table = ctk.CTkFrame(master=self)
        frm_step_table.grid(row=2, rowspan=12, column=0, padx=10, pady=10, sticky="ew")
        frm_step_table.grid_rowconfigure(index=8, weight=1)
        frm_step_table.grid_columnconfigure(index=0, weight=1)

        tab_label = ctk.CTkLabel(master=frm_step_table,
                                 text_color="white",
                                 text="Calibration Temperature Steps", justify="center")
        tab_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        tab_heading = ["T/[°C]", "CH0 Avg.", "CH1 Avg.", "CH2 Avg.", "Temp Avg.", "Start", "End"]
        self.t_step_sheet = Sheet(frm_step_table,
                                  startup_select=(0, 1, "rows"),
                                  page_up_down_select_row=True,
                                  height=220)
        self.t_step_sheet.grid(row=1, rowspan=7, column=0, padx=10, pady=10, sticky="ew")
        self.t_step_sheet.headers(tab_heading)
        self.t_step_sheet.set_all_column_widths(65)

        frm_result_table = ctk.CTkFrame(master=self)
        frm_result_table.grid(row=14, rowspan=7, column=0, padx=10, pady=10, sticky="ew")
        frm_result_table.grid_rowconfigure(index=6, weight=1)
        frm_result_table.grid_columnconfigure(index=0, weight=1)

        result_label = ctk.CTkLabel(master=frm_result_table,
                                    text_color="white",
                                    text="Linearization Results", justify="center")
        result_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        tab_result_heading = ["Channel", "Gain", "Offset", "R²"]
        self.t_result_sheet = Sheet(frm_result_table, show_y_scrollbar=False, height=150)
        self.t_result_sheet.grid(row=1, rowspan=4, column=0, padx=10, pady=10, sticky="ew")
        self.t_result_sheet.insert_columns(columns=4)
        self.t_result_sheet.insert_rows(rows=3)
        self.t_result_sheet.sheet_data_dimensions(total_rows=4, total_columns=4)
        self.t_result_sheet.headers(tab_result_heading)
        self.t_result_sheet.set_all_column_widths(85)

        self.btn_save_result = ctk.CTkButton(master=frm_result_table,
                                             text="Save Calibration", fg_color="blue",
                                             command=self.save_calibration_results,
                                             state="disabled")
        self.btn_save_result.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        self.fig = Figure(figsize=(11, 6.5), dpi=screen_dpi)
        G_Plots = self.fig.subplots(2, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1, rowspan=18, columnspan=5, padx=10, pady=10, sticky="ew")
        # Toolbar #########
        toolbar_frame = ctk.CTkFrame(master=self)
        toolbar_frame.grid(row=20, column=1, columnspan=5)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.update_plots()
        self.update()

    def update_plots(self):

        global G_Plots, Temp
        G_Plots[0].clear()
        # print("length ADC: " + str(len(CH_Names)))
        lines = []
        for PlotIdx in range(0, len(CH_Names)):
            if CH_Names[PlotIdx] != "OFF":
                line, = G_Plots[0].plot(TimeBaseTotal, ADC[PlotIdx, :], label=CH_Names[PlotIdx])
                lines.append(line)

        G_Plots[0].set_xlabel("Time / [s]")
        G_Plots[0].set_ylabel("Diode Voltage / [V]")
        G_Plots[0].set_xlim(left=0)
        G_Plots[0].callbacks.connect('xlim_changed', self.on_xlims_change)
        G_Plots[0].grid(True)

        if len(ADC) > 0:
            G_Plots[0].legend(loc="lower left")

        G_Plots[1].clear()
        # print("Temp Len: " + str(len(Temp)))
        # Temp = Temp[0, :]
        if len(Temp) > 0:
            for PlotIdx in range(1):
                G_Plots[1].plot(TimeBaseTotal, Temp[PlotIdx, :], label="TC " + str(PlotIdx))

            G_Plots[1].set_xlim(left=0)

            G_Plots[1].legend(loc="lower left")
            G_Plots[1].grid(True)

        G_Plots[1].set_xlabel("Time / [s]")
        G_Plots[1].set_ylabel("Temperature / [°C]")

        self.canvas.draw()

    def save_calibration_results(self):

        cal_file_name = uTTA_data_import.select_file("Select the measurement file",
                                                     (('uTTA Calibration Files', '*.ucf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        cfile, data_file_no_ext, file_path = uTTA_data_import.split_file_path(cal_file_name)
        if len(cal_file_name) > 0:  # check if string is not empty
            tsp_cal_value = uTTA_data_import.DevCalibration

            for ChIdx in range(0, 4):  # iterate through all the 4 channels viewed
                tsp_name = self.t_result_sheet.get_cell_data(ChIdx, 0)
                if tsp_name != "OFF":
                    abort_save = False

                    tsp_offs = self.t_result_sheet.get_cell_data(ChIdx, 2)
                    tsp_lin = self.t_result_sheet.get_cell_data(ChIdx, 1)
                    tsp_cub = 0.0
                    r_sq = self.t_result_sheet.get_cell_data(ChIdx, 3)
                    if r_sq < 0.98:
                        msg_box = tk.messagebox.askquestion("Low confidence results",
                                                            "The R² of channel '"+ tsp_name +"'only {Rsqmin:.3f}".format(Rsqmin=np.min(r_sq)) +
                                                            ", this seems to low to provide a good calibration.\n" +
                                                            "Do you wish to continue anyway?", icon="warning", )
                        if msg_box != "yes":
                            abort_save = True
                    if not abort_save:
                        print("Creating Cal Entry for Channel {Ch}, Name: {nam}, Offset {Offs:.4f}, Gain {Gain:.4f}".format(
                            Ch=ChIdx, nam=tsp_name, Offs=tsp_offs, Gain=tsp_lin))

                        tsp_cal_value.Name = tsp_name
                        tsp_cal_value.Offset = tsp_offs
                        tsp_cal_value.Lin_Gain = tsp_lin
                        tsp_cal_value.Cub_Gain = tsp_cub

                        uTTA_data_import.write_diodes_to_calfile(cal_file_name, tsp_cal_value)
                        self.lbl_helpbar.configure(text="Successfully saved calibration of channel " + tsp_name + " to file: " + data_file_no_ext)
                    else:
                        self.lbl_helpbar.configure(text="Aborted saving calibration of channel " + tsp_name + "because of bad convergence")
        else:
            self.lbl_helpbar.configure(text="File: " + DataFile + " was not imported.")

    def read_measurement_file_callback(self):
        global TimeBaseTotal, ADC, CH_Names, Temp, CoolingStartBlock, DataFile
        measfilename = uTTA_data_import.select_file("Select the measurement file",
                                                    (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        if len(measfilename) > 0:    # check if string is not empty
            DataFile, data_file_no_ext, file_path = uTTA_data_import.split_file_path(measfilename)

            tb_import, adc_import, tc_import, samp_decade, CoolingStartBlock, CH_Names, dut_tsp_sensitivity = (
                uTTA_data_import.read_measurement_file(measfilename, 0))

            TimeBaseTotal, ADC, Temp = uTTA_data_processing.interpolate_to_common_timebase(tb_import, adc_import, tc_import)

            self.update_plots()
            self.btn_add_steps.configure(state='normal')
            self.lbl_helpbar.configure(text="File: " + DataFile + " was successfully imported. Now click on the magnifying glass below the plot and select "+
                                       "the first horizontal section in the upper plot.")
        else:
            self.lbl_helpbar.configure(text="File: " + DataFile + " was not imported.")

    def add_calibration_step(self):
        cal_range = G_Plots[0].get_xlim()
        # print("New Calibration Range: ", cal_range)
        t_step = self.ent_step_temp.get()
        t_step = t_step.replace(",", ".")
        if t_step.isdigit():
            # tab_line = np.array(float(self.ent_step_temp.get()), int(cal_range[0]), int(cal_range[1]) )
            tbl = self.t_step_sheet.data

            xstart = int(cal_range[0])
            xend = int(cal_range[1])

            self.t_step_sheet.insert_row(idx=0)
            self.t_step_sheet["A1"].data = float(t_step)
            self.t_step_sheet["B1"].data = np.mean(ADC[0, xstart:xend])
            self.t_step_sheet["C1"].data = np.mean(ADC[1, xstart:xend])
            self.t_step_sheet["D1"].data = np.mean(ADC[2, xstart:xend])
            self.t_step_sheet["E1"].data = np.mean(Temp[0, xstart:xend])
            self.t_step_sheet["F1"].data = xstart
            self.t_step_sheet["G1"].data = xend

            self.ent_step_temp.delete(0, 'end')
            self.update_plots()

            if len(tbl) >= 2:    # above two selected points the interpolation calculation ca begin

                for ChIdx in range(0, 4):   # iterate through all the 4 channels viewed

                    x_data = np.array(self.t_step_sheet.get_column_data(0), dtype=np.float32)
                    print("X-Data: " + str(x_data))
                    y_data = np.array(self.t_step_sheet.get_column_data(ChIdx+1), dtype=np.float32)
                    slope, offs = np.polyfit(x_data, y_data, 1)
                    if abs(slope) > 0.00001:
                        y_fit = offs + slope * x_data
                        corr_mat = np.corrcoef(y_data, y_fit)
                        corr = corr_mat[0, 1]
                        r_sq = corr**2
                    else:
                        r_sq = 1.0
                    print("Fitting Channel {Ch} with linear interpolation: Slope: {Slope:.4f}, Offset: {Offs:.4f} R²: {Rsq:.4f}".format(
                         Ch=ChIdx, Slope=slope, Offs=offs, Rsq=r_sq))
                    if ChIdx < 3:
                        self.t_result_sheet.set_cell_data(r=ChIdx, c=0, value=CH_Names[ChIdx])
                    else:
                        self.t_result_sheet.set_cell_data(r=ChIdx, c=0, value="TC0")
                    self.t_result_sheet.set_cell_data(r=ChIdx, c=1, value=slope)
                    self.t_result_sheet.set_cell_data(r=ChIdx, c=2, value=offs)
                    self.t_result_sheet.set_cell_data(r=ChIdx, c=3, value=r_sq)

                self.btn_save_result.configure(state='normal')
                self.lbl_helpbar.configure(text="Repeat the selection process with the next temperature step, "
                                                + "or press 'Save Calibration' to complete the process.")
            else:
                self.lbl_helpbar.configure(text="Repeat the selection process with the next temperature step")

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.destroy()

    def on_xlims_change(self, event_ax):
        global G_Plots
        x_limits = event_ax.get_xlim()
        xlim_min = int(x_limits[0])
        xlim_max = int(x_limits[1])
        # print("updated xlims: ", event_ax.get_xlim())
        G_Plots[1].set_xlim(left=x_limits[0], right=x_limits[1])
        ymin = np.min(Temp[0, xlim_min:xlim_max])
        ymax = np.max(Temp[0, xlim_min:xlim_max])
        G_Plots[1].set_ylim(bottom=ymin, top=ymax)

        tsp_min = np.min(ADC[0, xlim_min:xlim_max])
        tsp_max = np.max(ADC[0, xlim_min:xlim_max])
        tsp_pp = Quantity(tsp_max-tsp_min, "V")

        self.ent_step_temp.delete(0, 'end')
        self.ent_step_temp.insert(0, "{:.2f}".format(np.mean(Temp[0, xlim_min:xlim_max])))

        self.lbl_helpbar.configure(text="Zoom into the measurement until the whole plot is filled with the steady state. " +
                                   "Peak-to-peak spread of " + CH_Names[0] + " is {tsp_mm}. ".format(tsp_mm=tsp_pp) +
                                   "\nWhen you are satisfied enter the step temperature and click on 'Add Step'")


# Declare and register callbacks


app = CalApp()

app.mainloop()
