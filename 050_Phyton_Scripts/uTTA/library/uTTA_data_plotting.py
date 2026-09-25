#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    utta_data_plotting.py
Description:    Specialized and customizable plotting utility for generating
                diagrams with matplotlib. These functions can be used within
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
import math
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.backends._backend_tk as nav_toolbar
import matplotlib.pyplot as plt
import numpy as np
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import LogLocator


class UttaPlotConfiguration:
    """A class to save the plot configuration and the data for plotting a single graph.
    This class can be used as return value from functions which provide data to a GUI.
    """
    def __init__(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], title: str, x_label: str, y_label: str, plot_type: str = "line",
                 x_scale: str = "linear", x_scale_formatter: Optional[Any] = None, y_scale: str = "linear", y_scale_formatter: Optional[Any] = None, style: Optional[Dict[str, Any]] = None,
                 secondary_data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None, secondary_y_label: Optional[str] = None):
        """Initializes the plot configuration.

        Args:
            data (Union[List[Dict[str, Any]], Dict[str, Any]]): X-Y data for primary Y-axis.
            title (str): Overall plot title.
            x_label (str): Label text for x-axis.
            y_label (str): Label text for primary y-axis.
            plot_type (str): Type of plot ('line' or 'dual_y_axis'). Defaults to 'line'.
            x_scale (str): Scaling for x-axis ('linear' or 'log'). Defaults to 'linear'.
            x_scale_formatter (Optional[Any]): Custom formatter for x-scale. Defaults to None.
            y_scale (str): Scaling for y-axis ('linear' or 'log'). Defaults to 'linear'.
            y_scale_formatter (Optional[Any]): Custom formatter for y-scale. Defaults to None.
            style (Optional[Dict[str, Any]]): Styling information dictionary. Defaults to None.
            secondary_data (Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]): Secondary Y-axis data. Defaults to None.
            secondary_y_label (Optional[str]): Label text for secondary y-axis. Defaults to None.
        """
        # Ensure data and secondary_data are stored as lists internally for uniform iteration
        if isinstance(data, dict):
            self.data = [data]
        else:
            self.data = data

        if isinstance(secondary_data, dict):
            self.secondary_data = [secondary_data]
        else:
            self.secondary_data = secondary_data or []
        self.plot_type = plot_type
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.x_scale = x_scale
        self.x_scale_formatter = x_scale_formatter
        self.y_scale = y_scale
        self.y_scale_formatter = y_scale_formatter
        self.style = style or {} # for optional use of matplotlib styling parameters
        self.secondary_y_label = secondary_y_label or ""


class UttaPlotData:
    """ Dynamic plotting engine integrating data sources into matplotlib graphing objects. The engine can also be used to run without a GUI if needed.
    """
    def __init__(self, parent: Optional[ttk.Frame], size: Tuple[int, int], rows: int, cols: int, dpi: float = 96, padding: float = 3.0, no_gui: bool = False):
        """ Initializes a new dynamic matplotlib multiplot instance.

        Args:
            parent (Optional[ttk.Frame]): Parent GUI frame object. Set to None for non-GUI mode.
            size (Tuple[int, int]): Dimensions of the plot window in pixels (width, height).
            rows (int): Number of subplot rows.
            cols (int): Number of subplot columns.
            dpi (float): Screen resolution in dots per inch. Defaults to 96.0.
            padding (float): Padding around subplots in pixels. Defaults to 3.0.
            no_gui (bool): Set to True if running headlessly without a GUI. Defaults to False.
        """

        # Creates the Matplotlib-Figure and the subplots in the requested grid
        self.parent = parent
        self.size = size
        self.dpi = dpi
        self.no_gui = no_gui
        self.padding = padding
        
        # Save grid dimensions as state for later
        self.rows = rows
        self.cols = cols

        # Independent plot annotations
        self.vertical_lines: List[Dict[str, Any]] = []  # List of dicts with vertical lines
        self.plot_labels: List[Dict[str, Any]] = []     # List of dicts with text labels
        
        # Axis mapping: [{"row": r, "col": c, "func": config_func, "ax": ax}, ...]
        self.plot_mapping: List[Dict[str, Any]] = []
        self._grid_needs_rebuild = True  # Flag to control when the grid must be rebuilt

        # Curve visibility cache: {(ax_index, "Curve-Label"): True/False}
        self._visibility_cache: Dict[Tuple[int, str], bool] = {}

        # Legend element mapping to plot lines
        self._leg_to_plot_line: Dict[Any, Any] = {}

        # Matplotlib default configurations
        mpl.rcParams["axes.labelsize"] = 8
        mpl.rcParams["legend.fontsize"] = 7
        mpl.rcParams["font.size"] = 9.5
        mpl.rcParams["xtick.labelsize"] = 8
        mpl.rcParams["ytick.labelsize"] = 8
        mpl.rcParams["text.usetex"] = False

        # Backend initialization
        if self.no_gui:
            fig_size_inch = (size[0] / dpi, size[1] / dpi)
            self.figure = plt.figure(figsize=fig_size_inch, dpi=dpi)
        else:
            self.figure = Figure(figsize=(size[0] / dpi, size[1] / dpi), dpi=96)
            # Initialize Canvas
            self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Toolbar Frame
            toolbar_frame = ttk.Frame(master=parent)
            toolbar_frame.pack(fill=tk.X, padx=10, pady=10)
            self.toolbar = nav_toolbar.NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()

        # Connect the Matplotlib pick-event handler
        self.figure.canvas.mpl_connect("pick_event", self._on_legend_pick)


    def update_plots(self) -> None:
        """ Redraws and updates all defined subplots within this instance.
        """  
        # If mappings were added or items were deleted -> Rebuild Grid
        if self._grid_needs_rebuild:
            self._rebuild_grid()

        # Clear the mapping dictionary before redraw
        self._leg_to_plot_line.clear()

        # Iterate through the active mapping
        for ax_idx, item in enumerate(self.plot_mapping):
            ax = item["ax"]
            if ax is None:
                continue

            ax.clear()
            config: UttaPlotConfiguration = item["func"]()
            num_plots = 0
            
            # Lists to collect the line-objects for the legend
            primary_lines = []
            secondary_lines = []

            # ==========================================================
            # Logic for dual Y-axis plots
            # ==========================================================
            if config.plot_type == "dual_y_axis":
                ax2 = ax.twinx()
                
                # Axis 1: Primary data
                for line in config.data:
                    lbl = line.get("label", "Data")
                    # Check the visibility cache (standard: True)
                    is_visible = self._visibility_cache.setdefault((ax_idx, lbl), True)
                    
                    (l,) = ax.plot(line["x_data"], line["y_data"], label=lbl, visible=is_visible, **line.get("style", {}))
                    primary_lines.append((l, (ax_idx, lbl)))
                    num_plots += 1
                ax.set_ylabel(config.y_label)
                
                # Secondary axis
                for sec_line in config.secondary_data:
                    lbl = sec_line.get("label", "Data")
                    is_visible = self._visibility_cache.setdefault((ax_idx, lbl), True)
                    
                    (l,) = ax2.plot(sec_line["x_data"], sec_line["y_data"], label=lbl, visible=is_visible, **sec_line.get("style", {}))
                    secondary_lines.append((l, (ax_idx, lbl)))
                    num_plots += 1
                ax2.set_ylabel(config.secondary_y_label)
                # Scaling and axis synchronisation
                ax.set_xscale(config.x_scale)
                ax.set_yscale(config.y_scale)
                ax2.set_yscale(config.y_scale)
                # Apply x and y formatters if specified
                if config.x_scale_formatter:
                    ax.xaxis.set_major_formatter(config.x_scale_formatter)
                if config.y_scale_formatter:
                    ax.yaxis.set_major_formatter(config.y_scale_formatter)

            # ==========================================================
            # Logic for standard line plots
            # ==========================================================
            elif config.plot_type == "line":

                for curve in config.data:
                    lbl = curve.get("label", "Data")
                    is_visible = self._visibility_cache.setdefault((ax_idx, lbl), True)
                    
                    (l,) = ax.plot(curve["x_data"], curve["y_data"], label=lbl, visible=is_visible, **curve.get("style", {}))
                    primary_lines.append((l, (ax_idx, lbl)))
                    num_plots += 1
                    # Fallback to Linear in case the plotted data have negative values
                    if config.y_scale == "log" and len(curve["y_data"]) > 0:
                        if np.min(curve["y_data"]) <= 0.0:
                            config.y_scale = "linear"
                        
                ax.set_xscale(config.x_scale)
                ax.set_yscale(config.y_scale)
                if config.x_scale == "log":
                    ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=[1.0], numticks=999))
                    ax.grid(True, axis="x", which="major", ls="-", color="grey")
                    ax.grid(True, axis="x", which="minor", alpha=0.7)

            # ==========================================================
            # Plot independant markers and labels
            # ==========================================================
            current_row = item["row"]
            current_col = item["col"]

            # Vertical lines for this specific plot
            for vline in self.vertical_lines:
                if vline["row"] == current_row and vline["col"] == current_col:
                    ax.axvline(x=vline["x"], **vline["kwargs"])
                    if "label" in vline["kwargs"]:
                        num_plots += 1

            # Plot independent text labels
            for label in self.plot_labels:
                if label["row"] == current_row and label["col"] == current_col:
                    ax.text(label["x"], label["y"], label["text"], **label["kwargs"])

            # Setup legends and interactivity
            if num_plots > 0:       # check if anything was printed into the plot. Otherwise mpl will generate an error
                legend = ax.legend(loc="best", fontsize="small")
                
                # combine the legend entries from the lists with the real curve-objects
                # Combine primary and secondary lines at once
                all_drawn_lines = primary_lines + secondary_lines
                
                for leg_line, (plot_line, cache_key) in zip(legend.get_lines(), all_drawn_lines):
                    leg_line.set_picker(True)
                    leg_line.set_pickradius(10)
                    
                    # Save the mapping to the dictionary
                    self._leg_to_plot_line[leg_line] = (plot_line, cache_key)
                    
                    # In case the curve is invisible, change the alpha within the legend accordingly
                    if not plot_line.get_visible():
                        leg_line.set_alpha(0.2)

            ax.set_title(config.title)
            ax.grid(axis="both")
            ax.set_xlabel(config.x_label)
            ax.set_ylabel(config.y_label)

        # Refresh of layout
        self.figure.tight_layout(pad=self.padding)
        if self.no_gui:
            plt.draw()
            # Suppress plt.show() if running under non-interactive backends like 'Agg'
            if mpl.get_backend().lower() != "agg":
                plt.show()  # blocking plot window is opened here
        else:
            self.canvas.draw()

    def _rebuild_grid(self) -> None:
        """ Deletes all existing axes and rebuilds the grid specified by rows and cols.
        """
        for ax in self.figure.get_axes():
            ax.remove()

        # Define a new gridspec
        if self.rows > 0 and self.cols > 0:
            gs = GridSpec(self.rows, self.cols, figure=self.figure)

            # Add a new axis for every registered mapping within the new grid
            for item in self.plot_mapping:
                r, c = item["row"], item["col"]
                # Check if the mapping is still within the valid range
                if r < self.rows and c < self.cols:
                    ax = self.figure.add_subplot(gs[r, c])
                    item["ax"] = ax
        self._grid_needs_rebuild = False

    def add_plot_mapping(self, row: int, col: int, config_func: Callable[[], UttaPlotConfiguration]) -> None:
        """ Registers a plot callback function at a specified grid position.

        Args:
            row (int): Row index (0-indexed).
            col (int): Column index (0-indexed).
            config_func (Callable[[], UttaPlotConfiguration]): Callback returning plot configuration.
        """
        existing_item = next((item for item in self.plot_mapping if item["row"] == row and item["col"] == col), None)
        
        if existing_item:
            # Update the plot function in case the mapping existed
            existing_item["func"] = config_func
        else:
            self.plot_mapping.append({"row": row, "col": col, "func": config_func, "ax": None})
            self._grid_needs_rebuild = True

    def delete_column(self, col_index: int) -> None:
        """ Removes a column at runtime and shifts remaining plots to fill the gap.

        Args:
            col_index (int): Index of the column to remove (0-indexed).
        """
        if col_index >= self.cols or col_index < 0:
            return  # Invalid Index

        # Remove all existings mapping within the column to be deleted
        self.plot_mapping = [item for item in self.plot_mapping if item["col"] != col_index]

        # Move all remaining plots right of the deleted column to the left
        for item in self.plot_mapping:
            if item["col"] > col_index:
                item["col"] -= 1

        # Reduce the number of columns
        self.cols -= 1

        # Regenerate the grid and update the plots
        self._grid_needs_rebuild = True
        self.update_plots()
    
    def delete_row(self, row_index: int) -> None:
        """ Removes a row at runtime and shifts remaining plots upwards.
        
        Args:
            row_index (int): Index of the row to remove (0-indexed).
        """
        if row_index >= self.rows or row_index < 0:
            return  # Invalid Index

        #  Remove all existings mapping within the row to be deleted
        self.plot_mapping = [item for item in self.plot_mapping if item["row"] != row_index]

        # Move all remaining plots below of the deleted row upwards
        for item in self.plot_mapping:
            if item["row"] > row_index:
                item["row"] -= 1

        # Reduce number of total rows
        self.rows -= 1
        
        # Regenerate the grid and update the plots
        self._grid_needs_rebuild = True
        self.update_plots()
    
    def add_column(self) -> None:
        """Adds an empty column to the grid. Plots need to be mapped after adding the column.
        The new column is added on the right side
        """
        self.cols += 1
        self._grid_needs_rebuild = True
        self.update_plots()
    
    def add_row(self) -> None:
        """Adds an empty row to the grid. Plots need to be mapped after adding the row.
        The new row is added on the bottom
        """
        self.rows += 1
        self._grid_needs_rebuild = True
        self.update_plots()

    def add_vertical_line(self, row: int, col: int, x: float, **kwargs):
        """Adds a vertical line annotation to a specific plot location.

        Args:
            row (int): Row index (0-indexed).
            col (int): Column index (0-indexed).
            x (float): X-coordinate for the vertical line.
            **kwargs (Any): Additional matplotlib kwargs (e.g. color='red', linestyle='--').
        """

        line_item = {"row": row, "col": col, "x": x, "kwargs": kwargs}

        for idx, item in enumerate(self.vertical_lines):
            if item["row"] == row and item["col"] == col and item["x"] == x:
                self.vertical_lines[idx] = line_item
                return

        self.vertical_lines.append(line_item)

    def add_plot_label(self, row: int, col: int, x: float, y: float, text: str, **kwargs):
        """ Adds text a a certain X-Y coordinate to the plot. 
        Args:
            row (int): The row the plot shall be drawn in. Index starts a 0
            col (int): The colum the plot shall be drawn in. Index starts a 0
            x (float): The x-position where the label shall be added
            y (float): The y-position where the label shall be added
            text (str): The text label to be added.
        kwargs example: fontsize=10, color="blue", weight="bold"
        """

        label_item = {"row": row, "col": col, "x": x, "y": y, "text": text, "kwargs": kwargs,}
        for idx, item in enumerate(self.plot_labels):
            if (
                item["row"] == row
                and item["col"] == col
                and math.isclose(item["x"], x, rel_tol=1e-9, abs_tol=1e-9)
                and math.isclose(item["y"], y, rel_tol=1e-9, abs_tol=1e-9)
            ):
                self.plot_labels[idx] = label_item
                return

        self.plot_labels.append(label_item)

    def clear_decorations(self):
        """ Clears all manually added vertical lines and text labels.
        """
        self.vertical_lines.clear()
        self.plot_labels.clear()

    
    def _on_legend_pick(self, event: Any) -> None:
        """ Toggles line visibility when clicking a legend item.
        """
        leg_line = event.artist
        if leg_line not in self._leg_to_plot_line:
            return

        # Find the matching real curve and its cache data
        plot_line, cache_key = self._leg_to_plot_line[leg_line]
        
        # Invert visibility
        new_visible = not plot_line.get_visible()
        plot_line.set_visible(new_visible)
        
        # Save new status to cache
        self._visibility_cache[cache_key] = new_visible
        
        # Give visual feedback within the legend (greyed out)
        leg_line.set_alpha(1.0 if new_visible else 0.2)
        
        # Redraw the canvas
        if self.no_gui:
            plt.draw()
        else:
            self.canvas.draw()