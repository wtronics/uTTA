import uTTA_data_import
import uTTA_data_processing
import numpy as np                  # numpy 2.1.1
import numpy.dtypes                 # numpy 2.1.1
import matplotlib                   # matplotlib 3.9.2

import customtkinter                # customtkinter 5.2.2
import customtkinter as ctk         # customtkinter 5.2.2
import blittedsnappycursor as bsc
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)     # matplotlib 3.9.2
from matplotlib.backend_bases import MouseEvent
from matplotlib.figure import Figure
from tkinter import messagebox      # part of python 3.12.5
from tksheet import (               # tksheet 7.2.16
    Sheet, formatter,
    float_formatter, int_formatter,
    percentage_formatter, bool_formatter,
    truthy, falsy, num2alpha)


PGA_Calibration = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], dtype=float)
ADC_Calibration = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], dtype=float)

CH_Names = []
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

        self.geometry("1400x700")
        self.minsize(1400, 700)
        self.title("uTTA Calibration Factor Calculation Tool")
        self.update()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)      # window closing event

        self.frm_file_btns = ctk.CTkFrame(master=self, width=400, height=40)
        self.frm_file_btns.place(x=10, y=10)
        self.frm_file_btns.grid_rowconfigure(1, weight=1)
        self.frm_file_btns.grid_columnconfigure(2, weight=1)

        self.btn_cal_file = ctk.CTkButton(master=self.frm_file_btns,
                                          text="Calibration File", fg_color="blue", width=155, height=30,
                                          command=self.read_calfile_callback)
        self.btn_cal_file.place(x=5, y=5)

        self.btn_measure_file = ctk.CTkButton(master=self.frm_file_btns,
                                              text="Measurement File", fg_color="blue", width=155, height=30,
                                              command=self.read_measurement_file_callback,
                                              state="disabled"
                                              )
        self.btn_measure_file.place(x=165, y=5)

        frm_tstep_entry = ctk.CTkFrame(master=self, width=400, height=40)
        frm_tstep_entry.place(x=10, y=60)
        self.btn_add_steps = ctk.CTkButton(master=frm_tstep_entry,
                                           text="Add Step", fg_color="blue",
                                           command=self.add_calibration_step,
                                           state="disabled", width=125, height=30)
        self.btn_add_steps.place(x=5, y=5)
        lbl_no_steps = ctk.CTkLabel(master=frm_tstep_entry,
                                    text_color="white",
                                    text="Step Temperature:", justify="right",
                                    width=140, height=30)
        lbl_no_steps.place(x=135, y=5)

        self.ent_step_temp = ctk.CTkEntry(master=frm_tstep_entry,
                                          fg_color="blue",
                                          placeholder_text="°C",
                                          width=60, height=30)
        self.ent_step_temp.place(x=260, y=5)

        frm_step_table = ctk.CTkFrame(master=self, width=430, height=305)
        frm_step_table.place(x=10, y=110)
        tab_label = ctk.CTkLabel(master=frm_step_table,
                                 text_color="white",
                                 text="Calibration Temperature Steps", justify="center",
                                 width=420, height=20)
        tab_label.place(x=5, y=5)

        tab_heading = ["T/[°C]", "CH0 Avg.", "CH1 Avg.", "CH2 Avg.", "Temp Avg.", "Start", "End"]
        self.t_step_sheet = Sheet(frm_step_table,
                                  width=420,
                                  height=270,
                                  startup_select=(0, 1, "rows"),
                                  startup_focus=(0, 1, "rows"),
                                  page_up_down_select_row=True)
        self.t_step_sheet.place(x=5, y=30)
        self.t_step_sheet.headers(tab_heading)
        self.t_step_sheet.set_all_column_widths(65)

        frm_result_table = ctk.CTkFrame(master=self, width=430, height=225)
        frm_result_table.place(x=10, y=425)
        result_label = ctk.CTkLabel(master=frm_result_table,
                                    text_color="white",
                                    text="Linearization Results", justify="center",
                                    width=420, height=20)
        result_label.place(x=5, y=5)

        tab_result_heading = ["Channel", "Gain", "Offset", "R²"]
        self.t_result_sheet = Sheet(frm_result_table, width=420, height=150, show_x_scrollbar=False, show_y_scrollbar=False)
        self.t_result_sheet.place(x=5, y=30)
        self.t_result_sheet.insert_columns(columns=4)
        self.t_result_sheet.insert_rows(rows=3)
        self.t_result_sheet.sheet_data_dimensions(total_rows=4, total_columns=4)
        self.t_result_sheet.headers(tab_result_heading)
        self.t_result_sheet.set_all_column_widths(85)

        self.btn_save_result = ctk.CTkButton(master=frm_result_table,
                                             text="Save Calibration", fg_color="blue",
                                             # command=self.save_calibration_results,
                                             state="disabled", width=420, height=30)
        self.btn_save_result.place(x=5, y=190)

        self.fig = Figure(figsize=(9.1, 6), dpi=100)
        G_Plots = self.fig.subplots(2, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().place(x=550, y=10)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
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
                G_Plots[1].plot(TimeBaseTotal, Temp[PlotIdx, :], label="TC " + str(PlotIdx + 1))
            G_Plots[1].set_xlabel("Time / [s]")
            G_Plots[1].set_ylabel("Temperature / [°C]")
            G_Plots[1].set_xlim(left=0)

            G_Plots[1].legend(loc="lower left")
            G_Plots[1].grid(True)

        self.canvas.draw()

    def read_calfile_callback(self):
        global PGA_Calibration, ADC_Calibration
        cal_file_path = uTTA_data_import.select_file("Select the uTTA Calibration File",
                                                     (('uTTA Calibration Files', '*.uTTA_CAL'), ('All files', '*.*')))
        print("Reading calibration values from file: " + cal_file_path)

        PGA_Calibration, ADC_Calibration = uTTA_data_import.read_calfile(cal_file_path)
        self.btn_measure_file.configure(state='normal')
        return

    def read_measurement_file_callback(self):
        global TimeBaseTotal, ADC, CH_Names, Temp, CoolingStartBlock, DataFile
        measfilename = uTTA_data_import.select_file("Select the measurement file",
                                                    (('Text-Files', '*.txt'), ('uTTA Measurement Files', '*.t3r'), ('All files', '*.*')))
        DataFile, data_file_no_ext, file_path = uTTA_data_import.split_file_path(measfilename, '.t3i')

        tb_import, adc_import, tc_import, samp_decade, CoolingStartBlock, CH_Names, dut_tsp_sensitivity = (
            uTTA_data_import.read_measurement_file(measfilename, PGA_Calibration, ADC_Calibration, 0))

        TimeBaseTotal, ADC, Temp = uTTA_data_processing.interpolate_to_common_timebase(tb_import, adc_import, tc_import)

        self.update_plots()
        self.btn_add_steps.configure(state='normal')

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

    # def save_calibration_results(self):

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
        self.ent_step_temp.delete(0, 'end')
        self.ent_step_temp.insert(0, "{:.2f}".format(np.mean(Temp[0, xlim_min:xlim_max])))


# Declare and register callbacks


app = CalApp()

app.mainloop()
