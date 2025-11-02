import tkinter
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # type: ignore # matplotlib 3.9.2
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib # matplotlib 3.9.2
import ttkbootstrap as ttk  # ttkbootstrap 1.13.5
import library.uTTA_data_processing as udpc
from quantiphy import Quantity

matplotlib.use("TkAgg")

class TSPInterpolationApp(ttk.Window):

    def __init__(self, mainwindow):
        super().__init__()
        self.timebase_scale_set = tkinter.StringVar(self)
        self.timebase_scale_set.set("Sqrt")

        self.mainwindow = mainwindow
        self.InterpolationAveragingHW = tkinter.IntVar()

        self.show_tangent = True

        self.interp_points_idx_start = udpc.find_nearest(self.mainwindow.utta_data.adc_timebase_cooling, self.mainwindow.utta_data.InterpolationTStart)
        self.interp_points_idx_end = udpc.find_nearest(self.mainwindow.utta_data.adc_timebase_cooling, self.mainwindow.utta_data.InterpolationTEnd)

        self.title("uTTA TSP Interpolation")
        self.geometry("1000x960")
        self.minsize(1000, 960)
        screen_dpi = self.winfo_fpixels('1i')
        geometry = self.winfo_geometry()
        print("DPI: " + str(screen_dpi) + " Geometry: " + str(geometry))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # Upper GUI Part (Plot Window)
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # Helper Bar Frame
        self.frm_help_bar = ttk.Frame(master=self, width=990, height=40, style='info.TFrame')
        self.frm_help_bar.place(x=5, y=5)

        self.lbl_helpbar = ttk.Label(master=self.frm_help_bar, anchor="w", style="inverse-info", wraplength=980)
        self.lbl_helpbar.place(x=5, y=5, width=980)
        self.lbl_helpbar.configure(text="Welcome to the uTTA interpolation tool.")

        self.frm_plot_area = ttk.Frame(master=self)
        self.frm_plot_area.place(x=5, y=50, width=990, height=760)

        self.interpol_fig = None
        # self.interpol_plot = None

        self.interpol_fig = Figure(figsize=(980 / screen_dpi, 700 / screen_dpi), dpi=96)
        self.interpol_plot = self.interpol_fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.interpol_fig, master=self.frm_plot_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1, rowspan=18, columnspan=5, padx=5, pady=5, sticky="ew")

        # Toolbar Frame
        toolbar_frame = ttk.Frame(master=self.frm_plot_area)
        toolbar_frame.place(x=5, y=710)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)

        # matplotlib default settings
        matplotlib.rcParams['axes.labelsize'] = 8
        matplotlib.rcParams['legend.fontsize'] = 7
        matplotlib.rcParams['font.size'] = 9.5
        matplotlib.rcParams['xtick.labelsize'] = 8
        matplotlib.rcParams['ytick.labelsize'] = 8
        # matplotlib.rcParams['text.usetex'] = True

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # Lower GUI Part (Controls)
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        #  Timescale Controls
        self.frm_controls = ttk.Frame(master=self, width=990, height=90, style='info.TFrame')
        self.frm_controls.place(x=5, y=815)

        # Time scale selection with radio buttons
        self.frm_timescale = ttk.Labelframe(self.frm_controls, text="Timescale")
        self.frm_timescale.place(x=5, y=5, width=120, height=80)

        self.ctrl_timescale_log = ttk.Radiobutton(master=self.frm_timescale,
                                                  text="Logarithmic", variable=self.timebase_scale_set,
                                                  value="Log", command=self.update_plots)
        self.ctrl_timescale_log.place(x=5, y=5)
        self.ctrl_timescale_sqrt = ttk.Radiobutton(master=self.frm_timescale,
                                                   text="Square-Root", variable=self.timebase_scale_set,
                                                   value="Sqrt", command=self.update_plots)
        self.ctrl_timescale_sqrt.place(x=5, y=30)

        self.interpol_marker_ctrl = Interpol_Controls_Widget(self.frm_controls, self)

        self.frm_interpol_results = ttk.Labelframe(master=self.frm_controls, text="Interpolation Results")
        self.frm_interpol_results.place(x=425, y=5, width=290, height=80)

        self.lbl_interpol_depth = ttk.Label(master=self.frm_interpol_results, text="Max. Interpolation Depth", anchor="w")
        self.lbl_interpol_depth.place(x=5, y=5, width=175)

        self.lbl_interpol_depth = ttk.Label(master=self.frm_interpol_results, style="inverse")
        self.lbl_interpol_depth.configure(text="")
        self.lbl_interpol_depth.place(x=180, y=5, width=90)

        self.lbl_est_die_size = ttk.Label(master=self.frm_interpol_results, text="Estimated Active Area", anchor="w")
        self.lbl_est_die_size.place(x=5, y=30, width=175)

        self.lbl_est_die_size = ttk.Label(master=self.frm_interpol_results, style="inverse")
        self.lbl_est_die_size.configure(text="")
        self.lbl_est_die_size.place(x=180, y=30, width=90)

        self.frm_interpol_settings = ttk.Labelframe(master=self.frm_controls, text="Interpolation Settings")
        self.frm_interpol_settings.place(x=425+290+10, y=5, width=290, height=80)

        self.lbl_interpol_width = ttk.Label(master=self.frm_interpol_settings, text="Averaging Half Width", anchor="w")
        self.lbl_interpol_width.place(x=5, y=5, width=160)

        self.spinb_interpol_point_hw = ttk.Spinbox(master=self.frm_interpol_settings, width=40,
                                                   from_=1, to=20, increment=1,
                                                   textvariable=self.InterpolationAveragingHW,
                                                   command=self.update_plots)
        self.spinb_interpol_point_hw.place(x=165, y=5, width=50)
        self.spinb_interpol_point_hw.set(value=self.mainwindow.utta_data.InterpolationAverageHW)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # Data Plotting Part (Display)
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        self.timebase = self.mainwindow.utta_data.adc_timebase_cooling
        self.diode_temp_values = self.mainwindow.utta_data.t_dio_raw[0, :]
        self.interpol_plot_cutoff = self.interpol_marker_ctrl.interpolation_plot_end_time
        self.interpol_plot_cutoff_idx = udpc.find_nearest(self.timebase, self.interpol_plot_cutoff)

        self.plotdata = {}
        self.plotdata["raw_data"], = self.interpol_plot.semilogx(self.timebase[0:self.interpol_plot_cutoff_idx],
                                                                 self.diode_temp_values[0:self.interpol_plot_cutoff_idx])

        interp_len = len(self.mainwindow.utta_data.t_dio_start_interpolation)
        self.plotdata["interp"], = self.interpol_plot.semilogx(self.timebase[0:interp_len],
                                                               self.mainwindow.utta_data.t_dio_start_interpolation[0:interp_len])

        self.plot_markerlines = {}
        self.plot_markerlines["start"] = self.interpol_plot.axvline(self.mainwindow.utta_data.InterpolationTStart,
                                                                    color="b", linewidth=0.5)
        self.plot_markerlines["end"] = self.interpol_plot.axvline(self.mainwindow.utta_data.InterpolationTEnd,
                                                                  color="r", linewidth=0.5)

        self.interpol_plot.set_xlabel(r'${Time \; / \; [s]}$')
        self.interpol_plot.set_ylabel(r'${Temperature \; / \; [K]}$')
        self.interpol_plot.grid(which='both')
        self.canvas.draw()

        self.toolbar.update()
        self.update_plots()
        self.update_displays()
        self.update()

    def create_si_string(self,value, unit):
        return '{val}'.format(val=Quantity(value, unit))

    def update_displays(self):
        # update the displayed time
        self.mainwindow.utta_data.InterpolationAverageHW = int(self.spinb_interpol_point_hw.get())
        self.interpol_marker_ctrl.lbl_interpol_start_time.configure(text=self.create_si_string(self.mainwindow.utta_data.InterpolationTStart, 's'))
        self.interpol_marker_ctrl.lbl_interpol_end_time.configure(text=self.create_si_string(self.mainwindow.utta_data.InterpolationTEnd, 's'))

        self.lbl_interpol_depth.configure(text=self.create_si_string(self.mainwindow.utta_data.DieMaxThickness, 'm'))
        self.lbl_est_die_size.configure(text=self.create_si_string(self.mainwindow.utta_data.EstimatedDieSize, 'mm²'))

    def update_plots(self):

        if self.timebase_scale_set.get() == "Log":
            tb_show = self.timebase[0:self.interpol_plot_cutoff_idx]
            self.interpol_plot.set_xscale("log")
            self.interpol_plot.set_xlabel(r'${Time \; / \; [s]}$')
        else:
            tb_show = np.sqrt(self.timebase[0:self.interpol_plot_cutoff_idx])
            self.interpol_plot.set_xscale("linear")
            self.interpol_plot.set_xlabel(r'${\sqrt{Time} \; / \; [\sqrt{s}]}$')

        self.plotdata["raw_data"].set_data(tb_show,
                                           self.diode_temp_values[0:self.interpol_plot_cutoff_idx])
        
        interp_len = len(self.mainwindow.utta_data.t_dio_start_interpolation)

        if self.show_tangent:
            interp_len = len(self.mainwindow.utta_data.t_dio_start_interpolation)

            min_y = np.min(self.diode_temp_values[0:self.interpol_plot_cutoff_idx])

            interp_start = (np.sqrt(self.mainwindow.utta_data.adc_timebase_cooling[0:self.interpol_plot_cutoff_idx]) * self.mainwindow.utta_data.InterpolationFactorM +
                            self.mainwindow.utta_data.InterpolationOffset)
            
            interp_cutoff_idx = udpc.find_nearest(interp_start, min_y)

            interp_cutoff_idx = np.min([interp_cutoff_idx, self.interpol_plot_cutoff_idx])

            self.plotdata["interp"].set_data(tb_show[0:interp_cutoff_idx], interp_start[0:interp_cutoff_idx])
        
        else:
            self.plotdata["interp"].set_data(tb_show[0:interp_len],
                                            self.mainwindow.utta_data.t_dio_start_interpolation[0:interp_len])

        if self.timebase_scale_set.get() == "Log":
            self.plot_markerlines["start"].set_xdata([self.mainwindow.utta_data.InterpolationTStart, self.mainwindow.utta_data.InterpolationTStart])
            self.plot_markerlines["end"].set_xdata([self.mainwindow.utta_data.InterpolationTEnd, self.mainwindow.utta_data.InterpolationTEnd])
        else:
            self.plot_markerlines["start"].set_xdata(np.sqrt([self.mainwindow.utta_data.InterpolationTStart, self.mainwindow.utta_data.InterpolationTStart]))
            self.plot_markerlines["end"].set_xdata(np.sqrt([self.mainwindow.utta_data.InterpolationTEnd, self.mainwindow.utta_data.InterpolationTEnd]))

        self.canvas.draw() # type: ignore


    def on_closing(self):
        print("closing")

        self.mainwindow.recalculate_interpolation()
        self.mainwindow.interpolation_window_closed()

        # destroy matplotlib references for plotting
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if self.interpol_fig:
            plt.close(self.interpol_fig)
            self.interpol_fig = None

        # matplotlib.rcParams['text.usetex'] = False
        plt.clf()  # Cleans up the figure in the global context
        plt.close('all')  # Close all remaining figures
        self.interpol_marker_ctrl.destroy()
        self.destroy()


class Interpol_Controls_Widget(ttk.Frame):
    def __init__(self, parent, window):
        super().__init__(parent)
        self.parent = parent
        self.__window = window

        self.interpolation_marker_move_fast = 20
        self.interpolation_marker_move_slow = 1
        self.interpolation_plot_end_time = 0.1      # the plot goes up to 0.1s

        # Interpolation Marker Controls
        self.frm_interpol_markers = ttk.Labelframe(master=self.parent)
        self.frm_interpol_markers.place(x=130, y=5, width=290, height=80)

        self.btn_interpol_start_left_fast = ttk.Button(master=self.frm_interpol_markers, text="<--",
                                                       command=self.change_interpolation_start_neg_fast, style="dark")
        self.btn_interpol_start_left_fast.place(x=5, y=2, height=25, width=40)

        self.btn_interpol_start_left = ttk.Button(master=self.frm_interpol_markers, text="<-",
                                                  command=self.change_interpolation_start_neg, style="dark")
        self.btn_interpol_start_left.place(x=45, y=2, height=25, width=40)

        self.lbl_interpol_start = ttk.Label(master=self.frm_interpol_markers, text="Start", anchor="center")
        self.lbl_interpol_start.place(x=85, y=5, width=40)

        self.btn_interpol_start_right = ttk.Button(master=self.frm_interpol_markers, text="->",
                                                   command=self.change_interpolation_start_pos, style="dark")
        self.btn_interpol_start_right.place(x=125, y=2, height=25, width=40)

        self.btn_interpol_start_right_fast = ttk.Button(master=self.frm_interpol_markers, text="-->",
                                                        command=self.change_interpolation_start_pos_fast, style="dark")
        self.btn_interpol_start_right_fast.place(x=165, y=2, height=25, width=40)

        self.lbl_interpol_start_time = ttk.Label(master=self.frm_interpol_markers, text="", anchor="center")
        self.lbl_interpol_start_time.place(x=205, y=5, width=80)

        self.btn_interpol_end_left_fast = ttk.Button(master=self.frm_interpol_markers, text="<--",
                                                     command=self.change_interpolation_end_neg_fast, style="dark")
        self.btn_interpol_end_left_fast.place(x=5, y=27, height=25, width=40)

        self.btn_interpol_end_left = ttk.Button(master=self.frm_interpol_markers, text="<-",
                                                command=self.change_interpolation_end_neg, style="dark")
        self.btn_interpol_end_left.place(x=45, y=27, height=25, width=40)

        self.lbl_interpol_end = ttk.Label(master=self.frm_interpol_markers, text="End", anchor="center")
        self.lbl_interpol_end.place(x=85, y=30, width=40)

        self.btn_interpol_end_right = ttk.Button(master=self.frm_interpol_markers, text="->",
                                                 command=self.change_interpolation_end_pos, style="dark")
        self.btn_interpol_end_right.place(x=125, y=27, height=25, width=40)

        self.btn_interpol_end_right_fast = ttk.Button(master=self.frm_interpol_markers, text="-->",
                                                      command=self.change_interpolation_end_pos_fast, style="dark")
        self.btn_interpol_end_right_fast.place(x=165, y=27, height=25, width=40)

        self.lbl_interpol_end_time = ttk.Label(master=self.frm_interpol_markers, text="", anchor="center")
        self.lbl_interpol_end_time.place(x=205, y=30, width=80)


    def change_interpolation_start_pos_fast(self):
        self.change_interpolation_settings("start", self.interpolation_marker_move_fast)

    def change_interpolation_start_pos(self):
        self.change_interpolation_settings("start", self.interpolation_marker_move_slow)

    def change_interpolation_start_neg(self):
        self.change_interpolation_settings("start", -self.interpolation_marker_move_slow)

    def change_interpolation_start_neg_fast(self):
        self.change_interpolation_settings("start", -self.interpolation_marker_move_fast)

    def change_interpolation_end_pos_fast(self):
        self.change_interpolation_settings("end", self.interpolation_marker_move_fast)

    def change_interpolation_end_pos(self):
        self.change_interpolation_settings("end", self.interpolation_marker_move_slow)

    def change_interpolation_end_neg(self):
        self.change_interpolation_settings("end", -self.interpolation_marker_move_slow)

    def change_interpolation_end_neg_fast(self):
        self.change_interpolation_settings("end", -self.interpolation_marker_move_fast)

    def change_interpolation_settings(self,point, value):
        if point == "start":
            if 0 <= self.__window.interp_points_idx_start + value < self.__window.interpol_plot_cutoff_idx:
                self.__window.interp_points_idx_start += value
                self.__window.mainwindow.utta_data.InterpolationTStart = self.__window.mainwindow.utta_data.adc_timebase_cooling[
                    self.__window.interp_points_idx_start]

        elif point == "end":
            if self.__window.interp_points_idx_start < self.__window.interp_points_idx_end + value < self.__window.interpol_plot_cutoff_idx:
                self.__window.interp_points_idx_end += value
                self.__window.mainwindow.utta_data.InterpolationTEnd = self.__window.mainwindow.utta_data.adc_timebase_cooling[
                    self.__window.interp_points_idx_end]

        self.__window.mainwindow.utta_data.interpolate_zth_curve_start()
        self.__window.update_displays()
        self.__window.update_plots()
