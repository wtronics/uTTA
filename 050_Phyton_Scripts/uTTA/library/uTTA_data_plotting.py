#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    utta_data_plotting.py
Description:    Specialized and custimizable plotting utility for generating
                diagrams with matplotlib. These functions can be used withi
                GUIs as well as stand alone.

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

from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends._backend_tk as nav_toolbar
import tkinter as tk
import ttkbootstrap as ttk
import numpy as np

class UttaPlotConfiguration:
    """A class to save the plot configuration and the data for plotting a single graph.
    This class can be used as return value from functions which provide data to a GUI
    """    
    def __init__(self, data:list[dict]|dict, title:str, x_label:str, y_label:str, plot_type:str='line',
                 x_scale:str='linear',x_scale_formatter = None , y_scale:str='linear', y_scale_formatter = None, style=None,
                 secondary_data:list[dict]|dict|None=None, secondary_y_label:str|None=None):
        """Initialization routine of the plot configuration

        Args:
            data (list[dict] | dict): X-Y data for the primary Y-axis provided as a list of dictionaries
                                      Each dictionary carries the following information:
                                      -x_data (list[]): The x-axis data points
                                      -y_data (list[]): The y-axis data points
                                      -label (str): The plot label for this plot line
                                      -axis (int): The axis number the data is printed on (starting at 0)
                                      -style (dict[str,str]): Styling information for the graph line e.g. {'color':'blue', 'marker':'x'}
            title (str): The overall plot title for the graph
            x_label (str): x-label text appearing on the x-axis
            y_label (str): y-label text on the primary y-axis
            plot_type (str, optional): The tpye of plot (Available: 'dual_y_axis' and 'line'). Defaults to 'line'.
            x_scale (str, optional): Defines the x-axis scaling (Available: 'linear' and 'log'). Defaults to 'linear'.
            x_scale_formatter (_type_, optional): Use a special formatter for the x-scale grid. Defaults to None.
            y_scale (str, optional): Defines the y-axis scaling (Available: 'linear' and 'log'). Defaults to 'linear'.
            y_scale_formatter (_type_, optional): Use a special formatter for the y-scale grid. Defaults to None.
            secondary_data (list[dict] | dict | None, optional):  X-Y data for the secondary Y-axis provided as a list of dictionaries. Defaults to None.
                                      Each dictionary carries the following information:
                                      -x_data (list[]): The x-axis data points
                                      -y_data (list[]): The y-axis data points
                                      -label (str): The plot label for this plot line
                                      -axis (int): The axis number the data is printed on (starting at 0)
                                      -style (dict[str,str]): Styling information for the graph line e.g. {'color':'blue', 'marker':'x'} 
            secondary_y_label (str | None, optional): y-label text on the secondary y-axis. Defaults to None.
        """        

        # TODO: find out if 'axis' in primary and secondary data is really needed.
        self.plot_type = plot_type
        self.data = data
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.x_scale = x_scale
        self.x_scale_formatter = x_scale_formatter
        self.y_scale = y_scale
        self.y_scale_formatter = y_scale_formatter
        self.style = style or {}  # for optional use of matplotlib styling parameters
        self.secondary_data = secondary_data
        self.secondary_y_label = secondary_y_label or {}


class UttaPlotData:
    """A dynamic plotting engine for easy integration of various data sources into a matplotlib
    graphing object with multiple subplots. The engine can also be used to run without a GUI if needed.
    """    
    def __init__(self, parent:ttk.Frame|None, size:tuple[int,int], rows:int, cols:int, dpi:float=96, padding:float=3.0, no_gui:bool=False):
        """Initializes a new dynamic matplotlib multiplot instance. 

        Args:
            parent (ttk.Frame|None): The parent object the plot is integrated into. For non-GUI use this can be set to None.
            size (tuple[int,int]): Size of the plot window in pixels.
            rows (int): Number of subplot rows
            cols (int): Number of subplot columns
            dpi (float, optional): Screen resolution in dots per inch. Defaults to 96.
            padding (float, optional): Defines the padding around the subplots in pixels. Defaults to 3.0.
            no_gui (bool, optional): Set this flag to True in case the instance is not run from a GUI. Defaults to False.
        """              

        # Creates the Matplotlib-Figure and the subplots in the requested grid
        self.parent = parent
        # self.figure = None
        self.axes = []
        self.plot_mapping = []
        self.size = size
        self.dpi = dpi
        self.no_gui = no_gui

        # matplotlib default settings
        mpl.rcParams['axes.labelsize'] = 8
        mpl.rcParams['legend.fontsize'] = 7
        mpl.rcParams['font.size'] = 9.5
        mpl.rcParams['xtick.labelsize'] = 8
        mpl.rcParams['ytick.labelsize'] = 8
        mpl.rcParams['text.usetex'] = False

        if self.no_gui:
            fig_size_inch = (size[0] / dpi, size[1] / dpi)
            self.figure, self.ax_array = plt.subplots(rows, cols, figsize=fig_size_inch, dpi=dpi)

            if rows * cols > 1:
                self.axes = self.ax_array.flatten().tolist() # type: ignore
            else:
                self.axes = [self.ax_array]
        else:
            self.figure = Figure(figsize=(size[0] / dpi, (size[1]-10) / dpi), dpi=96, tight_layout = True)

            for i in range(rows * cols):
                ax = self.figure.add_subplot(rows, cols, i + 1)
                self.axes.append(ax)
        
            self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, padx=10, pady=10)

            # Toolbar Frame
            toolbar_frame = ttk.Frame(master=parent)
            toolbar_frame.pack(fill=tk.X, padx=10, pady=10)
            self.toolbar = nav_toolbar.NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()
        self.figure.tight_layout(pad=padding)

    def update_plots(self):
        """Updates all defined subplots within this instance.
        """        

        for i, ax in enumerate(self.axes): # type: ignore
            ax.clear()
            mapping_item = next((item for item in self.plot_mapping if item[0] == i), None)

            if mapping_item:
                config_func = mapping_item[1]
                config = config_func()  # calls back the function to get the next configuration object
                num_plots = 0

                # ==========================================================
                # Logic for plots with 2 Y-Axis
                # ==========================================================
                if config.plot_type == 'dual_y_axis':
                    ax2 = ax.twinx()

                    # Axis 1: Primary data
                    for line in config.data:
                        ax.plot(line['x_data'],line['y_data'],label=line['label'],**line['style'])
                        num_plots += 1
                    ax.set_ylabel(config.y_label)

                    # Axis 2: Secondary Data
                    for sec_line in config.secondary_data:
                        ax2.plot(sec_line['x_data'],sec_line['y_data'],label=sec_line['label'],**sec_line['style'])
                        num_plots += 1
                    ax2.set_ylabel(config.secondary_y_label)

                    # Scaling and axis synchronisation
                    ax.set_xscale(config.x_scale)
                    ax.set_yscale(config.y_scale)
                    ax2.set_yscale(config.y_scale)

                    if config.x_scale_formatter:
                        ax.xaxis.set_major_formatter(config.x_scale_formatter)

                    if config.y_scale_formatter:
                        ax.yaxis.set_major_formatter(config.y_scale_formatter)

                # Logic for line plots
                elif config.plot_type == 'line':

                    for curve in config.data:
                        ax.plot(curve['x_data'], curve['y_data'], label=curve['label'], **curve.get('style', {}))
                        num_plots += 1
                        # In case the plotted data have negative values, the y-axis scaling will be automatically changed to linear scale
                        if config.y_scale == 'log' and np.min(curve['y_data']) <= 0.0:
                            config.y_scale = 'linear'

                    ax.set_xscale(config.x_scale)
                    ax.set_yscale(config.y_scale)
                    
                    if config.x_scale == 'log':
                        ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=[1.0], numticks=999))
                        ax.grid(True , axis='x', which='major', ls="-", color='grey') 
                        ax.grid(True , axis='x', which="minor", alpha=0.7)

                # Common settings for all plots + the legend
                if num_plots > 0:       # check if anything was printed into the plot. Otherwise mpl will generate an error
                    ax.legend(loc='best', fontsize='small')
                ax.set_title(config.title)
                ax.grid(axis="both")
                ax.set_xlabel(config.x_label)
                ax.set_ylabel(config.y_label)

        if self.no_gui:
            plt.draw()
            plt.show() # blocking plot window is opened here
        else:
            self.canvas.draw()


