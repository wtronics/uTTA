#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    uTTA_Postprocess_Measurement_GUI.py
Description:    A graphical user interface to provide a easy to use application for postprocessing measurement data from the uTTA device
                - Import of the measurement file via file dialog
                - Visualisation of the full measurement and the cooling section in plots for voltage and current
                - Interpolation dialog to tune the interpolation section of the heated JUT at the start of the cooling section
                - Iterative deconvolution of the calculated Zth curve by using the bayes iteration algorithm
                - Fitting dialog to generate fitted RC models as Foster and Cauer models.

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           28.09.2025
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
"""uTTA Postprocess Measurement GUI Application."""

import os
import logging
import matplotlib

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
import library.uTTA_data_processing as udProc
import library.uTTA_Postprocess_Measurement_Interpol_Widget as uttaInterpolWidget
import library.uTTA_Postprocess_Measurement_Widgets as uttaWidgets

from datetime import datetime
from typing import Any
from tkinter import filedialog as fd
from library.rc_fitting_tool_GUI import ThermalFittingWindow, print_emitted_results

matplotlib.use("TkAgg")

Debug_AutoLoadEnable = False
Debug_AutoExportHTML = False
Debug_LoggingLevel = logging.INFO
Debug_AutoLoadFile = os.path.abspath(r"..\..\060_Example_Measurement_Data\Example_Measurement.umf")

WINDOW_WIDTH = 1580
WINDOW_HEIGHT = 960


class UmfViewerApp(ttk.Window):
    """Main application window for uTTA measurement postprocessing."""

    def __init__(self) -> None:
        """ Initializes the main GUI window, layouts, widgets, and data objects."""
        super().__init__(themename="flatly")

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename=f"{__file__.split(".")[0]}.log", level=logging.WARNING, format="%(asctime)s  %(levelname)s | %(message)s")     # %(module)s::%(funcName)s |
        logging.getLogger("__main__").setLevel(Debug_LoggingLevel)
        self.title("uTTA Measurement postprocessing GUI")
        self.geometry("1480x960")
        self.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        screen_dpi = self.winfo_fpixels("1i")
        geometry = self.winfo_geometry()

        self.iconbitmap(r"library/uTTA_Icon.ico")
        self.logger.info(f"DPI: {screen_dpi}, Geometry: {geometry}")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        self.FileOpened = False
        self.FileNameWExt = ""
        self.FileName = ""
        self.DirName = ""

        self.utta_data = udProc.UttaZthProcessing(logger=self.logger)

        self.utta_data.load_settings(__file__)
        self.interp_window: Any = None

        self.paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # LEFT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        self.frm_left = ttk.Frame(self.paned)
        self.frm_left.pack(fill=tk.X, padx=10, pady=10)

        # Measurement File Button Frame
        self.frm_file_btns = ttk.Labelframe(self.frm_left, text="Import", style="secondary.TLabelframe")
        self.frm_file_btns.pack(fill=tk.X, padx=10, pady=10)
        self.btn_measure_file = ttk.Button(master=self.frm_file_btns,
                                           text="Import Measurement",
                                           command=self.read_measurement_file_callback,
                                           style="dark")
        self.btn_measure_file.pack(fill=tk.X, padx=10, pady=10)

        self.frm_processing_btns = ttk.Labelframe(self.frm_left, text="Processing", style="secondary.TLabelframe")

        self.frm_processing_btns.pack(fill=tk.X, padx=10, pady=10)
        self.btn_interpolation_setup = ttk.Button(master=self.frm_processing_btns,
                                                  text="Interpolation Setup",
                                                  command=self.open_interpolation_window_callback,
                                                  style="dark",
                                                  state=tk.DISABLED)
        self.btn_interpolation_setup.pack(fill=tk.X, padx=10, pady=10)

        self.btn_fitting_tool = ttk.Button(master=self.frm_processing_btns,
                                           text="Fit RC Parameters",
                                           command=self.open_fitting_gui,
                                           style="dark")
        self.btn_fitting_tool.pack(fill=tk.X, padx=10, pady=10)

        self.frm_export_btns = ttk.Labelframe(self.frm_left, text="Export", style="secondary.TLabelframe")
        self.frm_export_btns.pack(fill=tk.X, padx=10, pady=10)
        self.btn_export_tdim_master = ttk.Button(master=self.frm_export_btns,
                                                 text="Export TDIM Master",
                                                 command=self.export_to_tdim_master,
                                                 style="dark",
                                                 state=tk.DISABLED)
        self.btn_export_tdim_master.pack(fill=tk.X, padx=10, pady=10)

        self.btn_export_zth_curve = ttk.Button(master=self.frm_export_btns,
                                               text="Export Zth Curve",
                                               command=self.export_to_zth_curve,
                                               style="dark",
                                               state=tk.DISABLED)
        self.btn_export_zth_curve.pack(fill=tk.X, padx=10, pady=10)

        self.btn_export_t3i_curve = ttk.Button(master=self.frm_export_btns,
                                               text="Export t3i-Curve",
                                               command=self.export_to_t3i_file,
                                               style="dark",
                                               state=tk.DISABLED)
        self.btn_export_t3i_curve.pack(fill=tk.X, padx=10, pady=10)

        self.frm_report_btns = ttk.Labelframe(self.frm_left, text="Report", style="secondary.TLabelframe")
        self.frm_report_btns.pack(fill=tk.X, padx=10, pady=10)

        self.btn_report_html = ttk.Button(master=self.frm_report_btns,
                                          text="Create HTML Report",
                                          command=self.report_html,
                                          style="dark",
                                          state=tk.DISABLED)
        self.btn_report_html.pack(fill=tk.X, padx=10, pady=10)

        self.paned.add(self.frm_left)
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # RIGHT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        self.frm_right = ttk.Frame(self.paned)
        self.frm_right.pack(fill=tk.X, padx=10, pady=10)

        # Helper Bar Frame
        self.frm_help_bar = ttk.Frame(master=self.frm_right, style="info.TFrame")
        self.frm_help_bar.pack(fill=tk.X, padx=10, pady=10)

        self.lbl_helpbar = ttk.Label(master=self.frm_help_bar, anchor=tk.W, style="inverse-info", wraplength=1080)
        self.lbl_helpbar.pack(fill=tk.X, padx=10, pady=10)
        self.lbl_helpbar.configure(text="Welcome to the uTTA measurement postprocessing GUI. \n"
                                        "Click 'Measurement File' and import a measurement")

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # Tab Control
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        self.tabs = ttk.Notebook(master=self.frm_right)
        self.tabs.pack(fill=tk.BOTH, padx=10, pady=10)

        # 1st Page: Plot Area
        self.frm_plot_area = ttk.Frame(master=self)
        self.frm_plot_area.pack(fill=tk.BOTH, padx=10, pady=10)
        self.tabs.add(self.frm_plot_area, text="Measurement Data")

        self.meas_plots_widget = uttaWidgets.MeasurementPlotsWidget(self.frm_plot_area,
                                                                    self.utta_data,
                                                                    1230, 750,
                                                                    screen_dpi)

        # 2nd Page: Measurement Details
        self.frm_meas_details = ttk.Frame(master=self)
        self.frm_meas_details.pack(fill=tk.BOTH, padx=10, pady=10)
        self.tabs.add(self.frm_meas_details, text="Measurement Info")

        self.meas_info_widget = uttaWidgets.MeasurementInfoWidget(self.frm_meas_details)

        # 3rd Page: Zth Curves
        self.frm_zth_curves = ttk.Frame(master=self)
        self.frm_zth_curves.pack(fill=tk.BOTH, padx=10, pady=10)
        self.tabs.add(self.frm_zth_curves, text="Zth Curves      ")

        self.zth_plots_widget = uttaWidgets.ZthPlotsWidget(self.frm_zth_curves,
                                                           self.utta_data,
                                                           1230,
                                                           750,
                                                           screen_dpi)

        # 4th Page: Deconvolution
        self.frm_deconv = ttk.Frame(master=self)
        self.frm_deconv.pack(fill=tk.BOTH, padx=10, pady=10)
        self.tabs.add(self.frm_deconv, text="Deconvolution   ")

        self.deconv_widget = uttaWidgets.DeconvPlotsWidget(self.frm_deconv, 
                                                           self.utta_data,
                                                           1230, 750,
                                                           screen_dpi)

        # 5th Page: Settings
        self.frm_settings = ttk.Frame(master=self)
        self.frm_settings.pack(fill=tk.BOTH, padx=10, pady=10)
        self.tabs.add(self.frm_settings, text="Settings        ")

        self.settings = uttaWidgets.SettingsWidget(self.frm_settings, self, self.utta_data, self.logger)
        self.paned.add(self.frm_right)

        self.update_widgets()

        if Debug_AutoLoadEnable:
            self.read_measurement_file_callback()

    def update_widgets(self) -> None:
        """Triggers widget UI refresh if data import was successful."""

        self.logger.info("Attempting to update widgets")
        if self.utta_data.flag_import_successful:
            self.logger.info("Updating widgets")
            self.meas_info_widget.update_widget(self.utta_data)
            self.meas_plots_widget.plots.update_plots()
            self.zth_plots_widget.plots.update_plots()
            self.deconv_widget.plots.update_plots()

        self.update()

    def update_calculations(self, complete: bool = True) -> None:
        """Executes thermal cooling, voltage, interpolation, and deconvolution processing.

        Args:
            complete: If True, performs complete recalculation of initial curve parameters.
        """

        self.logger.info("Updating Calculations")
        if complete:
            self.utta_data.calculate_cooling_curve()
            self.utta_data.calculate_tsp_start_voltages()

        self.utta_data.interpolate_zth_curve_start()
        self.utta_data.zth_deconvolution_bayes()

        self.logger.info("Update of calculations completed")
        self.update_widgets()
        self.logger.info("Update of widgets completed")

    def read_measurement_file_callback(self) -> None:
        """Callback to prompt file selection and process the selected measurement file."""

        if not Debug_AutoLoadEnable:
            measfilename = udProc.select_file("Select the measurement file",
                                              (("uTTA Measurement Files", "*.umf"), ("Text-Files", "*.txt"), ("All files", "*.*")))
        else:
            measfilename = Debug_AutoLoadFile

        if len(measfilename) > 0:  # check if string is not empty
            self.FileNameWExt, self.FileName, self.DirName = udProc.split_file_path(measfilename)

            self.FileOpened = self.utta_data.import_data(measfilename)

            if not self.utta_data.meta_data.FlagTSPCalibrationFile:

                self.update_calculations()

                self.lbl_helpbar.configure(text=f"File: {self.FileNameWExt} was successfully imported.",
                                           style="success.Inverse.TLabel")
                self.frm_help_bar.configure(style="success.TFrame")

                self.btn_interpolation_setup.configure(state=tk.NORMAL)
                self.btn_export_tdim_master.configure(state=tk.NORMAL)
                self.btn_export_zth_curve.configure(state=tk.NORMAL)
                self.btn_report_html.configure(state=tk.NORMAL)
                self.btn_export_t3i_curve.configure(state=tk.NORMAL)

                if Debug_AutoExportHTML:
                    self.report_html()

            else:
                self.lbl_helpbar.configure(text=f"File: {self.FileNameWExt} is a TSP calibration measurement.\n"
                                                 "Therefore this file can't be processed!",
                                           style="danger.Inverse.TLabel")
                self.frm_help_bar.configure(style="danger.TFrame")

                self.btn_interpolation_setup.configure(state=tk.DISABLED)
                self.btn_export_tdim_master.configure(state=tk.DISABLED)
                self.btn_export_zth_curve.configure(state=tk.DISABLED)
                self.btn_report_html.configure(state=tk.DISABLED)
                self.btn_export_t3i_curve.configure(state=tk.DISABLED)

        else:
            self.lbl_helpbar.configure(text=f"File: {self.FileNameWExt} was not imported.",
                                       style="danger.Inverse.TLabel")
            self.frm_help_bar.configure(style="danger.TFrame")

    def open_interpolation_window_callback(self) -> None:
        """Opens or lifts the TSP interpolation setup child window."""

        self.logger.info("Opening Interpolation Window")
        if self.interp_window is None:   #  or not self.interp_window.winfo_exists():
            self.interp_window = uttaInterpolWidget.TSPInterpolationApp(self, self.logger)
        else:
            self.interp_window.lift()

    def recalculate_interpolation(self) -> None:
        """Triggers partial recalculation of interpolation parameters."""
        self.logger.info("Recalculate called")
        self.update_calculations(False)

    def report_html(self) -> None:
        """Prompts target directory and generates the HTML measurement report."""
        report_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the report shall be stored.",
                                        mustexist=True)

        if report_folder:
            outfilename = f"{report_folder}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.FileName}_Measurement_Report.html"
            self.utta_data.report_html(outfilename, self)

            if Debug_AutoExportHTML:
                self.on_closing()

    def export_to_tdim_master(self) -> None:
        """Exports measurement data to TDIM Master format."""
        output_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the TDIM Master File shall be stored.",
                                        mustexist=True)

        if output_folder:
            outfilename = f"{output_folder}/{self.FileName}.txt"
            self.utta_data.export_tdim_master(outfilename)

    def export_to_zth_curve(self) -> None:
        """Exports Zth raw data curve to a text file."""
        output_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the Zth raw data shall be stored.",
                                        mustexist=True)

        if output_folder:
            outfilename = f"{output_folder}/{self.FileName}_zth.txt"
            self.utta_data.export_zth_curve(outfilename)


    def export_to_t3i_file(self) -> None:
        """Exports measurement results to t3i file format."""
        output_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the t3i-file shall be stored.",
                                        mustexist=True)

        if output_folder:
            outfilename = f"{output_folder}/{self.FileName}.t3i"
            self.utta_data.export_t3i_file(outfilename)

    def interpolation_window_closed(self) -> None:
        """Resets the interpolation window reference upon closing."""
        self.interp_window = None
        self.logger.info("Updating Widgets after closing interpolation window")


    def open_fitting_gui(self) -> None:
        """Opens thermal fitting tool dialog window."""
        top = ttk.Toplevel()
        top.title("Thermal Fitting Tool")
        top.geometry("1200x850")

        app = ThermalFittingWindow(
            parent=top,
            time_data=np.asarray(self.utta_data.time_cooling, dtype=np.float64),
            zth_data=np.asarray(self.utta_data.zth[0], dtype=np.float64),
            on_fit_complete=self.handle_fit_results,
            auto_fit=False,
        )
        app.pack(fill=tk.BOTH, expand=True)

        # Only cleanup the pop up window, not the main application
        top.protocol("WM_DELETE_WINDOW", app.close)

    def handle_fit_results(self, results: dict[str, Any]) -> None:
        """Processes the fitting parameters returned from ThermalFittingWindow.

        Args:
            results: Dictionary containing network type, order, and R/C component vectors.
                Dictionary Structure: 
                    {"foster": {"order":self.fitted_foster_network.order, 
                                 "r": [r for r in self.fitted_foster_network.r],
                                 "c": [c for c in self.fitted_foster_network.c],},
                     "cauer": {"order":self.fitted_cauer_network.order, 
                                 "r": [r for r in self.fitted_cauer_network.r],
                                 "c": [c for c in self.fitted_cauer_network.c],}}
        """
        print(f"Received: Order {results['foster']['order']}")
        print_emitted_results(results=results)

    def on_closing(self) -> None:
        """Saves settings and destroys window upon application exit."""
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.utta_data.save_settings(__file__)
        self.destroy()


if __name__ == "__main__":
    app = UmfViewerApp()
    app.mainloop()