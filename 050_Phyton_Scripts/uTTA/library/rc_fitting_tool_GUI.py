#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    rc_fitting_tool_GUI.py
Description:    A graphical user interface for the thermal-network (https://github.com/erickschulz/thermal-network) tool.
                The backend is designed to be called from other Applications including handover of data to be fitted.

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           25.09.2026
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

import os
import re
import threading
import logging
import queue

import numpy as np
import tkinter as tk
import thermal_network as tn
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
import library.rc_circuit_representation as rc_schem
import library.export_spice as exp_spice

from tkinter import filedialog, messagebox
from typing import Callable, Any
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from quantiphy import Quantity


# Deactivate the search for accelerators like TPU or CUDA
os.environ["JAX_PLATFORMS"] = "cpu" 
os.environ["FLAGS_jax_backend_target"] = "cpu"

STD_GRAPH_COLORS: list[str] = [
    "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99", "#e31a1c",
    "#fdbf6f", "#ff7f00", "#cab2d6", "#6a3d9a", "#ffff99", "#b15928"
]


class ThreadSafeQueueHandler(logging.Handler):
    """Logging Handler that sends log records thread-safely into a queue for UI display.

    Attributes:
        log_queue (queue.Queue): Queue used to store formatted log records.
        widget_to_notify (tk.Widget): Tkinter widget that receives custom event notifications.
    """

    def __init__(self, log_queue: queue.Queue, widget_to_notify: tk.Widget) -> None:
        """Initializes the ThreadSafeQueueHandler.

        Args:
            log_queue (queue.Queue): Reference to the message queue.
            widget_to_notify (tk.Widget): Reference to the target widget for event generation.
        """        
        super().__init__()
        self.log_queue: queue.Queue = log_queue
        self.widget_to_notify: tk.Widget = widget_to_notify

    def emit(self, record: logging.LogRecord) -> None:
        """Formats and enqueues a log record, then triggers a virtual GUI event.

        Args:
            record (logging.LogRecord): The log record to be processed.
        """
        msg: str = self.format(record)
        self.log_queue.put(msg)

        try:
            self.widget_to_notify.event_generate("<<NewLogRecord>>", when="tail")
        except Exception:
            pass


class QueueTextLogger:
    """Cyclic reader of the queue within the GUI main thread for outputting into a text widget.

    Attributes:
        text_widget (tk.Text): Target Tkinter text widget to append log outputs.
        log_queue (queue.Queue): Source queue containing log strings.
    """

    def __init__(self, text_widget: tk.Text, log_queue: queue.Queue) -> None:
        """Initializes the QueueTextLogger.

        Args:
            text_widget (tk.Text): Tkinter Text widget to display log messages.
            log_queue (queue.Queue): Queue holding incoming log records.
        """
        self.text_widget: tk.Text = text_widget
        self.log_queue: queue.Queue = log_queue

    def poll_log_queue(self) -> None:
        """Polls the queue periodically using `widget.after()` from the main thread."""
        while True:
            try:
                record: str = self.log_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.text_widget.configure(state="normal")
                self.text_widget.insert("end", record + "\n")
                self.text_widget.see("end")  # Automatically scroll to the end
                self.text_widget.configure(state="disabled")

        # Rerun every 100ms
        self.text_widget.after(100, self.poll_log_queue)



class ThermalFittingWindow(ttk.Frame):
    """Main GUI window for fitting thermal impedance data to Foster/Cauer networks.

    Can be executed as a standalone Tkinter app or integrated into parent applications.

    Attributes:
        log_queue (queue.Queue): Queue used for capturing backend logs.
        on_fit_complete (Callable[[dict], None] | None): Callback executed after fitting completes.
        fitted_foster_params (list[tuple[float, float]]): Extracted list of (R, C) parameter pairs.
        fitted_network (FosterNetwork): Best-fit network representation object.
        fitting_time (np.ndarray): Processed time vector used during fitting.
        fitting_results (ModelSelectionResult): Detailed results across evaluated model orders.
        show_all_fits (bool): Flag specifying whether to display all evaluated models in plot.
        min_tau_s (float): Floor limit for thermal time constants in seconds.
        raw_data (np.ndarray | None): 2D array holding raw measurement data [time, Zth].
        gui_is_called (bool): Indicates if window was instantiated with external data.
    """

    def __init__(
        self, 
        parent: tk.Misc | None = None, 
        time_data: np.ndarray | list[float] | None = None, 
        zth_data: np.ndarray | list[float] | None = None, 
        min_order: int = 1,
        max_order: int = 5, 
        on_fit_complete: Callable[[dict], None] | None = None, 
        auto_fit: bool = False,
        **kwargs: Any,
    ) -> None:   
        """Initializes the ThermalFittingWindow frame.

        Args:
            parent (tk.Tk | ttk.Window | None, optional): Parent Tkinter widget. Defaults to None.
            time_data (np.ndarray | list[float] | None, optional): Input time array in seconds. Defaults to None.
            zth_data (np.ndarray | list[float] | None, optional): Input Zth array in K/W. Defaults to None.
            min_order (int, optional): Sets the minimum order of RC-Layers to be fitted. Defaults to 1.
            max_order (int, optional): Sets the maximum order of RC-Layers to be fitted. Defaults to 5.
            on_fit_complete (Callable[[dict], None] | None, optional): Callback for passing results back. Defaults to None.
            auto_fit (bool, optional): Automatically start thread upon initialization. Defaults to False.
        """
        super().__init__(master=parent, **kwargs)

        # Create a queue for logging messages
        self.log_queue: queue.Queue = queue.Queue()

        self.on_fit_complete: Callable[[dict], None] | None = on_fit_complete
        self.fitted_foster_network: tn.networks.FosterNetwork|None = None
        self.fitted_cauer_network: tn.networks.CauerNetwork|None = None
        self.displayed_network = "foster"
        self.fitting_time: np.ndarray
        self.fitting_results: tn.fitting.ModelSelectionResult 
        self.show_fitted_plots: int = -1

        self.min_tau_s: float = 1e-4   # Standard Minimum Tau is 100µs

        # Do min and max for both parameters to prevent twisted parameters
        self.min_layer = min(min_order, max_order)
        self.max_layer = max(min_order, max_order)
            

        self.gui_is_called: bool = False
        self.raw_data: np.ndarray | None = None

        # In case the window is started without parent (Standalone),
        # hide the standard root window created by tkinter.       
        # Data transfer
        if time_data is not None and zth_data is not None:
            self.gui_is_called = True
            self.raw_data = np.column_stack((np.asarray(time_data), np.asarray(zth_data)))
        else:
            self.raw_data = None
            self.gui_is_called = False

        self.circuit_canvas: FigureCanvasTkAgg | None = None
        self.circuit_canvas_widget: tk.Widget | None = None

        self._build_ui()

        self._setup_logging()

        if self.raw_data is not None:
            self._plot_raw_data()
            self._calc_min_tau()
            if auto_fit:
                self.after(300, self.start_fitting_thread)


    def _setup_logging(self) -> None:
        """Configures logger handlers to capture output from the backend library."""
        # Taps off the logging of the thermal-network package
        logger: logging.Logger = logging.getLogger("thermal_network") 
        logger.setLevel(logging.INFO)

        # Creat a custom handler and set the appropriate format
        handler = ThreadSafeQueueHandler(self.log_queue, widget_to_notify=self)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        # Bind the Event to the logging method
        self.bind("<<NewLogRecord>>", self._on_log_record_received)


    def _on_log_record_received(self, event: tk.Event) -> None:
        """Handles incoming log records triggered via virtual event notifications.

        Args:
            event (tk.Event): Event instance passed by Tkinter.
        """
        records: list[str] = []
        while not self.log_queue.empty():
            try:
                record = self.log_queue.get_nowait()
                records.append(record)
                
                # Update Status-Text and Progressbar based in the current log
                self._update_progress_from_log(record)
            except queue.Empty:
                break
        
        if records:
            self.txt_log.configure(state=tk.NORMAL)
            self.txt_log.insert("end", "\n".join(records) + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state=tk.DISABLED)


    def _update_progress_from_log(self, log_msg: str) -> None:
        """Parses incoming log strings to update GUI progress indicators.

        Args:
            log_msg (str): A single log message entry.
        """
        # Trimming phase
        if "Trimming steady state" in log_msg:
            self.lbl_status.config(text="Trimming steady state data...")
            self.progress["value"] = 5

        # Search for the optimum number of layers
        elif "Searching for optimal model" in log_msg:
            self.lbl_status.config(text=f"Searching optimal model ({self.min_layer} to {self.max_layer} layers)...")
            self.progress["value"] = 10

        # Progress per fitted layer
        elif "Completed fit for" in log_msg:
            match = re.search(r"Completed fit for (\d+)-layer network", log_msg)
            if match:
                current_layer = int(match.group(1))
                
                # Calculate the relative progress between 10% and 90%
                if hasattr(self, "max_layer") and hasattr(self, "min_layer") and self.max_layer > self.min_layer:
                    total_steps = self.max_layer - self.min_layer + 1
                    current_step = current_layer - self.min_layer + 1
                    progress_pct = 10 + int((current_step / total_steps) * 80)
                else:
                    progress_pct = 50

                self.lbl_status.config(text=f"Fitting layer {current_layer} complete...")
                self.progress["value"] = progress_pct

        # Select a model
        elif "Model Selection Complete" in log_msg:
            self.lbl_status.config(text="Model selection complete. Finalizing...")
            self.progress["value"] = 95

    def _build_ui(self) -> None:
        """Constructs and lays out all visual components within the frame."""
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        control_frame = ttk.Frame(self, padding=15)
        control_frame.grid(row=0, column=0, sticky=tk.NSEW)

        if not self.gui_is_called:
            ttk.Label(control_frame, text="Control & Configuration").pack(anchor=tk.W, pady=(0, 15))
            ttk.Button(control_frame, text="Import Data", bootstyle="primary-outline", command=self.load_data_from_file).pack(fill=tk.X, pady=5)

        self.lbl_file = ttk.Label(control_frame, text="Data Ready in Memory" if self.raw_data is not None else "No Data")
        self.lbl_file.pack(anchor=tk.W, pady=(0, 15))

        frm_fit_settings = ttk.Labelframe(master=control_frame, text="Fit Settings")
        frm_fit_settings.pack(anchor=tk.W, padx=5, pady=5)
        
        ttk.Label(frm_fit_settings, text="Min. RC-Elements (Order):", justify=tk.LEFT).grid(row= 0, column=0, padx=5, pady=8, sticky=tk.W)
        self.spin_order_min = ttk.Spinbox(frm_fit_settings, from_=1, to=self.max_layer, width=10, command=self.fitting_layers_changed)
        self.spin_order_min.set(self.min_layer)
        self.spin_order_min.grid(row=0, column=1, pady=4, padx=5, sticky=tk.W, columnspan=2)

        ttk.Label(frm_fit_settings, text="Max. RC-Elements (Order):", justify=tk.LEFT).grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        self.spin_order_max = ttk.Spinbox(frm_fit_settings, from_=self.min_layer, to=20, width=10, command=self.fitting_layers_changed)
        self.spin_order_max.set(self.max_layer)
        self.spin_order_max.grid(row=1, column=1, pady=4, padx=5, sticky=tk.W, columnspan=2)

        ttk.Label(master=frm_fit_settings, text="Optimization Criterion:", justify=tk.LEFT).grid(row=2, column=0, padx=5, pady=8, sticky=tk.W)

        self.optimization_criterion = tk.StringVar(self)
        self.optimization_criterion.set("BIC")

        self.rb_optim_bic = ttk.Radiobutton(master=frm_fit_settings,text="BIC", 
                                                  variable=self.optimization_criterion,
                                                  value="BIC")
        self.rb_optim_bic.grid(row=2, column=1, padx=5, sticky=tk.W)
        self.rb_optimc_aic = ttk.Radiobutton(master=frm_fit_settings,text="AIC", 
                                                   variable=self.optimization_criterion,
                                                   value="AIC")
        self.rb_optimc_aic.grid(row=2, column=2, padx=5, sticky=tk.W)

        ttk.Label(master=frm_fit_settings, text="Minimum τ:", justify=tk.LEFT, anchor=tk.W).grid(row=3, column=0, padx=5, pady=8, sticky=tk.W)
        self.min_tau = tk.StringVar()
        self.min_tau.set(str(Quantity(self.min_tau_s, "s")))

        self.ent_min_tau = ttk.Entry(master=frm_fit_settings, textvariable=self.min_tau, width=10, justify=tk.LEFT)
        self.ent_min_tau.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

        frm_display_options = ttk.Labelframe(master=control_frame, text="Display Options")
        frm_display_options.pack(anchor=tk.W, fill=tk.X, padx=5, pady=5)

        self.cb_display_opt_select = tk.StringVar()
        self.cb_display_opt_select.set("All Networks")
        self.cb_display_plots = ttk.Combobox(master=frm_display_options, 
                                             values=self._create_cb_display_options(), 
                                             justify=tk.CENTER, 
                                             textvariable=self.cb_display_opt_select , 
                                             width=12, 
                                             state=tk.DISABLED)
        self.cb_display_plots.pack(fill=tk.X, padx=5, pady=5)
        self.cb_display_plots.bind("<<ComboboxSelected>>", self._on_plot_layers_changed)

        self.btn_fit = ttk.Button(control_frame, text="Start Fitting", bootstyle="success", command=self.start_fitting_thread)
        self.btn_fit.pack(fill=tk.X, pady=5)

        # Status for fitting progress
        self.lbl_status = ttk.Label(control_frame, text="Ready", font=("Helvetica", 9, "italic"))
        self.lbl_status.pack(anchor=tk.W, pady=(10, 2))

        self.progress = ttk.Progressbar(control_frame, mode="determinate", bootstyle="striped-info")
        self.progress.pack(fill=tk.X, pady=(0, 10))

        self.btn_export = ttk.Button(control_frame, text="Export LTspice Subcircuit", bootstyle="warning", command=self.export_ltspice, state=tk.DISABLED)
        self.btn_export.pack(fill=tk.X, pady=(20, 5))

        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=1, sticky=tk.NSEW, padx=10, pady=10)

        ######################################################
        # THERMAL NETWORK & EQUIVALENT COMPONENTS TAB
        ######################################################
        plot_frame = ttk.Frame(notebook)
        notebook.add(plot_frame, text="Thermal Impedance Plot")
        self._init_plot(plot_frame)

        self.circuit_frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.circuit_frame, text="Equivalent Circuit & Components")
        self._init_circuit_view(self.circuit_frame)
        
        ######################################################
        # LOGGING TAB
        ######################################################
        log_frame = ttk.Frame(notebook, padding=10)
        notebook.add(log_frame, text="Log")

        # Scrolled Text for the LOG-Output
        self.txt_log = ttk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        self.txt_log.pack(fill=tk.BOTH, expand=True)


    def fitting_layers_changed(self):
        self.min_layer = int(self.spin_order_min.get())
        self.max_layer = int(self.spin_order_max.get())
        new_opt = self._create_cb_display_options()

        self.cb_display_plots.configure(values=new_opt)


    def _create_cb_display_options(self) -> list[str]:

        cb_options = []
        for idx in range(self.min_layer, self.max_layer+1):
            cb_options.append(f"Order {idx} Network")

        cb_options.append("All Networks")

        if self.cb_display_opt_select.get() not in cb_options:
            self.cb_display_opt_select.set("All Networks")

        self.cb_display_options = cb_options
        return cb_options

    def _on_plot_layers_changed(self, event: tk.Event) -> None:
        """Handles changes in the plot mode combobox selection.

        Args:
            event (tk.Event): Tkinter event object passed by the binding.
        """
        self._on_fitting_finished()


    def _init_plot(self, parent: ttk.Frame) -> None:
        """Initializes the Matplotlib plot area embedded into the GUI.

        Args:
            parent (ttk.Frame): Container frame to attach the canvas widget.
        """
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.ax.set_title("Thermal Impedance Zth(t)")
        self.ax.set_xlabel("Time t/[s]")
        self.ax.set_ylabel("Zth/[K/W]")
        self.ax.grid(True, which="both", ls="--")

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, parent)
        toolbar.update()


    def _init_circuit_view(self, parent: ttk.Frame) -> None:
        """Initializes the Treeview table and schematic view frame.

        Args:
            parent (ttk.Frame): Container frame holding circuit parameters.
        """
        ttk.Label(parent, text="Calculated RC-Parameters",).pack(anchor=tk.W, pady=5)

        style = ttk.Style()

        style.configure("Treeview",
                        rowheight=24,                  
                        relief="solid",                # Border style
                        bd=1)                          # Border width


        style.configure("Treeview.Heading",
                        font=("Helvetica", 9, "bold"),
                        relief="raised",
                        bd=1)

        columns = ("element", "r_val", "c_val", "tau")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=10 )
        self.tree.heading("element", text="RC-Element")
        self.tree.heading("r_val", text="R [K/W]")
        self.tree.heading("c_val", text="C [Ws/K]")
        self.tree.heading("tau", text="Time Constant Tau [s]")

        self.tree.column("element", width=100, minwidth=80, anchor="center", stretch=False)
        self.tree.column("r_val", width=120, minwidth=100, anchor="center", stretch=False)
        self.tree.column("c_val", width=120, minwidth=100, anchor="center", stretch=False)
        self.tree.column("tau", width=160, minwidth=120, anchor="center", stretch=False)

        self.tree.tag_configure("even", background="#f8f9fa")
        self.tree.tag_configure("odd", background="#ffffff")

        self.tree.pack(fill=tk.X, pady=5)

        self.btn_convert_network = ttk.Button(parent, text="Convert to Cauer Network", bootstyle="info", command=self._switch_displayed_network, state=tk.DISABLED)
        self.btn_convert_network.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parent, text="Circuit Topology:", ).pack(anchor=tk.W, pady=(10, 2))
        self.schematic_container = ttk.Frame(parent)
        self.schematic_container.pack(fill=tk.BOTH, expand=True)


    def _plot_raw_data(self) -> None:
        """Plots the imported raw measurement dataset on a logarithmic time scale."""
        if self.raw_data is None:
            return
        self.ax.clear()
        self.ax.semilogx(self.raw_data[:, 0], self.raw_data[:, 1], label="Measurement Data", color="#00bc8c")
        self.ax.set_xlabel("Time t [s]")
        self.ax.set_ylabel("Zth [K/W]")
        self.ax.grid(True, which="both", ls="--")
        self.ax.legend()
        self.canvas.draw()


    def load_data_from_file(self) -> None:
        """Opens a file dialog to load raw measurement data from CSV/text files."""
        path = filedialog.askopenfilename(filetypes=[("CSV/Data Files", "*.csv *.txt *.dat"), ("All Files", "*.*")])
        if path:
            try:
                self.raw_data = np.loadtxt(path, delimiter=",")
                self.lbl_file.config(text=f"File: {path.split('/')[-1]}")
                self._plot_raw_data()
                self._calc_min_tau()

            except Exception as e:
                messagebox.showerror("Error when loading", str(e))


    def _calc_min_tau(self) -> None:
        """ Calculates the automatic minimum tau setting based on the imported data
        """        

        if self.raw_data is not None:
            if self.raw_data[0, 0] != 0.0:
                self.min_tau_s = self.raw_data[0, 0] * 5    # Minimum Tau must be at least 5 times larger than the first sample
            else:
                self.min_tau_s = 1e-6

            self.min_tau.set(str(Quantity(self.min_tau_s, "s")))


    def start_fitting_thread(self) -> None:
        """Validates configuration and launches the fitting calculation in a background thread."""
        plt.ioff()
        logger = logging.getLogger("thermal_network")
        logger.info("Starting the fitting process")
        if self.raw_data is None:
            messagebox.showwarning("Warning", "No measurement data loaded.")
            return

        self.btn_fit.config(state="disabled")
        self.cb_display_plots.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.lbl_status.config(text="Starting fitting process...")

        # Read ALL Tkinter variable values HERE in the main thread to avoid threading issues
        try:
            min_layer = int(self.spin_order_min.get())
            max_layer = int(self.spin_order_max.get())
            min_tau_s = Quantity(self.min_tau.get()).real
            criterion = self.optimization_criterion.get()
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input parameters: {e}")
            self.btn_fit.config(state=tk.NORMAL)
            return

        self.min_layer = min_layer
        self.max_layer = max_layer

        threading.Thread(target=self._run_fitting_process, 
                         args=(min_layer, 
                               max_layer, 
                               min_tau_s, 
                               criterion), 
                         daemon=True
                         ).start()


    def _run_fitting_process(self, min_layer: int, max_layer: int, min_tau_s: float, criterion: str) -> None:
        """ Executes data preprocessing and optimization algorithm within a background thread.

        Args:
            min_layer (int): Minimum network order.
            max_layer (int): Maximum network order.
            min_tau_s (float): Lower time constant boundary in seconds.
            criterion (str): Model selection criterion ('BIC' or 'AIC').
        """
        logger = logging.getLogger("thermal_network")
        logger.info("Fitting Thread started")

        try:
            assert self.raw_data is not None
            t = np.asarray(self.raw_data[:, 0], dtype=np.float64)
            zth = np.asarray(self.raw_data[:, 1], dtype=np.float64)
            logger.info(f"Trimming steady state. Data lenght: {len(t)}")

            if len(t) > 1000:
                logger.info(f"Downsampling dataset from {len(t)} to 1000 points for fast fitting...")

                # Create logarithmic equidistant indexes
                log_indices = np.unique(np.logspace(0, np.log10(len(t) - 1), num=1000).astype(int))
                t = t[log_indices]
                zth = zth[log_indices]

            time_data, impedance_data = tn.fitting.trim_steady_state(time_data=t, impedance_data=zth)
            model = tn.fitting.fit_optimal_foster_network(time_data=time_data, 
                                                          impedance_data=impedance_data, 
                                                          min_layers=min_layer,
                                                          max_layers=max_layer, 
                                                          tau_floor=min_tau_s, 
                                                          selection_criterion=criterion)
            self.fitting_time = time_data
            self.fitting_results = model
            self.fitted_foster_network = model.best_model.network

            
            self.after(0, self._on_fitting_finished)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Fitting Error", str(e)))
            self.after(0, self._reset_ui_after_fit)


    def _on_fitting_finished(self) -> None:
        """Main-thread callback invoked upon successful execution of the fitting algorithm."""
        self._reset_ui_after_fit()
        self.cb_display_plots.config(state="readonly")

        selected_mode = self.cb_display_opt_select.get()
        if selected_mode == "All Networks":
            self.show_fitted_plots = -1
        else:
            try:    # catch unwanted states when controls were changed between fitting runs
                self.show_fitted_plots = self.cb_display_options.index(selected_mode)
            except:
                self.show_fitted_plots = -1
                self.cb_display_opt_select.set("All Networks")

        self.ax.clear()
        if self.raw_data is not None:
            self.ax.semilogx(self.raw_data[:, 0], self.raw_data[:, 1], label="Measurement Data", color="#00bc8c")
        else:
            ValueError("Fitting finished without input data :/")

        t = self.fitting_time

        if self.show_fitted_plots < 0:  # show all fitted networks
            for color_idx, fit in enumerate(self.fitting_results.evaluated_models):

                zth_fit = tn.foster_impedance_time_domain(fit.network, t)

                if fit.network.order == self.fitting_results.best_model.network.order:
                    color = "#e74c3c"
                    l_style = "--"
                    label = f"Fit-Model Order: {fit.network.order} -> Best"
                else:
                    color = STD_GRAPH_COLORS[color_idx % 12]
                    l_style = (0, (1, 5))
                    label = f"Fit-Model Order: {fit.network.order}"
                self.ax.plot(t, zth_fit, label=label, 
                             color=color, 
                             linestyle=l_style)

        else:   # show only one fitted network

            network = self.fitting_results.evaluated_models[self.show_fitted_plots].network
            zth_fit = tn.foster_impedance_time_domain(network, t)
            self.ax.plot(t, zth_fit, label=f"Fit-Model Order: {network.order}", 
                         color="#e74c3c", linestyle="--")

        self.ax.set_xlabel("Time t [s]")
        self.ax.set_ylabel("Zth [K/W]")
        self.ax.grid(True, which="both", ls="--")

        self.fitted_foster_network = self.fitting_results.best_model.network

        self.fitted_cauer_network = tn.conversions.foster_to_cauer(self.fitted_foster_network)

        self._fill_results_to_treeview()
   
        self._render_schemdraw_circuit()
        self.btn_export.config(state=tk.NORMAL)


    def _fill_results_to_treeview(self) -> None:

        # Delete existing entries
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.fitted_foster_network is None or self.fitted_cauer_network is None:
            raise ValueError("Fitting results seem to be empty.")
        
        if self.displayed_network.lower() == "foster":
            self.display_params = list(zip(self.fitted_foster_network.r, self.fitted_foster_network.c))

            self.btn_convert_network.configure(text="Show Cauer Network")
            self.btn_convert_network.configure(state=tk.NORMAL)

        elif self.displayed_network.lower() == "cauer":
            self.display_params = list(zip(self.fitted_cauer_network.r, self.fitted_cauer_network.c))

            self.btn_convert_network.configure(text="Show Foster Network")
            self.btn_convert_network.configure(state=tk.NORMAL)
        else:
            raise ValueError(f"WRONG Parameter: {self.displayed_network} is not defined")

        for i, (r, c) in enumerate(self.display_params, 1):
            tau: float = r * c
            # Add interleaved tags for odd and even lines to have some contrast
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", 
                             "end", 
                             values=(f"RC_{i}", f"{Quantity(r)}", f"{Quantity(c)}", f"{Quantity(tau)}"),
                             tags=(tag,)) 

        self.ax.legend()
        self.canvas.draw()


    def _switch_displayed_network(self) -> None:
        if self.displayed_network.lower() == "foster":
            self.displayed_network = "cauer"
        else:
            self.displayed_network = "foster"

        self._fill_results_to_treeview()
        self._render_schemdraw_circuit()


    def _reset_ui_after_fit(self) -> None:
        """Restores interactive state of controls after fitting process terminates."""
        self.progress["value"] = 100
        self.lbl_status.config(text="Fitting completed.")
        self.btn_fit.config(state=tk.NORMAL)


    def _render_schemdraw_circuit(self) -> None:
        """Generates and embeds schematic diagram inside the GUI."""
        if not self.display_params:
            return

        # remove old widgets and figures
        if self.circuit_canvas_widget:
            self.circuit_canvas_widget.pack_forget()
            self.circuit_canvas_widget.destroy()
            self.circuit_canvas_widget = None

        if self.circuit_canvas:
            plt.close(self.circuit_canvas.figure)
            self.circuit_canvas = None

        num_elements = len(self.display_params)
        r_vals = [r for r, _ in self.display_params]
        c_vals = [c for _, c in self.display_params]
        net_type = self.displayed_network

        # Schemdraw creates an matplotlib figure
        if net_type == "foster":
            fig = rc_schem.draw_foster_rc_network(num_elements, RValues=r_vals, CValues=c_vals )
        else:
            fig = rc_schem.draw_cauer_rc_network(num_elements, RValues=r_vals, CValues=c_vals)

        # Create canvas and rendering
        self.circuit_canvas = FigureCanvasTkAgg(fig, master=self.schematic_container)
        self.circuit_canvas.draw()

        self.circuit_canvas_widget = self.circuit_canvas.get_tk_widget()
        self.circuit_canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.schematic_container.update_idletasks()


    def export_ltspice(self) -> None:
        """Exports extracted network parameters into an LTspice subcircuit (.sub) file."""
        if self.fitted_foster_network is None or self.fitted_cauer_network is None:
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".sub",
                                                filetypes=[("LTspice Subcircuit", "*.sub *.cir *.lib"), ("All Files", "*.*")])
        if not filepath:
            return

        net_type = self.displayed_network

        if net_type == "foster":
            network = exp_spice.create_ltspice_foster(self.fitted_foster_network)
        else:
            network = exp_spice.create_ltspice_cauer(self.fitted_cauer_network)


        with open(filepath, tk.W) as f:
            f.write("\n".join(network))

        messagebox.showinfo("Export sucess", f"Subcircuit saved at:\n{filepath}")


    def _get_result_dict(self) -> dict[str, Any] | None:
        """Structures extracted fitting parameters into a standard dictionary.

        Returns:
            dict[str, Any] | None: Dictionary of parameters or None if no params exist.
        """
        if self.fitted_foster_network is None or self.fitted_cauer_network is None:
            return None

        return {"foster": {"order":self.fitted_foster_network.order, 
                            "r": [r for r in self.fitted_foster_network.r],
                            "c": [c for c in self.fitted_foster_network.c],},
                "cauer": {"order":self.fitted_cauer_network.order, 
                            "r": [r for r in self.fitted_cauer_network.r],
                            "c": [c for c in self.fitted_cauer_network.c],}}


    def _emit_results(self) -> None:
        """Executes the `on_fit_complete` callback with current fitting parameters."""
        res: dict[str, Any] | None = self._get_result_dict()
        if res is not None and callable(self.on_fit_complete):
            self.on_fit_complete(res)


    def close(self) -> None:
        """Clean up resources and destroy frame/window properly."""
        self._emit_results()

        #  clean Matplotlib
        plt.close(self.fig)
        if self.circuit_canvas:
            plt.close("all")

        top_level = self.winfo_toplevel()

        # Close the parent window
        if self.gui_is_called:
            # Check if self is placed directly inside a Toplevel or is just a sub-frame
            #if top_level != self.master and isinstance(top_level, (tk.Toplevel, ttk.Toplevel)):
            top_level.destroy()
        else:
            # Standalone mode: terminate event loop completely
            top_level.quit()
            top_level.destroy()


def print_emitted_results(results:dict[str, Any]) -> None:
    """Helper function to print the results emitted by the fitting tool

    Args:
        results (dict[str, Any]): Dictionary which contains the best matching fitting results
    """    

    print(f"Foster: Order: {results['foster']['order']}")
    for r, c in zip(results['foster']['r'], results['foster']['c']):
        print(f"R: {r:.4f} K/W, C: {c:.4e} Ws/K")

    print(f"\nCauer: Order: {results['cauer']['order']}")
    for r, c in zip(results['cauer']['r'], results['cauer']['c']):
        print(f"R: {r:.4f} K/W, C: {c:.4e} Ws/K")


# ==============================================================================
# STANDALONE LAUNCHER
# ==============================================================================
if __name__ == "__main__":
    root = ttk.Window(
        title="Thermal Network Fitting Tool (Stand-Alone)"  #, themename="darkly"
    )

    app = ThermalFittingWindow(parent=root)
    app.pack(fill="both", expand=True)

    # IMPORTANT: The X-Symbol of the windown needs a proper close method bound to it
    root.protocol("WM_DELETE_WINDOW", app.close)

    # Dictionary Structure: 
    # {"foster": {"order":self.fitted_foster_network.order, 
    #              "r": [r for r in self.fitted_foster_network.r],
    #              "c": [c for c in self.fitted_foster_network.c],},
    #  "cauer": {"order":self.fitted_cauer_network.order, 
    #              "r": [r for r in self.fitted_cauer_network.r],
    #              "c": [c for c in self.fitted_cauer_network.c],}}

    def standalone_callback(results: dict[str, Any]) -> None:
        print("\n--- Fitting completed (Stand-Alone) ---")
        print_emitted_results(results=results)
    app.on_fit_complete = standalone_callback

    root.mainloop()