from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # matplotlib 3.9.2
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import messagebox  # part of python 3.12.5
from tksheet import (Sheet, float_formatter)
from quantiphy import Quantity      # quantiphy 2.20

import library.uTTA_data_processing as udpc
import numpy as np                  # numpy 2.1.1
import matplotlib                   # matplotlib 3.9.2
import ttkbootstrap as ttk

matplotlib.use("TkAgg")

CalData_FileName = ''
Diode_Calibration = []
TableValues = []

MaxDeltaT_StartEnd = 1.0
DataFile = ''
G_Plots = []
Static_States = []
Highlight_State = -1
MaxJUT_Channels = 3
InterpolationDegrees = 1
MetaData = {}


class CalApp(ttk.Window):
    def __init__(self):
        super().__init__()
        # self.hdpi = False
        self.title("uTTA Calibration Factor Calculation Tool")
        self.geometry("1480x750")
        self.minsize(1480, 750)
        screen_dpi = self.winfo_fpixels('1i')
        geometry = self.winfo_geometry()
        print("DPI: " + str(screen_dpi) + " Geometry: " + str(geometry))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        global G_Plots

        self.utta_data = udpc.UttaZthProcessing()

        self.frm_file_btns = ttk.Frame(master=self,  width=350, height=60, style="secondary.TFrame")
        self.frm_file_btns.place(x=10, y=10)

        self.btn_measure_file = ttk.Button(master=self.frm_file_btns, text="Measurement File", width=35,
                                           command=self.read_measurement_file_callback)
        self.btn_measure_file.place(x=10, y=10)

        self.frm_help_bar = ttk.Frame(master=self, width=1050, height=60, style='info.TFrame')
        self.frm_help_bar.place(x=370, y=10)

        self.lbl_helpbar = ttk.Label(master=self.frm_help_bar, width=150, style='info.Inverse.TLabel')
        self.lbl_helpbar.place(x=10, y=15)
        self.lbl_helpbar.configure(text="Welcome to the calibration GUI v2. Click 'Measurement File' and import a calibration measurement")

        frm_step_table = ttk.Frame(master=self,  width=350, height=400, style="secondary.TFrame")
        frm_step_table.place(x=10, y=80)

        tab_label = ttk.Label(master=frm_step_table, text="Calibration Temperature Steps", style='secondary.Inverse.TLabel',
                              justify="center", width=330)
        tab_label.place(x=10, y=10)

        lbl_no_steps = ttk.Label(master=frm_step_table, text="Step Temp:", width=120,
                                 style='secondary.Inverse.TLabel', justify="right")
        lbl_no_steps.place(x=170, y=45)

        self.ent_step_temp = ttk.Entry(master=frm_step_table, width=8, justify="right")
        self.ent_step_temp.insert(-1, "°C")
        self.ent_step_temp.place(x=250, y=40)

        self.btn_add_steps = ttk.Button(master=frm_step_table, text="Add Step", width=13,
                                        command=self.add_calibration_step, state="disabled")
        self.btn_add_steps.place(x=10, y=40)

        self.btn_rem_steps = ttk.Button(master=frm_step_table, text="Remove Step", width=13,
                                        command=self.remove_calibration_step)
        self.btn_rem_steps.place(x=10, y=80)

        self.btn_calc_steps = ttk.Button(master=frm_step_table, text="Recalculate", width=13,
                                         command=self.fit_temp_steps, state="disabled")
        self.btn_calc_steps.place(x=10, y=120)

        tab_heading = ["T/[°C]", "CH0 Avg.", "CH1 Avg.", "CH2 Avg.", "Temp Avg.", "Start", "End"]
        self.t_step_sheet = Sheet(frm_step_table, startup_select=(0, 1, "rows"),
                                  page_up_down_select_row=True, height=230, width=330)
        self.t_step_sheet.format("A", formatter_options=float_formatter(), decimals=3)
        self.t_step_sheet.format("B:E", formatter_options=float_formatter(), decimals=4)

        self.t_step_sheet.place(x=10, y=160)
        self.t_step_sheet.enable_bindings(('single_select', 'edit_cell'))
        self.t_step_sheet.extra_bindings("cell_select", self.on_cell_select)
        self.t_step_sheet.headers(tab_heading)
        self.t_step_sheet.set_all_column_widths(65)

        frm_result_table = ttk.Frame(master=self, width=350, height=250, style="secondary.TFrame")
        frm_result_table.place(x=10, y=490)

        result_label = ttk.Label(master=frm_result_table, width=330, style='secondary.Inverse.TLabel',
                                 text="Linearization Results", justify="center")
        result_label.place(x=10, y=10)

        tab_result_heading = ["Channel", "Offset", "Lin.", "Quad.", "R²"]
        self.t_result_sheet = Sheet(frm_result_table, show_y_scrollbar=False, height=160, width=330, row_index_width=30)
        self.t_result_sheet.place(x=10, y=40)
        self.t_result_sheet.insert_columns(columns=4)
        self.t_result_sheet.insert_rows(rows=3)
        self.t_result_sheet.enable_bindings()
        self.t_result_sheet.sheet_data_dimensions(total_rows=4, total_columns=4)
        self.t_result_sheet.format("B:E", formatter_options=float_formatter(), decimals=4)
        # self.t_result_sheet.format("C:E", formatter_options=float_formatter(), decimals=4)
        self.t_result_sheet.headers(tab_result_heading)
        self.t_result_sheet.set_all_column_widths(65)

        self.btn_save_result = ttk.Button(master=frm_result_table, text="Save Calibration", width=35,
                                          command=self.save_calibration_results, state="disabled")
        self.btn_save_result.place(x=10, y=210)

        self.fig = Figure(figsize=(880/screen_dpi, 500/screen_dpi), dpi=screen_dpi, tight_layout = True)
        G_Plots = self.fig.subplots(2, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().place(x=370, y=80)

        # Toolbar #########
        toolbar_frame = ttk.Frame(master=self, width=1050, style="secondary.TFrame")
        toolbar_frame.place(x=370, y=700)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.update_plots()
        self.update()

    def update_plots(self):

        global G_Plots, Static_States, Highlight_State, MetaData
        G_Plots[0].clear()

        lines = []
        ymin = 10
        ymax = 0

        for PlotIdx in range(0, MaxJUT_Channels):
            ch_tsp = "TSP{Ch}".format(Ch=PlotIdx)
            if ch_tsp in self.utta_data.meta_data.Channels:
                if self.utta_data.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                    line, = G_Plots[0].plot(self.utta_data.timebase_int, self.utta_data.adc_int[PlotIdx, :], label=self.utta_data.meta_data.Channels[ch_tsp]["Name"])
                    lines.append(line)
                    ymin = np.min([ymin, np.min(self.utta_data.adc_int[PlotIdx, :])])
                    ymax = np.max([ymax, np.max(self.utta_data.adc_int[PlotIdx, :])])

        G_Plots[0].set_xlabel("Time / [s]")
        G_Plots[0].set_ylabel("Diode Voltage / [V]")
        G_Plots[0].set_xlim(left=0)
        G_Plots[0].callbacks.connect('xlim_changed', self.on_xlims_change)
        G_Plots[0].grid(True)

        if len(self.utta_data.adc_int) > 0:
            G_Plots[0].legend(loc="lower left")
            G_Plots[0].set_ylim([ymin - (ymax - ymin)*0.05 , ymax + (ymax - ymin)*0.05])

        G_Plots[1].clear()

        ymin = 100
        ymax = -100

        if len(self.utta_data.adc_int) > 0:
            for PlotIdx in range(1):
                G_Plots[1].plot(self.utta_data.timebase_int, self.utta_data.adc_int[PlotIdx, :], label="TC " + str(PlotIdx))

                ymin = np.min([ymin, np.min(self.utta_data.adc_int[PlotIdx, :])])
                ymax = np.max([ymax, np.max(self.utta_data.adc_int[PlotIdx, :])])

            G_Plots[1].set_xlim(left=0)
            G_Plots[1].legend(loc="lower left")
            G_Plots[1].set_ylim([ymin - (ymax - ymin) * 0.05, ymax + (ymax - ymin) * 0.05])
            G_Plots[1].grid(True)

        G_Plots[1].set_xlabel("Time / [s]")
        G_Plots[1].set_ylabel("Temperature / [°C]")
        tbl = self.t_step_sheet.data
        self.canvas.draw()

        if len(tbl) >= 1:
            self.btn_rem_steps.configure(state='normal')

            times = np.transpose([np.array(self.t_step_sheet.get_column_data(5), dtype=np.float32), # starttime
                                  np.array(self.t_step_sheet.get_column_data(6), dtype=np.float32), # endtime
                                  np.array(self.t_step_sheet.get_column_data(0), dtype=np.float32)]) # temperature

            ylims = G_Plots[0].axes.get_ylim()
            ypos = ylims[0] + (ylims[1] - ylims[0]) * 0.05
            for idx, stat_state in enumerate(times):
                # Highlight_State
                if idx == Highlight_State:
                    bar_color = 'orange'
                else:
                    bar_color = 'green'

                G_Plots[1].fill_between(self.utta_data.timebase_int, 0, 1,
                                        where=np.logical_and((stat_state[0] <= self.utta_data.timebase_int), (stat_state[1] >= self.utta_data.timebase_int)),
                                        color=bar_color, alpha=0.5,
                                        transform=G_Plots[1].get_xaxis_transform())
                G_Plots[0].fill_between(self.utta_data.timebase_int, 0, 1,
                                        where=np.logical_and((stat_state[0] <= self.utta_data.timebase_int), (stat_state[1] >= self.utta_data.timebase_int)),
                                        color=bar_color, alpha=0.5,
                                        transform=G_Plots[0].get_xaxis_transform())

                G_Plots[0].text((stat_state[0]+stat_state[1])/2, ypos, "{temp:.1f}°C".format(temp=stat_state[2]), ha="center", va="center")

        else:
            self.btn_rem_steps.configure(state='disabled')

        if len(tbl) >= 2:
            self.btn_calc_steps.configure(state='normal')
        else:
            self.btn_calc_steps.configure(state='disabled')

        self.canvas.draw()

    def save_calibration_results(self):

        cal_file_name = udpc.select_file("Select the measurement file",
                                                     (('uTTA Calibration Files', '*.ucf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        cfile, data_file_no_ext, file_path = udpc.split_file_path(cal_file_name)
        if len(cal_file_name) > 0:  # check if string is not empty
            tsp_cal_value = {}

            for ChIdx in range(0, 4):  # iterate through all the 4 channels viewed
                tsp_name = self.t_result_sheet.get_cell_data(ChIdx, 0)
                if tsp_name != "OFF":
                    abort_save = False

                    tsp_offs = self.t_result_sheet.get_cell_data(ChIdx, 1)
                    tsp_lin = self.t_result_sheet.get_cell_data(ChIdx, 2)
                    tsp_quad = self.t_result_sheet.get_cell_data(ChIdx, 3)
                    r_sq = self.t_result_sheet.get_cell_data(ChIdx, 4)
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

                        if str(tsp_name).startswith("TC"):
                            chan_prefix = "$TC_"
                        else:
                            chan_prefix = "$CHAN_"

                        tsp_cal_value = {str(chan_prefix + tsp_name): {
                                            "Offset" : tsp_offs,
                                            "LinGain": tsp_lin,
                                            "QuadGain": tsp_quad,
                                            "CalStatus": 1
                                        }}

                        udpc.write_tsp_cal_to_file(cal_file_name, tsp_cal_value)
                        self.lbl_helpbar.configure(text="Successfully saved calibration of channel " + tsp_name + " to file: " + data_file_no_ext,
                                                   style='success.Inverse.TLabel')
                        self.frm_help_bar.configure(style='success.Inverse.TLabel')
                    else:
                        self.lbl_helpbar.configure(text="Aborted saving calibration of channel " + tsp_name + "because of bad convergence",
                                                   style='warning.Inverse.TLabel')
                        self.frm_help_bar.configure(style='warning.Inverse.TLabel')
        else:
            self.lbl_helpbar.configure(text="File: " + DataFile + " was not imported.", style='warning.Inverse.TLabel')
            self.frm_help_bar.configure(style='warning.Inverse.TLabel')

    def read_measurement_file_callback(self):
        global DataFile, Static_States, MetaData
        measfilename = udpc.select_file("Select the measurement file",
                                                    (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        if len(measfilename) > 0:    # check if string is not empty
            DataFile, data_file_no_ext, file_path = udpc.split_file_path(measfilename)
            self.utta_data.import_data(measfilename)
            #tb_import, adc_import, tc_import, MetaData = uTTA_data_import.read_measurement_file(measfilename, 0)

            if self.utta_data.meta_data.FlagTSPCalibrationFile:
                self.utta_data.interpolate_to_common_timebase()
                #self.utta_data.timebase_int, self.utta_data.adc_int, Temp = uTTA_data_processing.interpolate_to_common_timebase(tb_import, adc_import, tc_import)

                # look for periods of at least 5 minutes (300 samples) where the temperature changes less than +/-0.7°C
                # Static_States = uTTA_data_processing.find_static_states(Temp[0, :], 0.7, 200)
                Static_States = udpc.find_static_states(self.utta_data.adc_int[0, :], 0.0008, 500)

                if Static_States:
                    for stat_state in Static_States:
                        # for the temperature average take only the last 60 samples (1Minute) for the average
                        t_avg = np.mean(self.utta_data.tc_int[0, (stat_state[1]-60):stat_state[1]])
                        self.add_cal_step_entry(stat_state[1]-60, stat_state[1], t_avg)

                self.update_plots()

                self.btn_add_steps.configure(state='normal')
                self.lbl_helpbar.configure(text="File: " + DataFile + " was successfully imported.\nNow click on the magnifying glass below the plot and select "+
                                           "the first horizontal section in the upper plot.",
                                           style='info.Inverse.TLabel')
                self.frm_help_bar.configure(style='info.Inverse.TLabel')
            else:
                self.lbl_helpbar.configure(text="Seems like : " + DataFile + " is not a calibration measurement. Therefore the measurement was not imported.",
                                           style='warning.Inverse.TLabel')
                self.frm_help_bar.configure(style='warning.Inverse.TLabel')
        else:
            self.lbl_helpbar.configure(text="File: " + DataFile + " was not imported.", style='danger.Inverse.TLabel')
            self.frm_help_bar.configure(style='danger.Inverse.TLabel')

    def add_calibration_step(self):
        cal_range = G_Plots[0].get_xlim()

        t_step = self.ent_step_temp.get()

        if len(t_step) > 2:
            t_step = float(t_step.replace(",", "."))

            xstart = int(cal_range[0])
            xend = int(cal_range[1])

            self.add_cal_step_entry(xstart, xend, t_step)

            self.ent_step_temp.delete(0, 'end')
            self.update_plots()

            tbl = self.t_step_sheet.data
            if len(tbl) >= 2:  # above two selected points the interpolation calculation ca begin
                self.lbl_helpbar.configure(text="Repeat the selection process with the next temperature step, "
                                                + "or press 'Save Calibration' to complete the process.")
            else:
                self.lbl_helpbar.configure(text="Repeat the selection process with the next temperature step")

    def add_cal_step_entry(self, starttime, endtime, temp_step):
        self.t_step_sheet.insert_row(idx=0)
        self.t_step_sheet["A1"].data = float(temp_step)
        self.t_step_sheet["B1"].data = np.mean(self.utta_data.adc_int[0, starttime:endtime])
        self.t_step_sheet["C1"].data = np.mean(self.utta_data.adc_int[1, starttime:endtime])
        self.t_step_sheet["D1"].data = np.mean(self.utta_data.adc_int[2, starttime:endtime])
        self.t_step_sheet["E1"].data = np.mean(self.utta_data.adc_int[0, starttime:endtime])
        self.t_step_sheet["F1"].data = starttime
        self.t_step_sheet["G1"].data = endtime

    def remove_calibration_step(self):

        tbl = self.t_step_sheet
        for box in tbl.get_all_selection_boxes():
            row_number = tbl.datarn(box.from_r)

        tbl.delete_row(row_number)
        self.update_plots()

    def on_cell_select(self, event):
        global Highlight_State
        content = event["selected"]
        Highlight_State = content.row
        # print("Cell Selected in row {row}".format(row=Highlight_State))
        self.update_plots()

    def fit_temp_steps(self):

        global InterpolationDegrees

        self.update_plots()
        tbl = self.t_step_sheet.data
        if len(tbl) >= 2:  # above two selected points the interpolation calculation ca begin

            for ChIdx in range(0, 3):  # iterate through all the 4 channels viewed
                ch_tsp = "TSP{Ch}".format(Ch=ChIdx)
                x_data = np.array(self.t_step_sheet.get_column_data(0), dtype=np.float32)

                y_data = np.array(self.t_step_sheet.get_column_data(ChIdx + 1), dtype=np.float32)

                p_fit = np.polyfit(x_data, y_data, InterpolationDegrees)

                if InterpolationDegrees == 1:
                    p_fit = np.insert(p_fit, 0, 0.0)

                [quad, slope, offs] = p_fit

                if abs(slope) > 0.00001:
                    y_fit = offs + slope * x_data + quad * x_data * x_data
                    corr_mat = np.corrcoef(y_data, y_fit)
                    corr = corr_mat[0, 1]
                    r_sq = corr ** 2
                else:
                    r_sq = 1.0
                print("Fitting Channel {Ch} with quadratic interpolation: Offset: {Offs:.4f} ,Linear: {Lin:.4f}, Quad: {Quad:.7f}, R²: {Rsq:.4f}".format(
                     Ch=ChIdx, Lin=slope, Offs=offs, Quad=quad, Rsq=r_sq))
                if ChIdx < 3:
                    self.t_result_sheet.set_cell_data(r=ChIdx, c=0, value=MetaData[ch_tsp]["Name"])
                # else:
                    #self.t_result_sheet.set_cell_data(r=ChIdx, c=0, value="TC0")
                self.t_result_sheet.set_cell_data(r=ChIdx, c=1, value=offs)
                self.t_result_sheet.set_cell_data(r=ChIdx, c=2, value=slope)
                self.t_result_sheet.set_cell_data(r=ChIdx, c=3, value=quad)
                self.t_result_sheet.set_cell_data(r=ChIdx, c=4, value=r_sq)

            self.btn_save_result.configure(state='normal')

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.destroy()

    def on_xlims_change(self, event_ax):
        global G_Plots, MetaData
        x_limits = event_ax.get_xlim()
        xlim_min = int(x_limits[0])
        xlim_max = int(x_limits[1])
        # print("updated xlims: ", event_ax.get_xlim())
        G_Plots[1].set_xlim(left=x_limits[0], right=x_limits[1])
        ymin = np.min(self.utta_data.adc_int[0, xlim_min:xlim_max])
        ymax = np.max(self.utta_data.adc_int[0, xlim_min:xlim_max])
        G_Plots[1].set_ylim(bottom=ymin, top=ymax)

        tsp_min = np.min(self.utta_data.adc_int[0, xlim_min:xlim_max])
        tsp_max = np.max(self.utta_data.adc_int[0, xlim_min:xlim_max])
        tsp_pp = Quantity(tsp_max-tsp_min, "V")

        self.ent_step_temp.delete(0, 'end')
        self.ent_step_temp.insert(0, "{:.2f}".format(np.mean(self.utta_data.adc_int[0, xlim_min:xlim_max])))

        self.lbl_helpbar.configure(text="Zoom into the measurement until the whole plot is filled with the steady state.\n" +
                                   "Peak-to-peak spread of " + MetaData["TSP0"]["Name"] + " is {tsp_mm}. ".format(tsp_mm=tsp_pp) +
                                   "\nWhen you are satisfied enter the step temperature and click on 'Add Step'", style='info.Inverse.TLabel')
        self.frm_help_bar.configure(style='info.TFrame')


# Declare and register callbacks


app = CalApp()

app.mainloop()
