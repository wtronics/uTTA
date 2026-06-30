#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    utta_Reporting.py
Description:    An HTML report generation service for uTTA Measurements.
                This module uses jinja2 and plotly to generate HTML reports with
                interactive graphs the user can zoom in and use cursors to extract meausrement data.

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
from typing import List, Union
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined, Template
import plotly.graph_objects as go
from tkinter import messagebox as mb
from tkinter import filedialog as fd
import ttkbootstrap as ttk
import os
import pandas as pd
import numpy as np
import numpy.dtypes 
import library.uTTA_data_processing as udpc
import library.uTTA_Reporting_Annotation as utta_report
from quantiphy import Quantity
import base64
from PIL import Image
import io

def export(utta_data, outfilename:str, root_window:ttk.Window) -> None:
    ''' Generates an HTML measurement report for a Zth measurement. 
    The report contains all measurement relevant information, including interactive plots
    as plotly graph object. In addition the Zth curves are represented in tables with reduced resolution.
    For improved traceability the calibration data of each TSP are also stored in a separate section.
    The template used is stored in >050_Phyton_Scripts/uTTA/Report_Templates/Master_Template.html<

    Args:
        utta_data (utta_data)   : uTTA measurement data
        outfilename (string)    : Path of the final report file
    Returns:
        None
        '''

    environment = Environment(loader=FileSystemLoader("Report_Templates/"))
    template = environment.get_template("Master_Template.html")
    filename = outfilename

    utta_dict = {}

    add_img = mb.askquestion('Add Image of Test Setup', 'Do you want to add some images of your test setup to the report?')
    if add_img == 'yes':

        photo_pathes = fd.askopenfilenames(filetypes=(('JPEG-Images', '*.jpg'), ('PNG-Images', '*.png'), ('All files', '*.*')))

        utta_dict['Test_Setup_Photo'] = False

        if photo_pathes:

            # Open the Report Image Annotation Dialog
            dialog = utta_report.ImageLayoutDialog(root_window, list(photo_pathes))
            root_window.wait_window(dialog)  # Wait until dialog is closed

            if dialog.confirmed:
                utta_dict['Test_Setup_Layout'] = dialog.result_layout
                utta_dict['Test_Setup_HTML'] = "".join(dialog.processed_images_html)
                utta_dict["Test_Setup_Images"] =  process_and_resize_images(list(photo_pathes), max_width=900, quality=70)
                utta_dict['Test_Setup_Photo'] = True


    # entries to style the report
    utta_dict["TitleImageLeft"] = encode_png2html_string(os.path.abspath(r'Report_Templates/uTTA_Logo.png'))
    utta_dict["TitleImageRight"] = encode_png2html_string(os.path.abspath(r'Report_Templates/Your_Logo.png'))
    utta_dict["PDF_Printable_Report"] = False

    # transfer of information inside utta_data into the jinja2 information dict
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
    fig.add_trace(go.Scatter(x=utta_data.time_cooling, y=utta_data.zth[0,:], name=utta_dict["Channels"]['TSP0']['Name']))
    fig.update_xaxes(type="log", exponentformat="SI")
    fig.update_yaxes(type="log")
    fig.update_layout(width=1100, height=600, xaxis_title=r'Time / [s]', yaxis_title=r'Z<sub>th</sub> / [K/W]')

    utta_dict["PlotFullMeasurement"] = fig.to_html(full_html=False, include_plotlyjs=False)


    if utta_dict["Channels"]["TSP1"]["Name"]!="OFF" or utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
        fig = go.Figure()
        if utta_dict["Channels"]["TSP1"]["Name"]!="OFF":
            fig.add_trace(go.Scatter(x=utta_data.time_cooling, y=utta_data.zth[1,:], name=utta_dict["Channels"]['TSP1']['Name']))
        if utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
            fig.add_trace(go.Scatter(x=utta_data.time_cooling, y=utta_data.zth[2,:], name=utta_dict["Channels"]['TSP2']['Name']))

        fig.update_xaxes(type="log", exponentformat="SI")
        if np.min(utta_data.zth[1:2,:]) > 0.0:
            fig.update_yaxes(type="log")
        fig.update_layout(width=1100, height=600, xaxis_title=r'Time / [s]', yaxis_title=r'Z<sub>th</sub> / [K/W]')
        utta_dict["PlotZthCouplingCurves"] = fig.to_html(full_html=False, include_plotlyjs=False)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=utta_data.time_full, y=utta_data.udiode_full[0,:], name=utta_dict["Channels"]['TSP0']['Name'], yaxis='y1'))
    if utta_dict["Channels"]["TSP1"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.time_full, y=utta_data.udiode_full[1,:], name=utta_dict["Channels"]['TSP1']['Name'], yaxis='y1'))
    if utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.time_full, y=utta_data.udiode_full[2,:], name=utta_dict["Channels"]['TSP2']['Name'], yaxis='y1'))
    fig.add_trace(go.Scatter(x=utta_data.time_full, y=utta_data.current_full, name="Current", yaxis='y2'))
    fig.update_xaxes(exponentformat="SI")
    fig.update_layout(width=1100, height=600, xaxis_title="Time / [s]", yaxis_title="Diode Voltage / [V]",  
                      yaxis2=dict(title='Current / [A]',overlaying='y',side='right'))
    utta_dict["PlotFullMeasDiode"] = fig.to_html(full_html=False, include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=utta_data.time_full, y=utta_data.udiode_cooling[0,:], name=utta_dict["Channels"]['TSP0']['Name']))
    if utta_dict["Channels"]["TSP1"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.time_full, y=utta_data.udiode_cooling[1,:], name=utta_dict["Channels"]['TSP1']['Name']))
    if utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.time_full, y=utta_data.udiode_cooling[2,:], name=utta_dict["Channels"]['TSP2']['Name']))
    fig.update_xaxes(type="log", exponentformat="SI")

    fig.update_layout(width=1100, height=600, xaxis_title="Time / [s]", yaxis_title="Diode Voltage / [V]")
    utta_dict["PlotCoolingMeasDiode"] = fig.to_html(full_html=False, include_plotlyjs=False)

    utta_dict["PlotStartInterpolation"] = interpol_plot(utta_data, utta_dict)

    report = template.render(utta_dict)
    with open(filename, mode="w", encoding="utf-8") as output:
        output.write(report)

    print("\033[94mReport written\033[0m")

    os.startfile(filename)

def encode_png2html_string(imagepath:str) -> str:
    ''' Encodes a given png-file into a base64 encoded string which is then returned.
    Args:
        imagepath (string) : Path to png-file to be encoded
    Returns:
        (string) The base64 encoded png file
    '''

    if imagepath.lower().endswith('.png'):
        img_base64 = base64.b64encode(open(imagepath,'rb').read())
        img_base64 = img_base64.decode()

        return '<img src="data:image/png;base64,' + img_base64 + '", height=70></img>'
    elif imagepath.lower().endswith('.jpg'):
        print("Encoding JPEG Image")
        img_base64 = base64.b64encode(open(imagepath,'rb').read())
        img_base64 = img_base64.decode()

        return '<img src="data:image/jpeg;base64,' + img_base64 + '"</img>'
    else:
        return '<p> No PNG-Image found! </p>'


def process_and_resize_images(image_paths: List[Union[str, Path]], max_width: int = 1200, quality: int = 75) -> List[str]:
    """Reads multiple images, resizes them proportionally if they exceed max_width,
    compresses them using the WebP format, and returns a list of ready-to-use 
    HTML <img> tags with Base64-encoded source strings.
    """
    html_snippets: List[str] = []
    
    for path in image_paths:
        # Open the image using Pillow
        try:
            with Image.open(path) as img:
                
                # WebP standard RGB mode is safer if no transparency is required.
                # Convert palette ('P') or transparent ('RGBA') images to standard 'RGB'.
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Proportional scaling: check if the image width exceeds the container limit
                if img.width > max_width:
                    w_percent: float = max_width / float(img.width)
                    h_size: int = int(float(img.height) * w_percent)
                    # Resize using high-quality LANCZOS resampling
                    img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
                
                # Create an in-memory byte buffer to avoid writing files to disk
                buffer: io.BytesIO = io.BytesIO()
                
                # Save the image into the buffer using WebP format and the specified quality
                img.save(buffer, format="WEBP", quality=quality)
                
                # Retrieve byte data from buffer and encode it to a Base64 ASCII string
                base64_encoded: str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Append the fully formatted HTML string to the results list
                html_snippets.append(f'<img src="data:image/webp;base64,{base64_encoded}" alt="Test Setup Image" />')
        except Exception as e:
            print(f"ERROR: Problem when resizing images: {e}")
    return html_snippets

def compress_curve(timebase:np.ndarray, data:np.ndarray, samples_decade:int) -> np.ndarray:
    ''' Compresses the measurement data to an array with a selectable number of points per decade.
    
    Args:
        timebase        (np.ndarray)    : Timebase from the uTTA data processing     
        data            (np.ndarray)    : Zth curve data from uTTA data processing
        samples_decade  (int)           : Number of samples per decade which shall be exported
    Returns:
        (np.ndarray)    first column is time, the following columns are interpolated Zth curves
    '''

    if not isinstance(samples_decade, int) or samples_decade <= 0:
        raise ValueError("Input 'samples_decade' must be a non-negative integer.")
    if samples_decade >= len(timebase):
        return []  # type: ignore

    # build the basic timebase for one decade. This will be reused and multiplied by the corresponding decade
    sub_timebase = np.power(10.0, np.linspace(0, 1/samples_decade * (samples_decade-1), samples_decade))

    time_multiplier = -6.0
    interpol_timebase = []
    while(True):    # make a little do-while loop...
        timestep = np.power(10.0, time_multiplier)
        segment_timebase =  timestep * sub_timebase
        time_multiplier += 1
        interpol_timebase.extend(segment_timebase)

        if np.max(interpol_timebase) > np.max(timebase):
            break

    filtered_timebase = [tim for tim in interpol_timebase if tim <= np.max(timebase)]
    
    if filtered_timebase[-1] < np.max(timebase):
        filtered_timebase.append(np.max(timebase))

    arr_width = len(data[:,0])  # check for the width of the array to do an interpolation for every column
    data_output = np.zeros(shape=(1+len(data[:,0]), len(filtered_timebase)))
    data_output[0, :] = filtered_timebase
    for col in range(1, arr_width+1):
        data_output[col, :] = np.interp(filtered_timebase, timebase, data[col-1, :])
    data_output = np.transpose(data_output)

    return data_output

def interpol_plot(utta_data, utta_dict):
    ''' Generates a nice looking plotly plot to show the starting point interpolation of the
    heated TSP. The plot includes two cursors to show where the interpolation start and endpoints were placed.
    Args:
        utta_data (utta_data) : uTTA measurement data
        outfilename (string)  : Path of the final report file
    Returns:
        None
    '''

    fig = go.Figure()

    interpol_plot_cutoff_idx = udpc.find_nearest(utta_data.time_cooling, 0.1)
    tb_show = np.sqrt(utta_data.time_cooling[0:interpol_plot_cutoff_idx])

    diode_temp_values = utta_data.t_dio_raw[0,:]

    fig.add_trace(go.Scatter(x=tb_show, y=diode_temp_values[0:interpol_plot_cutoff_idx], name=utta_dict["Channels"]['TSP0']['Name']))

    interp_len = len(utta_data.t_dio_start_interpolation)

    min_y = np.min(diode_temp_values[0:interpol_plot_cutoff_idx])

    interp_start = (np.sqrt(utta_data.time_cooling[0:interpol_plot_cutoff_idx]) * utta_data.InterpolationFactorM +
                    utta_data.InterpolationOffset)
    
    interp_cutoff_idx = udpc.find_nearest(interp_start, min_y)

    interp_cutoff_idx = np.min([interp_cutoff_idx, interpol_plot_cutoff_idx])

    fig.add_trace(go.Scatter(x=tb_show[0:interp_cutoff_idx], y=interp_start[0:interp_cutoff_idx], name="Interpolated"))

    fig.update_xaxes(exponentformat="SI")
    # TODO: Stabilize the sometimes inconsistent rendering of LaTeX axis labels
    fig.update_layout(width=1100, height=600, xaxis_title=r'$\sqrt{\text{Time}} / [\sqrt{s}]$', yaxis_title=r'$\Delta\text{Temperature / [°C]}$')
    fig.add_vline(x=np.sqrt(utta_data.InterpolationTStart), annotation_text=r'$t_{cut}$', annotation_position="top")
    fig.add_vline(x=np.sqrt(utta_data.InterpolationTEnd), annotation_text=r'$t_{end}$', annotation_position="bottom")
    return fig.to_html(full_html=False, include_plotlyjs=False)
