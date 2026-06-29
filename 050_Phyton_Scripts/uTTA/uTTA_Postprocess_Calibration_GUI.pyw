#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    uTTA_Postprocess_Calibration_GUI.pyw
Description:    GUI for postprocessing TSP calibration measurements.
                Features:
                - Import of uTTA measurement files including automatic scaling
                - Interpolation of thermocouples and TSPs to a common time base
                - Automatic detection of steady state regions for identification of valid points for TSP parameter interpolation
                - Manual identification of steady state regions for TSP parameter interpolation
                - TSP parameter interpolation. User selectable as pure linear or quadratic interpolation
                - Save calibration results to existing calibration file
                - Load and Save last GUI settings when the application is opened/closed

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

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # type: ignore # matplotlib 3.9.2
from matplotlib.figure import Figure  
from tksheet import (Sheet, float_formatter, num2alpha, formatter)
from quantiphy import Quantity      
from typing import Any, Callable
import os
import configparser
import library.uTTA_data_processing as udpc
import numpy as np                  
import matplotlib 
import tkinter as tk  
from tkinter import messagebox               
import ttkbootstrap as ttk

matplotlib.use("TkAgg")

MaxJUT_Channels = 3

WINDOW_WIDTH = 1580
WINDOW_HEIGHT = 960

# Define a Type Alias for clarity
TksheetFormatterInstance = Any

# ==============================================================================
# Quantiphy Formatting Logic
# ==============================================================================

def convert_SI_to_float(val: Any, **kwargs: Any) -> float:
    """Cleans German local decimal commas and converts the value to a standard float.
    
    This ensures that inputs like "1.500,5" or "12,34" don't crash the parser.
    """
    if isinstance(val, (int, float)):
        return float(val)
        
    if val is None or str(val).strip() == "":
        raise ValueError("Empty cell")

    val_str = str(val).strip()
    
    # Case 1: Thousands separator as "." and "," as decimal point (e.g. 1.500,50)
    if "." in val_str and "," in val_str:
        val_str = val_str.replace(".", "")   # remove thousands separators
        val_str = val_str.replace(",", ".")   # Convert comma to point
    # Case 2: Only decimal comma (e.g. 12,34)
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
        
    return float(val_str)


def create_quantiphy_to_str(unit: str = "") -> Any:
    """ Factory that returns a string-formatting function bound to a specific unit.
    """
    def to_str_function(val: Any, **kwargs: Any) -> str:
        if val is None or val == "":
            return ""
        try:
            # Create the pyhsical object
            q = Quantity(float(val), unit)
            
            # prec=3 -> 3 decimal digits
            return q.render(prec=3)
            
        except (ValueError, TypeError):
            return str(val)

    return to_str_function


def create_si_formatter(unit: str = "") -> TksheetFormatterInstance:
    """ Creates a tksheet generic formatter instance configured for SI units.
    """
    return formatter(
        datatypes=(int, float),
        format_function=convert_SI_to_float,
        to_str_function=create_quantiphy_to_str(unit),
        nullable=True,
        invalid_value="NaN",
    )


class CalApp(ttk.Window):
    def __init__(self):
        """Initialize the application, load settings from last session and build the GUI
        """        
        super().__init__()

        self.title("uTTA Calibration Factor Calculation Tool")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        screen_dpi = self.winfo_fpixels('1i')
        geometry = self.winfo_geometry()
        print("DPI: " + str(screen_dpi) + " Geometry: " + str(geometry))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        self.utta_data = udpc.UttaZthProcessing()
        fileext = __file__.split(".")[-1]
        self.ini_filename = __file__.replace(fileext, "ini")

        self.Interpolation_Degrees = tk.IntVar()
        self.steady_state_min_duration = tk.DoubleVar()
        self.steady_state_max_pp_diode = tk.DoubleVar()
        self.steady_state_max_pp_tc_k = tk.DoubleVar()

        self.load_settings()

        self.meas_file_path:str = ''
        self.g_plots:list = []
        self.detected_static_states = []
        self.highlight_static_state:int = -1

        self.paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # LEFT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#

        self.frm_left = ttk.Frame(self.paned)
        self.frm_left.pack(fill=tk.X, padx=5, pady=5)

        self.tabs = ttk.Notebook(master=self.frm_left)
        self.tabs.pack(fill=tk.BOTH, padx=5, pady=5)

        # 1st Page: Calibration
        self.frm_calibration = ttk.Frame(master=self)
        self.frm_calibration.pack(fill=tk.BOTH, padx=10, pady=10)
        self.tabs.add(self.frm_calibration, text="Calibration")

        self.frm_file_btns = ttk.Frame(master=self.frm_calibration)
        self.frm_file_btns.pack(fill=tk.X, padx=5, pady=5)

        self.btn_measure_file = ttk.Button(master=self.frm_file_btns, text="Measurement File",
                                           command=self.read_measurement_file_callback, width=14)
        self.btn_measure_file.pack(fill=tk.X, padx=5, pady=5)

        frm_step_table = ttk.Labelframe(master=self.frm_calibration,text="Calibration Temperature Steps")
        frm_step_table.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(master=frm_step_table, text="Step Temp:", 
                 justify="right").grid(row=0, column=0, sticky="e")
    
        self.ent_step_temp = ttk.Entry(master=frm_step_table, justify="right", width=8)
        self.ent_step_temp.insert(-1, "°C")
        self.ent_step_temp.grid(row = 0, column=1, sticky='ew', padx=5, pady=5)

        self.btn_add_steps = ttk.Button(master=frm_step_table, text="Add Step", width=12,
                                        command=self.add_calibration_step, state="disabled")
        self.btn_add_steps.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

        self.btn_rem_steps = ttk.Button(master=frm_step_table, text="Remove Step", width=12,
                                        command=self.remove_calibration_step)
        self.btn_rem_steps.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        self.btn_calc_steps = ttk.Button(master=frm_step_table, text="Recalculate",
                                         command=self.fit_temp_steps, state="disabled")
        self.btn_calc_steps.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

        self.btn_auto_detects = ttk.Button(master=frm_step_table, text="Auto-Detect",
                                         command=self.auto_detect_steady_states, state="disabled")
        self.btn_auto_detects.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

        tab_heading = ["Step Temp", "CH0 Avg.", "CH1 Avg.", "CH2 Avg.", "Temp Avg.", "Start", "End"]
        self.t_step_sheet = Sheet(frm_step_table, startup_select=(0, 1, "rows"),
                                  page_up_down_select_row=True)

        self.t_step_sheet['A'].format(create_si_formatter('°C'))
        self.t_step_sheet['B:D'].format(create_si_formatter('V'))
        self.t_step_sheet['E'].format(create_si_formatter('°C'))

        self.t_step_sheet.grid(row=3, column=0, columnspan=2)
        self.t_step_sheet.enable_bindings(('single_select', 'edit_cell')) # type: ignore
        self.t_step_sheet.extra_bindings("cell_select", self.on_cell_select)
        self.t_step_sheet.headers(tab_heading)
        self.t_step_sheet.set_all_column_widths(55)

        frm_result_table = ttk.Labelframe(master=self.frm_calibration, text="Linearization Results")
        frm_result_table.pack(fill=tk.BOTH, padx=5, pady=5)

        tab_result_heading = ["Channel", "Offset", "Lin.", "Quad.", "R²"]
        self.t_result_sheet = Sheet(frm_result_table, show_y_scrollbar=False, row_index_width=30)
        self.t_result_sheet.grid(row=1, rowspan=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.t_result_sheet.insert_columns(columns=4)
        self.t_result_sheet.insert_rows(rows=3)
        self.t_result_sheet.enable_bindings()
        self.t_result_sheet.sheet_data_dimensions(total_rows=4, total_columns=4)
        self.t_result_sheet['B'].format(create_si_formatter('V'))
        self.t_result_sheet['C'].format(create_si_formatter('V/K'))
        self.t_result_sheet['D'].format(create_si_formatter('V²/K'))
        self.t_result_sheet['E'].format(create_si_formatter(''))
 
        self.t_result_sheet.headers(tab_result_heading)
        self.t_result_sheet.set_all_column_widths(70)

        self.btn_save_result = ttk.Button(master=frm_result_table, text="Save Calibration", width=12,
                                          command=self.save_calibration_results, state="disabled")
        self.btn_save_result.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # 2nd Page: Settings
        self.frm_settings = ttk.Frame(master=self)
        self.frm_settings.pack(fill=tk.BOTH, padx=5, pady=5)
        self.tabs.add(self.frm_settings, text="Settings")

        self.frm_set_interp = ttk.Labelframe(master=self.frm_settings, text='Interpolation')
        self.frm_set_interp.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(master=self.frm_set_interp, text='Polynomial Degrees', anchor='e', width=26).grid(row=0, column=0, padx=5, pady=5)
        self.sb_interp_degrees = ttk.Spinbox(master=self.frm_set_interp, from_=1, to=2, textvariable=self.Interpolation_Degrees , width=7)
        self.sb_interp_degrees.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.frm_steady_state = ttk.Labelframe(master=self.frm_settings, text='Steady State Detection')
        self.frm_steady_state.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(master=self.frm_steady_state, text='Minimum Steady Time', anchor='e', width=26).grid(row=0, column=0, padx=5, pady=5)
        self.sb_min_steady_time = ttk.Spinbox(master=self.frm_steady_state, from_=30.0, to=1000.0, increment=0.5, textvariable=self.steady_state_min_duration , width=7, justify='right')
        self.sb_min_steady_time.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(master=self.frm_steady_state, text='s', anchor='w', width=3).grid(row=0, column=2, padx=2, pady=5)

        ttk.Label(master=self.frm_steady_state, text='Max. Voltage P-P Deviation', anchor='e', width=26).grid(row=1, column=0, padx=5, pady=5)
        self.sb_max_diode_pp = ttk.Spinbox(master=self.frm_steady_state, from_=0.01, to=10.0, increment=0.01, textvariable=self.steady_state_max_pp_diode , width=7, justify='right')
        self.sb_max_diode_pp.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(master=self.frm_steady_state, text='mV', anchor='w', width=3).grid(row=1, column=2, padx=2, pady=5)

        ttk.Label(master=self.frm_steady_state, text='Max. Temperature Deviation', anchor='e', width=26).grid(row=2, column=0, padx=5, pady=5)
        self.sb_max_tck_pp = ttk.Spinbox(master=self.frm_steady_state, from_=0.05, to=5.0, increment=0.05, textvariable=self.steady_state_max_pp_tc_k , width=7, justify='right')
        self.sb_max_tck_pp.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(master=self.frm_steady_state, text='°C', anchor='w', width=3).grid(row=2, column=2, padx=2, pady=5)

        self.paned.add(self.frm_left)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # RIGHT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#

        self.frm_right = ttk.Frame(self.paned)
        self.frm_right.pack(fill=tk.X, padx=5, pady=5)

        self.lbl_helpbar = ttk.Label(master=self.frm_right, style='info.Inverse.TLabel', wraplength=1080)
        self.lbl_helpbar.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_helpbar.configure(text="Welcome to the TSP Calibration Postprocessing GUI. Click 'Measurement File' and import a calibration measurement")

        matplotlib.rcParams['axes.labelsize'] = 7
        matplotlib.rcParams['legend.fontsize'] = 7
        matplotlib.rcParams['font.size'] = 11
        matplotlib.rcParams['xtick.labelsize'] = 7
        matplotlib.rcParams['ytick.labelsize'] = 7

        # Plot Area
        self.frm_plot_area = ttk.Frame(master=self.frm_right)
        self.frm_plot_area.pack(fill=tk.BOTH, padx=5, pady=5)

        self.fig = Figure(figsize=(1430/screen_dpi, 770/screen_dpi), dpi=96, tight_layout = True)
        self.g_plots = self.fig.subplots(2, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, padx=10, pady=10)
        self.canvas.draw()

        # Toolbar #########
        toolbar_frame = ttk.Frame(master=self.frm_right, style="secondary.TFrame")
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.paned.add(self.frm_right)

        self.update_plots()
        self.update()

    def load_settings(self):
            """Loads GUI settings from the ini-File into the class itself
            """        

            if os.path.isfile(self.ini_filename):        # check if the config file exists
                config = configparser.ConfigParser()
                config.optionxform = str  # type: ignore # set configparser to Case-Sensitive
                config.read_file(open(self.ini_filename))

                self.Interpolation_Degrees.set(int(config.get("Settings", "Interpolation_Degrees", fallback='1')))

                self.steady_state_min_duration.set(float(config.get("Steady_State_Detection", "Min_Duration", fallback='500.0')))
                self.steady_state_max_pp_diode.set(float(config.get("Steady_State_Detection", "Max_PP_Diode", fallback='0.0008')))
                self.steady_state_max_pp_tc_k.set(float(config.get("Steady_State_Detection", "Max_PP_TCK", fallback='1.55')))

    def save_settings(self):
        """Saves the current GUI settings into an ini-file with the same name as the GUI.
        """        
        config = configparser.ConfigParser()
        config.optionxform = str  # type: ignore # set configparser to Case-Sensitive
        config.add_section("Settings")
        config.set("Settings", "Interpolation_Degrees", value=str(self.Interpolation_Degrees.get()))

        config.add_section('Steady_State_Detection')
        config.set("Steady_State_Detection", "Min_Duration", value=str(self.steady_state_min_duration.get()))
        config.set("Steady_State_Detection", "Max_PP_Diode", value=str(self.steady_state_max_pp_diode.get()))
        config.set("Steady_State_Detection", "Max_PP_TCK", value=str(self.steady_state_max_pp_tc_k.get()))

        with open(self.ini_filename, 'w') as configfile:
            config.write(configfile)

    def update_plots(self):
        """Updates all plots with fresh data.
        Adds highlighted areas where steady state regions were marked.
        """        

        if len(self.g_plots) == 0 :
            return

        self.g_plots[0].clear()

        lines = []
        ymin = 10
        ymax = 0

        for PlotIdx in range(0, MaxJUT_Channels):
            ch_tsp = f"TSP{PlotIdx}"
            if ch_tsp in self.utta_data.meta_data.Channels:
                if self.utta_data.meta_data.Channels[ch_tsp]["Name"] != "OFF":
                    line, = self.g_plots[0].plot(self.utta_data.time_interp, self.utta_data.adc_interp[PlotIdx, :], label=self.utta_data.meta_data.Channels[ch_tsp]["Name"]) # type: ignore
                    lines.append(line)
                    ymin = np.min([ymin, np.min(self.utta_data.adc_interp[PlotIdx, :])]) # type: ignore
                    ymax = np.max([ymax, np.max(self.utta_data.adc_interp[PlotIdx, :])]) # type: ignore

        self.g_plots[0].set_xlabel("Time / [s]")
        self.g_plots[0].set_ylabel("Diode Voltage / [V]")
        self.g_plots[0].set_xlim(left=0)
        self.g_plots[0].callbacks.connect('xlim_changed', self.on_xlims_change)
        self.g_plots[0].grid(True)

        if len(self.utta_data.adc_interp) > 0:
            self.g_plots[0].legend(loc="lower left")
            self.g_plots[0].set_ylim([ymin - (ymax - ymin)*0.05 , ymax + (ymax - ymin)*0.05])

        self.g_plots[1].clear()

        ymin = 100
        ymax = -100

        if len(self.utta_data.adc_interp) > 0:
            for PlotIdx in range(1):
                self.g_plots[1].plot(self.utta_data.time_interp, self.utta_data.tc_interp[PlotIdx, :], label="TC " + str(PlotIdx)) # type: ignore

                ymin = np.min([ymin, np.min(self.utta_data.tc_interp[PlotIdx, :])]) # type: ignore
                ymax = np.max([ymax, np.max(self.utta_data.tc_interp[PlotIdx, :])]) # type: ignore

            self.g_plots[1].set_xlim(left=0)
            self.g_plots[1].legend(loc="lower left")
            self.g_plots[1].set_ylim([ymin - (ymax - ymin) * 0.05, ymax + (ymax - ymin) * 0.05])
            self.g_plots[1].grid(True)

        self.g_plots[1].set_xlabel("Time / [s]")
        self.g_plots[1].set_ylabel("Temperature / [°C]")
        tbl = self.t_step_sheet.data
        self.canvas.draw()

        if len(tbl) >= 1:
            self.btn_rem_steps.configure(state='normal')

            times = np.transpose([np.array(self.t_step_sheet.get_column_data(5), dtype=np.float32), # starttime
                                  np.array(self.t_step_sheet.get_column_data(6), dtype=np.float32), # endtime
                                  np.array(self.t_step_sheet.get_column_data(0), dtype=np.float32)]) # temperature

            ylims = self.g_plots[0].axes.get_ylim()
            ypos = ylims[0] + (ylims[1] - ylims[0]) * 0.05
            for idx, stat_state in enumerate(times):
                # Highlight_State
                if idx == self.highlight_static_state:
                    bar_color = 'orange'
                else:
                    bar_color = 'green'

                self.g_plots[1].fill_between(self.utta_data.time_interp, 0, 1,
                                        where=np.logical_and((stat_state[0] <= self.utta_data.time_interp), (stat_state[1] >= self.utta_data.time_interp)),
                                        color=bar_color, alpha=0.5,
                                        transform=self.g_plots[1].get_xaxis_transform())
                self.g_plots[0].fill_between(self.utta_data.time_interp, 0, 1,
                                        where=np.logical_and((stat_state[0] <= self.utta_data.time_interp), (stat_state[1] >= self.utta_data.time_interp)),
                                        color=bar_color, alpha=0.5,
                                        transform=self.g_plots[0].get_xaxis_transform())

                self.g_plots[0].text((stat_state[0]+stat_state[1])/2, ypos, f"{stat_state[2]:.1f}°C", ha="center", va="center", size=7)

        else:
            self.btn_rem_steps.configure(state='disabled')

        if len(tbl) >= 2:
            self.btn_calc_steps.configure(state='normal')
        else:
            self.btn_calc_steps.configure(state='disabled')

        self.canvas.draw()

    def save_calibration_results(self):
        """Saves calibration results to an existing *.ucf calibration file
        """        

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
                        msg_box = messagebox.askquestion("Low confidence results",
                                                            f"The R² of channel '{tsp_name}'only {np.min(r_sq):.3f}" +
                                                            ", this seems to low to provide a good calibration.\n" +
                                                            "Do you wish to continue anyway?", icon="warning", )
                        if msg_box != "yes":
                            abort_save = True
                    if not abort_save:
                        print(f"Creating Cal Entry for Channel {ChIdx}, Name: {tsp_name}, Offset {tsp_offs:.4f}, Gain {tsp_lin:.4f}")

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
                        
                    else:
                        self.lbl_helpbar.configure(text="Aborted saving calibration of channel " + tsp_name + "because of bad convergence",
                                                   style='warning.Inverse.TLabel')
                        
        else:
            self.lbl_helpbar.configure(text="File: " + self.meas_file_path + " was not imported.", style='warning.Inverse.TLabel')

    def read_measurement_file_callback(self):
        """Callback function triggered by the Open Measurement button.
        - Loads a full measurement file into the GUI
        - Interpolates TSP voltages and thermocouples to a common timebase
        - searches for steady state temperatures and TSP voltages to find viable calibration points
        """        
        measfilename = udpc.select_file("Select the measurement file",
                                                    (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        if len(measfilename) > 0:    # check if string is not empty
            self.meas_file_path, data_file_no_ext, file_path = udpc.split_file_path(measfilename)
            self.utta_data.import_data(measfilename)
            
            self.detected_static_states = []
            self.highlight_static_state = -1

            if self.utta_data.meta_data.FlagTSPCalibrationFile:
                self.utta_data.interpolate_to_common_timebase()

                self.auto_detect_steady_states()

                self.btn_add_steps.configure(state='normal')
                self.btn_auto_detects.configure(state='normal')
                self.lbl_helpbar.configure(text=f"File: {self.meas_file_path} was successfully imported.\nNow click on the magnifying glass below the plot and select "+
                                           "the first horizontal section in the upper plot.",
                                           style='info.Inverse.TLabel')
                
            else:
                self.lbl_helpbar.configure(text=f"Seems like : {self.meas_file_path} is not a calibration measurement. Therefore the measurement was not imported.",
                                           style='warning.Inverse.TLabel')
                self.btn_add_steps.configure(state='disabled')
                self.btn_auto_detects.configure(state='disabled')
        else:
            self.lbl_helpbar.configure(text=f"File: {self.meas_file_path} was not imported.", style='danger.Inverse.TLabel')
            
    def auto_detect_steady_states(self) -> None:
        """Automatically detects steady state regions in TSP and thermocouple data. At first
        steady state regions are detected for voltage and temperature separately.
        After detection the detection the TSP voltage regions are shrunk down to a 60 seconds window
        in the middle of the detected area (aiming to get even more stable resilts).
        Next it is checked that this window fits into one of the found temperature regions.
        Otherwise the area is discarded.
        """        

        if self.utta_data.flag_import_successful:

            max_dev = float(self.steady_state_max_pp_diode.get())/1000.0
            max_tc_dev = float(self.steady_state_max_pp_tc_k.get())
            t_steady = int(self.steady_state_min_duration.get())
            # Check for regions where the TSP value is stable within a certain range for a given time. The do the same with the thermocouples
            self.detected_static_states = udpc.find_static_states(self.utta_data.adc_interp[0, :], max_dev, t_steady) # type: ignore
            tc_static_states = udpc.find_static_states(self.utta_data.tc_interp[0, :], max_tc_dev, t_steady) # type: ignore

            #print(f"TC Static States: {tc_static_states}")
            # After finding areas for TSP and thermocouple these regions are crosschecked to make sure the areas overlap.
            # Non overlapping areas are discarded
            if self.detected_static_states:
                for stat_state in self.detected_static_states:
                    # calculate the temperature average for the center 60s of the found data
                    idx_center = int(sum(stat_state)/2) -30  # calculated the most central index of the found range and subtract 30 seconds

                    for tc_static in tc_static_states:
                        if tc_static[0] < idx_center and tc_static[1]> idx_center+60:
                            t_avg = np.mean(self.utta_data.tc_interp[0, idx_center:idx_center+60]) # type: ignore
                            self.add_cal_step_entry(idx_center, idx_center+60, float(t_avg))
                            break
                    
            self.update_plots()

    def add_calibration_step(self) -> None:
        """Adds a new calibration step to the table and the plot
        """        
        cal_range = self.g_plots[0].get_xlim()

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

    def add_cal_step_entry(self, starttime:int, endtime:int, temp_step:float) -> None:
        """Adds a new calibration step as entry to the step table.
        Start and Endtime are baiscally the indexes of the samples

        Args:
            starttime (int): Start time ne new area starts
            endtime (int): End time the new area ends
            temp_step (float): The average thermocouple temperature calculated for this step
        """             
        self.t_step_sheet.insert_row(idx=0)
        self.t_step_sheet["A1"].data = float(temp_step)
        self.t_step_sheet["B1"].data = np.mean(self.utta_data.adc_interp[0, starttime:endtime]) # type: ignore
        self.t_step_sheet["C1"].data = np.mean(self.utta_data.adc_interp[1, starttime:endtime]) # type: ignore
        self.t_step_sheet["D1"].data = np.mean(self.utta_data.adc_interp[2, starttime:endtime]) # type: ignore
        self.t_step_sheet["E1"].data = np.mean(self.utta_data.tc_interp[0, starttime:endtime]) # type: ignore
        self.t_step_sheet["F1"].data = starttime
        self.t_step_sheet["G1"].data = endtime

        self.consolidate_cal_step_entries()

    def consolidate_cal_step_entries(self):
        """Runs through the found calibraion steps and removes redundant entries.
        Furthermore, entries which intersect are merged to one entry.
        """

        tbl = self.t_step_sheet.data

        if not tbl: # just in case the table is empty
            return
        
        # Sort the table by start time (column index 5)
        # This way the overlapping intervall are next to each other.
        sorted_data = sorted(tbl, key=lambda x: x[5])

        # Initialisation with the first intervall
        # Saved values: [[Summe_der_Werte], Start, End, , Number of values]
        current_start = sorted_data[0][5+0]
        current_end = sorted_data[0][5+1]
        current_value_sum = sorted_data[0][0:5]
        current_count = 1

        merged = []

        for i in range(1, len(sorted_data)):
            next_start= sorted_data[i][5+0]
            next_end  = sorted_data[i][5+1]
            next_value = sorted_data[i][0:5]

            # Check if the next intervall overlaps the the current one
            if next_start <= current_end:

                # Update the enttime (in case the new intervall reaches further than the old one)
                current_end = max(current_end, next_end)
                # Sum the values for each column for the later averaging
                current_value_sum = [sum(x) for x in zip(current_value_sum, next_value)]
                current_count += 1
            else:
                # No overlap -> close the old intervall and calculate the average
                mean_value = [x/current_count for x in current_value_sum]
                mean_value.extend([current_start, current_end])
                merged.append(mean_value)
                
                # Get the next intervall as basis for the next step
                current_start = next_start
                current_end = next_end
                current_value_sum = next_value
                current_count = 1

        # # Add the last remaining intervall
        mean_value = [x/current_count for x in current_value_sum]    
        mean_value.extend([current_start, current_end])
        merged.append(mean_value)

        self.t_step_sheet.set_sheet_data(data=merged, redraw=True)
        self.t_step_sheet.set_sheet_data_and_display_dimensions(total_rows=len(merged))
        self.t_step_sheet.refresh()
        self.update()

    def remove_calibration_step(self):
        """Removes the currently selected calibration step from the step table and the plots.
        """        
        row_number = None
        tbl = self.t_step_sheet
        for box in tbl.get_all_selection_boxes():
            row_number = tbl.datarn(box.from_r) # type: ignore

        if row_number:
            tbl.delete_row(row_number)
        self.update_plots()

    def on_cell_select(self, event):
        """Event-Callback function triggerd by the cell select event of the step table.
        Triggers a redraw of the plots where the currently selected calibration step is highlighted.

        Args:
            event (dict): The event information
        """        

        content = event["selected"]
        self.highlight_static_state = content.row
        # print(f"Cell Selected in row {self.highlight_static_state}")
        self.update_plots()

    def fit_temp_steps(self):
        """Fitting function. Takes the identified calibration steps and calculates for each channel (including thermocouples)
        the polynomial fit. 
        """        

        self.update_plots()
        tbl = self.t_step_sheet.data
        if len(tbl) >= 2:  # above two selected points the interpolation calculation ca begin

            for ChIdx in range(0, MaxJUT_Channels):  # iterate through all the 4 channels viewed
                ch_tsp = f"TSP{ChIdx}"
                x_data = np.array(self.t_step_sheet.get_column_data(0), dtype=np.float32)
                y_data = np.array(self.t_step_sheet.get_column_data(ChIdx + 1), dtype=np.float32)

                interp_deg = self.Interpolation_Degrees.get()
                
                p_fit = np.polyfit(x_data, y_data, interp_deg)

                if interp_deg == 1:
                    p_fit = np.insert(p_fit, 0, 0.0)

                [quad, slope, offs] = p_fit

                if abs(slope) > 0.00001:
                    y_fit = offs + slope * x_data + quad * x_data * x_data
                    corr_mat = np.corrcoef(y_data, y_fit)
                    corr = corr_mat[0, 1]
                    r_sq = corr ** 2
                else:
                    r_sq = 1.0
                print(f"Fitting Channel {ChIdx} with interpolation degree n={interp_deg}: Offset: {offs:.4f} ,Linear: {slope:.4f}, Quad: {quad:.7f}, R²: {r_sq:.4f}")
                if ChIdx < MaxJUT_Channels:
                    self.t_result_sheet.set_cell_data(r=ChIdx, c=0, value=self.utta_data.meta_data.Channels[ch_tsp]["Name"])
                # else:
                    #self.t_result_sheet.set_cell_data(r=ChIdx, c=0, value="TC0")
                self.t_result_sheet.set_cell_data(r=ChIdx, c=1, value=offs)
                self.t_result_sheet.set_cell_data(r=ChIdx, c=2, value=slope)
                self.t_result_sheet.set_cell_data(r=ChIdx, c=3, value=quad)
                self.t_result_sheet.set_cell_data(r=ChIdx, c=4, value=r_sq)

            self.btn_save_result.configure(state='normal')

    def on_closing(self):
        """On Closing event. Triggered as soon as the application window is closed
        """        
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.save_settings()
            self.destroy()

    def on_xlims_change(self, event_ax):
        """Plot Event, triggerd when the plot is zoomed and the x-limits change.

        Args:
            event_ax (_type_): The event information
        """        

        x_limits = event_ax.get_xlim()
        xlim_min = int(x_limits[0])
        xlim_max = int(x_limits[1])
        # print("updated xlims: ", event_ax.get_xlim())
        self.g_plots[1].set_xlim(left=x_limits[0], right=x_limits[1])
        ymin = np.min(self.utta_data.tc_interp[0, xlim_min:xlim_max]) # type: ignore
        ymax = np.max(self.utta_data.tc_interp[0, xlim_min:xlim_max]) # type: ignore
        self.g_plots[1].set_ylim(bottom=ymin, top=ymax)

        tsp_min = float(np.min(self.utta_data.adc_interp[0, xlim_min:xlim_max])) # type: ignore
        tsp_max = float(np.max(self.utta_data.adc_interp[0, xlim_min:xlim_max])) # type: ignore
        tsp_pp = Quantity(tsp_max-tsp_min, "V")

        self.ent_step_temp.delete(0, 'end')
        self.ent_step_temp.insert(0, f"{np.mean(self.utta_data.tc_interp[0, xlim_min:xlim_max]):.2f}") # type: ignore

        self.lbl_helpbar.configure(text="Zoom into the measurement until the whole plot is filled with the steady state.\n" +
                                   f"Peak-to-peak spread of {self.utta_data.meta_data.Channels["TSP0"]["Name"] } is {tsp_pp}. " +
                                   "\nWhen you are satisfied enter the step temperature and click on 'Add Step'", style='info.Inverse.TLabel')
        

if __name__ == "__main__":
    app = CalApp()
    app.mainloop()
