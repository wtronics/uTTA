from jinja2 import Template, Environment, FileSystemLoader, StrictUndefined, Undefined
#import plotly.express as px
import plotly.graph_objects as go
import os
import pandas as pd
import numpy as np
import library.uTTA_data_processing as udpc
from quantiphy import Quantity
import base64

def export(utta_data, outfilename):

    environment = Environment(loader=FileSystemLoader("Report_Templates/"))
    template = environment.get_template("Master_Template.html")
    filename = outfilename

    utta_dict = {}

    # entries to style the report
    utta_dict["TitleImageLeft"] = encode_png2html_string(os.path.abspath(r'Report_Templates/uTTA_Logo.png'))
    utta_dict["TitleImageRight"] = encode_png2html_string(os.path.abspath(r'Report_Templates/Your_Logo.png'))
    utta_dict["PDF_Printable_Report"] = False

    # transfer of information inside utta_data into the jinja2 information dict
    utta_dict["adc_timebase"] = utta_data.adc_timebase
    utta_dict["adc"] = utta_data.adc
    utta_dict["cooling_start_index"] = utta_data.cooling_start_index
    utta_dict["Channels"] = utta_data.meta_data.Channels
    utta_dict["Zth_Table"] = compress_curve(utta_data.adc_timebase_cooling, utta_data.zth, 6)

    utta_dict["Measurement_Info"] = utta_data.meta_data.Measurement
    utta_dict["Cal_Data"] = utta_data.meta_data.CalData

    utta_dict["I_Heat"] = utta_data.i_heat
    utta_dict["I_Sense"] = utta_data.meta_data.Isense
    utta_dict["P_Heat"] = utta_data.p_heat
    utta_dict["T_Preheat"] = utta_data.meta_data.TPreheat
    utta_dict["T_Heating"] = utta_data.meta_data.THeating
    utta_dict["T_Cooling"] = utta_data.meta_data.TCooling

    utta_dict["InterpolTStart"] = '{val}'.format(val=Quantity(utta_data.InterpolationTStart, "s")) 
    utta_dict["InterpolTEnd"] = '{val}'.format(val=Quantity(utta_data.InterpolationTEnd, "s")) 
    utta_dict["InterpolFactor"] = utta_data.InterpolationFactorM
    utta_dict["InterpolOffset"] = utta_data.InterpolationOffset
    utta_dict["InterpolDieSize"] = utta_data.EstimatedDieSize

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=utta_data.adc_timebase_cooling, y=utta_data.zth[0,:], name=utta_dict["Channels"]['TSP0']['Name']))
    fig.update_xaxes(type="log", exponentformat="SI")
    fig.update_yaxes(type="log")
    fig.update_layout(width=1100, height=600, xaxis_title=r'Time / [s]', yaxis_title=r'Z<sub>th</sub> / [K/W]')

    utta_dict["PlotFullMeasurement"] = fig.to_html(full_html=False, include_plotlyjs=False)


    if utta_dict["Channels"]["TSP1"]["Name"]!="OFF" or utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
        fig = go.Figure()
        if utta_dict["Channels"]["TSP1"]["Name"]!="OFF":
            fig.add_trace(go.Scatter(x=utta_data.adc_timebase_cooling, y=utta_data.zth[1,:], name=utta_dict["Channels"]['TSP1']['Name']))
        if utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
            fig.add_trace(go.Scatter(x=utta_data.adc_timebase_cooling, y=utta_data.zth[2,:], name=utta_dict["Channels"]['TSP2']['Name']))

        fig.update_xaxes(type="log", exponentformat="SI")
        fig.update_yaxes(type="log")
        fig.update_layout(width=1100, height=600, xaxis_title=r'Time / [s]', yaxis_title=r'Z<sub>th</sub> / [K/W]')
        utta_dict["PlotZthCouplingCurves"] = fig.to_html(full_html=False, include_plotlyjs=False)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=utta_data.adc_timebase, y=utta_data.adc[0,:], name=utta_dict["Channels"]['TSP0']['Name'], yaxis='y1'))
    if utta_dict["Channels"]["TSP1"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.adc_timebase, y=utta_data.adc[1,:], name=utta_dict["Channels"]['TSP1']['Name'], yaxis='y1'))
    if utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.adc_timebase, y=utta_data.adc[2,:], name=utta_dict["Channels"]['TSP2']['Name'], yaxis='y1'))
    fig.add_trace(go.Scatter(x=utta_data.adc_timebase, y=utta_data.adc[3,:], name="Current", yaxis='y2'))
    fig.update_xaxes(exponentformat="SI")
    fig.update_layout(width=1100, height=600, xaxis_title="Time / [s]", yaxis_title="Diode Voltage / [V]",  
                      yaxis2=dict(title='Current / [A]',overlaying='y',side='right'))
    utta_dict["PlotFullMeasDiode"] = fig.to_html(full_html=False, include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=utta_data.adc_timebase_cooling, y=utta_data.adc_cooling[0,:], name=utta_dict["Channels"]['TSP0']['Name']))
    if utta_dict["Channels"]["TSP1"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.adc_timebase_cooling, y=utta_data.adc_cooling[1,:], name=utta_dict["Channels"]['TSP1']['Name']))
    if utta_dict["Channels"]["TSP2"]["Name"]!="OFF":
        fig.add_trace(go.Scatter(x=utta_data.adc_timebase_cooling, y=utta_data.adc_cooling[2,:], name=utta_dict["Channels"]['TSP2']['Name']))
    fig.update_xaxes(type="log", exponentformat="SI")

    fig.update_layout(width=1100, height=600, xaxis_title="Time / [s]", yaxis_title="Diode Voltage / [V]")
    utta_dict["PlotCoolingMeasDiode"] = fig.to_html(full_html=False, include_plotlyjs=False)

    utta_dict["PlotStartInterpolation"] = interpol_plot(utta_data, utta_dict)

    report = template.render(utta_dict)
    with open(filename, mode="w", encoding="utf-8") as output:
        output.write(report)

    print("\033[94mReport written\033[0m")



def encode_png2html_string(imagepath):

    if imagepath.endswith('.png'):
        img_base64 = base64.b64encode(open(imagepath,'rb').read())
        img_base64 = img_base64.decode()

        return '<img src="data:image/png;base64,' + img_base64 + '", height=70></img>'
    else:
        return '<p> No PNG-Image found! </p>'

def compress_curve(timebase, data, samples_decade):


    if not isinstance(samples_decade, int) or samples_decade <= 0:
        raise ValueError("Input 'samples_decade' must be a non-negative integer.")
    if samples_decade >= len(timebase):
        return

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

    fig = go.Figure()

    interpol_plot_cutoff_idx = udpc.find_nearest(utta_data.adc_timebase_cooling, 0.1)
    tb_show = np.sqrt(utta_data.adc_timebase_cooling[0:interpol_plot_cutoff_idx])

    diode_temp_values = utta_data.t_dio_raw[0,:]

    fig.add_trace(go.Scatter(x=tb_show, y=diode_temp_values[0:interpol_plot_cutoff_idx], name=utta_dict["Channels"]['TSP0']['Name']))

    interp_len = len(utta_data.t_dio_start_interpolation)

    min_y = np.min(diode_temp_values[0:interpol_plot_cutoff_idx])

    interp_start = (np.sqrt(utta_data.adc_timebase_cooling[0:interpol_plot_cutoff_idx]) * utta_data.InterpolationFactorM +
                    utta_data.InterpolationOffset)
    
    interp_cutoff_idx = udpc.find_nearest(interp_start, min_y)

    interp_cutoff_idx = np.min([interp_cutoff_idx, interpol_plot_cutoff_idx])

    fig.add_trace(go.Scatter(x=tb_show[0:interp_cutoff_idx], y=interp_start[0:interp_cutoff_idx], name="Interpolated"))

    fig.update_xaxes(exponentformat="SI")
    fig.update_layout(width=1100, height=600, xaxis_title=r'$\sqrt{\text{Time}} / [\sqrt{s}]$', yaxis_title=r'$\Delta\text{Temperature / [°C]}$')
    fig.add_vline(x=np.sqrt(utta_data.InterpolationTStart), annotation_text=r'$t_{cut}$', annotation_position="top")
    fig.add_vline(x=np.sqrt(utta_data.InterpolationTEnd), annotation_text=r'$t_{end}$', annotation_position="bottom")
    return fig.to_html(full_html=False, include_plotlyjs=False)
