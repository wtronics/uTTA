#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    uTTA_Reporting.py
Description:    An HTML report generation service for uTTA Measurements.
                This module uses jinja2 and plotly to generate HTML reports with
                interactive graphs the user can zoom in and use cursors to extract measurement data.

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           04.10.2025
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

import base64
import os
from pathlib import Path
from typing import Any, Dict, List, Union

from jinja2 import Environment, FileSystemLoader
import numpy as np
import plotly.graph_objects as go
from quantiphy import Quantity
from tkinter import filedialog as fd, messagebox as mb
import ttkbootstrap as ttk

import library.uTTA_data_processing as udpc
import library.uTTA_Reporting_Annotation as utta_report


def export(utta_data: Any, outfilename: str, root_window: ttk.Window) -> None:
    """ Generates an HTML measurement report for a Zth measurement.

    The report contains all measurement relevant information, including interactive plots
    as plotly graph objects. In addition, the Zth curves are represented in tables with reduced resolution.
    For improved traceability, the calibration data of each TSP are also stored in a separate section.

    Args:
        utta_data (Any): uTTA measurement data object.
        outfilename (str): Target file path for the generated HTML report.
        root_window (ttk.Window): Parent Tkinter window for dialog displays.
    """

    environment = Environment(loader=FileSystemLoader("Report_Templates/"))
    template = environment.get_template("Master_Template.html")
    filename = outfilename

    utta_dict: Dict[str, Any] = {}

    add_img = mb.askquestion("Add Image of Test Setup",
                             "Do you want to add some images of your test setup to the report?")
    if add_img == "yes":

        photo_pathes = fd.askopenfilenames(filetypes=(("JPEG-Images", "*.jpg"),
                                                      ("PNG-Images", "*.png"),
                                                      ("All files", "*.*")))

        utta_dict["Test_Setup_Photo"] = False

        if photo_pathes:
            # Open the Report Image Annotation Dialog
            dialog = utta_report.ImageLayoutDialog(root_window, list(photo_pathes))
            root_window.wait_window(dialog)  # Wait until dialog is closed

            if dialog.confirmed:
                utta_dict["Test_Setup_Layout"] = dialog.result_layout
                utta_dict["Test_Setup_HTML"] = "".join(dialog.processed_images_html)
                utta_dict["Test_Setup_Photo"] = True

    # Entries to style the report
    utta_dict["TitleImageLeft"] = encode_png2html_string(os.path.abspath(r"Report_Templates/uTTA_Logo.png"))
    utta_dict["TitleImageRight"] = encode_png2html_string(os.path.abspath(r"Report_Templates/Your_Logo.png"))
    utta_dict["PDF_Printable_Report"] = False

    # Transfer of information inside utta_data into the jinja2 information dict
    utta_dict["adc_timebase"] = utta_data.time_full
    utta_dict["adc"] = utta_data.udiode_full
    utta_dict["cooling_start_index"] = utta_data.cooling_start_idx
    utta_dict["Channels"] = utta_data.meta_data.Channels
    utta_dict["Zth_Table"] = compress_curve(utta_data.time_cooling, utta_data.zth, 6)

    utta_dict["Measurement_Info"] = utta_data.meta_data.Measurement
    utta_dict["Cal_Data"] = utta_data.meta_data.CalData

    utta_dict["I_Heat"] = utta_data.i_heat
    utta_dict["I_Sense"] = utta_data.meta_data.Isense
    utta_dict["P_Heat"] = utta_data.p_heat
    utta_dict["T_Preheat"] = utta_data.meta_data.TPreheat
    utta_dict["T_Heating"] = utta_data.meta_data.THeating
    utta_dict["T_Cooling"] = utta_data.meta_data.TCooling

    utta_dict["InterpolTStart"] = f'{Quantity(utta_data.InterpolationTStart, "s")}'
    utta_dict["InterpolTEnd"] = f'{Quantity(utta_data.InterpolationTEnd, "s")}'
    utta_dict["InterpolFactor"] = utta_data.InterpolationFactorM
    utta_dict["InterpolOffset"] = utta_data.InterpolationOffset
    utta_dict["InterpolDieSize"] = utta_data.EstimatedDieSize

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=utta_data.time_cooling, y=utta_data.zth[0, :], name=utta_dict["Channels"]["TSP0"]["Name"]))
    fig.update_xaxes(type="log", exponentformat="SI")
    fig.update_yaxes(type="log")
    fig.update_layout(width=1100, height=600, xaxis_title=r"Time / [s]", yaxis_title=r"Z<sub>th</sub> / [K/W]")

    utta_dict["PlotFullMeasurement"] = fig.to_html(full_html=False, include_plotlyjs=False)

    if (utta_dict["Channels"]["TSP1"]["Name"] != "OFF" or 
        utta_dict["Channels"]["TSP2"]["Name"] != "OFF"):
        fig = go.Figure()
        if utta_dict["Channels"]["TSP1"]["Name"] != "OFF":
            fig.add_trace(
                go.Scatter(x=utta_data.time_cooling, y=utta_data.zth[1, :], name=utta_dict["Channels"]["TSP1"]["Name"]))
        if utta_dict["Channels"]["TSP2"]["Name"] != "OFF":
            fig.add_trace(
                go.Scatter(x=utta_data.time_cooling, y=utta_data.zth[2, :], name=utta_dict["Channels"]["TSP2"]["Name"]))

        fig.update_xaxes(type="log", exponentformat="SI")
        if np.min(utta_data.zth[1:2, :]) > 0.0:
            fig.update_yaxes(type="log")
        fig.update_layout(width=1100, height=600, xaxis_title=r"Time / [s]", yaxis_title=r"Z<sub>th</sub> / [K/W]")
        utta_dict["PlotZthCouplingCurves"] = fig.to_html(full_html=False, include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=utta_data.time_full, y=utta_data.udiode_full[0, :], name=utta_dict["Channels"]["TSP0"]["Name"], yaxis="y1"))
    if utta_dict["Channels"]["TSP1"]["Name"] != "OFF":
        fig.add_trace(
            go.Scatter(x=utta_data.time_full, y=utta_data.udiode_full[1, :], name=utta_dict["Channels"]["TSP1"]["Name"], yaxis="y1"))
    if utta_dict["Channels"]["TSP2"]["Name"] != "OFF":
        fig.add_trace(
            go.Scatter(x=utta_data.time_full, y=utta_data.udiode_full[2, :], name=utta_dict["Channels"]["TSP2"]["Name"], yaxis="y1"))
    fig.add_trace(
        go.Scatter(x=utta_data.time_full, y=utta_data.current_full, name="Current", yaxis="y2"))
    fig.update_xaxes(exponentformat="SI")
    fig.update_layout(width=1100, height=600, xaxis_title="Time / [s]", yaxis_title="Diode Voltage / [V]",
                      yaxis2=dict(title="Current / [A]", overlaying="y", side="right"))
    utta_dict["PlotFullMeasDiode"] = fig.to_html(full_html=False, include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=utta_data.time_full, y=utta_data.udiode_cooling[0, :], name=utta_dict["Channels"]["TSP0"]["Name"]))
    if utta_dict["Channels"]["TSP1"]["Name"] != "OFF":
        fig.add_trace(
            go.Scatter(x=utta_data.time_full, y=utta_data.udiode_cooling[1, :], name=utta_dict["Channels"]["TSP1"]["Name"]))
    if utta_dict["Channels"]["TSP2"]["Name"] != "OFF":
        fig.add_trace(
            go.Scatter(x=utta_data.time_full, y=utta_data.udiode_cooling[2, :], name=utta_dict["Channels"]["TSP2"]["Name"]))
    fig.update_xaxes(type="log", exponentformat="SI")

    fig.update_layout(width=1100, height=600, xaxis_title="Time / [s]", yaxis_title="Diode Voltage / [V]")
    utta_dict["PlotCoolingMeasDiode"] = fig.to_html(full_html=False, include_plotlyjs=False)

    utta_dict["PlotStartInterpolation"] = _interpol_plot(utta_data, utta_dict)

    report = template.render(utta_dict)
    with open(filename, mode="w", encoding="utf-8") as output:
        output.write(report)

    print("\033[94mReport written\033[0m")

    if hasattr(os, "startfile"):
        os.startfile(filename)


def export_calibration_report(utta_data: Any, outfilename: str, root_window: ttk.Window, cal_results: Dict[str, Any]) -> None:
    """Generates an HTML calibration report for TSP sensor calibration.

    Args:
        utta_data (Any): uTTA calibration measurement data object.
        outfilename (str): Target file path for the generated HTML report.
        root_window (ttk.Window): Parent Tkinter window for dialog displays.
        cal_results (Dict[str, Any]): Dictionary containing processed calibration evaluation data.
    """
    print("starting calibration report")
    environment = Environment(loader=FileSystemLoader("Report_Templates/"))
    template = environment.get_template("Calibration_Template.html")
    filename = outfilename

    report_dict: Dict[str, Any] = {}

    # Entries to style the report
    report_dict["TitleImageLeft"] = encode_png2html_string(os.path.abspath(r"Report_Templates/uTTA_Logo.png"))
    report_dict["TitleImageRight"] = encode_png2html_string(os.path.abspath(r"Report_Templates/Your_Logo.png"))
    report_dict["PDF_Printable_Report"] = False
    report_dict["Channels"] = cal_results["Interpolation_Results"]

    # Transfer of information inside utta_data into the jinja2 information dict
    report_dict["Measurement_Info"] = utta_data.meta_data.Measurement

    report_dict["I_Sense"] = utta_data.meta_data.Isense
    report_dict["T_Preheat"] = utta_data.meta_data.TPreheat
    report_dict["T_Heating"] = utta_data.meta_data.THeating
    report_dict["T_Cooling"] = utta_data.meta_data.TCooling

    report_dict["Step_Table_Header"] = cal_results["Step_Table_Header"]
    report_dict["Step_Table"] = cal_results["Step_Table"]

    colstep_steptemp = cal_results["Col_Temp"]
    colstep_stablestart = cal_results["Col_Start"]
    colstep_stableend = cal_results["Col_End"]

    step_data = np.array(cal_results["Step_Data"])

    # Generate the plot with the raw measurement data of the TSPs
    fig_tsp = go.Figure()
    for ch_idx in range(0, utta_data.no_of_tsp):
        if report_dict["Channels"][f"TSP{ch_idx}"]["Name"] != "OFF":
            fig_tsp.add_trace(
                go.Scatter(x=utta_data.time_interp, y=utta_data.adc_interp[ch_idx], name=report_dict["Channels"][f"TSP{ch_idx}"]["Name"]))

            # Generate the interpolation plot for each active channel
            fig_interpol = go.Figure()
            fig_interpol.add_trace(
                go.Scatter(x=step_data[:, 0], y=step_data[:, 1 + ch_idx], name=report_dict["Channels"][f"TSP{ch_idx}"]["Name"]))
            fig_interpol.update_layout(width=1100, height=600, xaxis_title=r"Ambient Temperature / [°C]", yaxis_title=r"V<sub>TSP</sub> / [V]")
            report_dict["Channels"][f"TSP{ch_idx}"]["Temp_Plot"] = fig_interpol.to_html(full_html=False, include_plotlyjs=False)

    fig_tsp.update_layout(width=1100, height=600, xaxis_title=r"Time / [s]", yaxis_title=r"V<sub>TSP</sub> / [V]")

    # Generate the second plot with the raw measurement data of the Thermocouples
    fig_tck = go.Figure()
    fig_tck.add_trace(
        go.Scatter(x=utta_data.time_interp, y=utta_data.tc_interp[0], name="TC0"))
    fig_tck.update_layout(width=1100, height=600, xaxis_title=r"Time / [s]", yaxis_title=r"T<sub>Thermocouple</sub> / [°C]")

    # Add highlighting to the marked "stable" regions to both diagrams
    for t_step in step_data:
        fig_tsp.add_vrect(x0=t_step[colstep_stablestart], x1=t_step[colstep_stableend], line_width=0, fillcolor="MediumTurquoise", opacity=0.5 , 
                      label=dict(text=f"{t_step[colstep_steptemp]:.1f}°C", textangle=-90))
        fig_tck.add_vrect(x0=t_step[colstep_stablestart], x1=t_step[colstep_stableend], line_width=0, fillcolor="MediumTurquoise", opacity=0.5 , 
                      label=dict(text=f"{t_step[colstep_steptemp]:.1f}°C", textangle=-90))

    report_dict["U_Diode_Plot"] = fig_tsp.to_html(full_html=False, include_plotlyjs=False)
    report_dict["Temperature_Plot"] = fig_tck.to_html(full_html=False, include_plotlyjs=False)
    # TODO: Add graph lines for interpolated curves

    report = template.render(report_dict)
    with open(filename, mode="w", encoding="utf-8") as output:
        output.write(report)

    print("\033[94mReport written\033[0m")

    os.startfile(filename)

def encode_png2html_string(imagepath: str) -> str:
    """ Encodes a given PNG or JPEG file into a Base64 encoded HTML image element.

    Args:
        imagepath (str): Path to the image file to be encoded.

    Returns:
        str: HTML img tag string containing embedded Base64 data or error string.
    """
    path = Path(imagepath)
    if not path.exists():
        return "<p> No Image found! </p>"

    suffix = path.suffix.lower()
    if suffix in [".png", ".jpg", ".jpeg"]:
        with open(path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        if suffix == ".png":
            return f'<img src="data:image/png;base64,{img_base64}" height="70"></img>'
        return f'<img src="data:image/jpeg;base64,{img_base64}"></img>'

    return "<p> Unsupported image format! </p>"


def compress_curve(timebase: np.ndarray, data: np.ndarray, samples_decade: int) -> np.ndarray:
    """ Compresses measurement data to an array with a selectable number of points per decade.

    Args:
        timebase (np.ndarray): Timebase vector from uTTA data processing.
        data (np.ndarray): Zth curve data array from uTTA data processing.
        samples_decade (int): Target number of samples per decade to export.

    Returns:
        np.ndarray: Matrix where first column is time and subsequent columns are interpolated Zth curves.

    Raises:
        ValueError: If samples_decade is not a positive integer.
    """
    if not isinstance(samples_decade, int) or samples_decade <= 0:
        raise ValueError("Input 'samples_decade' must be a positive integer.")
    if samples_decade >= len(timebase):
        return np.empty((0, 1 + data.shape[0]))

    # Build the basic timebase for one decade. This will be reused and multiplied by the corresponding decade
    sub_timebase = np.power(10.0, np.linspace(0, 1 / samples_decade * (samples_decade - 1), samples_decade))

    time_multiplier = -6.0
    interpol_timebase: List[float] = []
    while True:    # make a little do-while loop...
        timestep = np.power(10.0, time_multiplier)
        segment_timebase = timestep * sub_timebase
        time_multiplier += 1
        interpol_timebase.extend(segment_timebase.tolist())

        if np.max(interpol_timebase) > np.max(timebase):
            break

    filtered_timebase = [tim for tim in interpol_timebase if tim <= np.max(timebase)]

    if filtered_timebase[-1] < np.max(timebase):
        filtered_timebase.append(float(np.max(timebase)))

    arr_width = len(data[:, 0])  # check for the width of the array to do an interpolation for every column
    data_output = np.zeros(shape=(1 + arr_width, len(filtered_timebase)))
    data_output[0, :] = filtered_timebase
    for col in range(1, arr_width + 1):
        data_output[col, :] = np.interp(filtered_timebase, timebase, data[col - 1, :])

    return np.transpose(data_output)


def _interpol_plot(utta_data: Any, utta_dict: Dict[str, Any]) -> str:
    """Generates an interactive Plotly plot showing early-time square-root-of-time interpolation.

    Args:
        utta_data (Any): uTTA measurement data object.
        utta_dict (Dict[str, Any]): Dictionary containing report metadata and channel settings.

    Returns:
        str: Rendered HTML snippet for the Plotly interpolation graph.
    """

    fig = go.Figure()

    interpol_plot_cutoff_idx = udpc.find_nearest(utta_data.time_cooling, 0.1)
    tb_show = np.sqrt(utta_data.time_cooling[0:interpol_plot_cutoff_idx])

    diode_temp_values = utta_data.t_dio_raw[0, :]

    fig.add_trace(
        go.Scatter(x=tb_show, y=diode_temp_values[0:interpol_plot_cutoff_idx], name=utta_dict["Channels"]["TSP0"]["Name"]))

    min_y = np.min(diode_temp_values[0:interpol_plot_cutoff_idx])

    interp_start = (np.sqrt(utta_data.time_cooling[0:interpol_plot_cutoff_idx]) * utta_data.InterpolationFactorM
                    + utta_data.InterpolationOffset)

    interp_cutoff_idx = udpc.find_nearest(interp_start, min_y)
    interp_cutoff_idx = int(np.min([interp_cutoff_idx, interpol_plot_cutoff_idx]))

    fig.add_trace(
        go.Scatter(x=tb_show[0:interp_cutoff_idx], y=interp_start[0:interp_cutoff_idx], name="Interpolated"))

    fig.update_xaxes(exponentformat="SI")
    # TODO: Stabilize the sometimes inconsistent rendering of LaTeX axis labels
    fig.update_layout(width=1100, height=600, xaxis_title=r"$\sqrt{\text{Time}} / [\sqrt{s}]$", yaxis_title=r"$\Delta\text{Temperature / [°C]}$")
    fig.add_vline(x=np.sqrt(utta_data.InterpolationTStart), annotation_text=r"$t_{cut}$", annotation_position="top")
    fig.add_vline(x=np.sqrt(utta_data.InterpolationTEnd), annotation_text=r"$t_{end}$", annotation_position="bottom")
    return str(fig.to_html(full_html=False, include_plotlyjs=False))
