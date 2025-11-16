import os
import matplotlib # matplotlib 3.9.2
from tkinter import filedialog as fd
import ttkbootstrap as ttk  # ttkbootstrap 1.13.5
import library.uTTA_data_processing as udProc
import library.uTTA_Postprocess_Measurement_Interpol_Widget as uttaInterpolWidget
import library.uTTA_Postprocess_Measurement_Widgets as uttaWidgets


matplotlib.use("TkAgg")


Debug_AutoLoadEnable = False
Debug_AutoExportHTML = False
Debug_AutoLoadFile = os.path.abspath(r"..\..\060_Example_Measurement_Data\Example_Measurement.umf")

WINDOW_WIDTH = 1480
WINDOW_HEIGHT = 960
FIRST_COL_WIDTH = 200
BTN_HEIGHT = 40
SEC_COL_WIDTH = (WINDOW_WIDTH - FIRST_COL_WIDTH - 3*10)


class UmfViewerApp(ttk.Window):
    def __init__(self):
        super().__init__()
        self.title("uTTA Measurement postprocessing GUI")
        self.geometry("1480x960")
        self.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        screen_dpi = self.winfo_fpixels('1i')
        geometry = self.winfo_geometry()

        self.iconbitmap(r'library/uTTA_Icon.ico')
        print("DPI: " + str(screen_dpi) + " Geometry: " + str(geometry))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        self.FileOpened = False
        self.FileNameWExt = ""
        self.FileName = ""
        self.DirName = ""

        self.utta_data = udProc.UttaZthProcessing()
        self.utta_data.load_settings(__file__)
        self.interp_window = None

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # LEFT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#

        # Measurement File Button Frame
        self.frm_file_btns = ttk.Labelframe(self, text="Import",
                                            width=FIRST_COL_WIDTH, style="secondary.TLabelframe")
        self.frm_file_btns.place(x=10, y=10, height=2*20 + BTN_HEIGHT)
        self.btn_measure_file = ttk.Button(master=self.frm_file_btns,
                                           text="Import Measurement",
                                           command=self.read_measurement_file_callback, style="dark")
        self.btn_measure_file.place(x=10, y=10, height=BTN_HEIGHT, width=180)


        self.frm_processing_btns = ttk.Labelframe(self, text="Processing",
                                                  width=FIRST_COL_WIDTH, style="secondary.TLabelframe")

        self.frm_processing_btns.place(x=10, y=90, height=2*20 + BTN_HEIGHT)
        self.btn_interpolation_setup = ttk.Button(master=self.frm_processing_btns,
                                                  text="Interpolation Setup",
                                                  command=self.open_interpolation_window_callback,
                                                  style="dark", state="disabled")
        self.btn_interpolation_setup.place(x=10, y=10, height=BTN_HEIGHT, width=180)

        self.frm_processing_btns = ttk.Labelframe(self, text="Export",
                                                  width=FIRST_COL_WIDTH, style="secondary.TLabelframe")
        self.frm_processing_btns.place(x=10, y=270, height=4*20 + 3*BTN_HEIGHT)
        self.btn_export_tdim_master = ttk.Button(master=self.frm_processing_btns,
                                                 text="Export TDIM Master", command=self.export_to_tdim_master,
                                                 style="dark", state="disabled")
        self.btn_export_tdim_master.place(x=10, y=10, height=BTN_HEIGHT, width=180)

        self.btn_export_zth_curve = ttk.Button(master=self.frm_processing_btns,
                                               text="Export Zth Curve", command=self.export_to_zth_curve,
                                               style="dark", state="disabled")
        self.btn_export_zth_curve.place(x=10, y=10+20 + BTN_HEIGHT, height=BTN_HEIGHT, width=180)

        self.btn_export_t3i_curve = ttk.Button(master=self.frm_processing_btns,
                                               text="Export t3i-Curve", command=self.export_to_t3i_file,
                                               style="dark", state="disabled")
        self.btn_export_t3i_curve.place(x=10, y=10+2*20 + 2*BTN_HEIGHT, height=BTN_HEIGHT, width=180)

        self.frm_report_btns = ttk.Labelframe(self, text="Report",
                                                  width=FIRST_COL_WIDTH, style="secondary.TLabelframe")
        self.frm_report_btns.place(x=10, y=480, height=3*20 + 2*BTN_HEIGHT)

        self.btn_report_html = ttk.Button(master=self.frm_report_btns,
                                                 text="Create HTML Report", command=self.report_html,
                                                 style="dark", state="disabled")
        self.btn_report_html.place(x=10, y=10, height=BTN_HEIGHT, width=180)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # RIGHT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # Helper Bar Frame
        self.frm_help_bar = ttk.Frame(master=self, width=SEC_COL_WIDTH, height=50, style='info.TFrame')
        self.frm_help_bar.place(x=FIRST_COL_WIDTH+20, y=10)

        self.lbl_helpbar = ttk.Label(master=self.frm_help_bar, anchor="w", style="inverse-info", wraplength=1080)
        self.lbl_helpbar.place(x=10, y=5)
        self.lbl_helpbar.configure(text="Welcome to the uTTA measurement postprocessing GUI. \n"
                                        "Click 'Measurement File' and import a measurement")

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # Tab Control
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#

        self.tabs = ttk.Notebook(master=self)
        self.tabs.place(x=FIRST_COL_WIDTH + 2*10, y=70, width=SEC_COL_WIDTH, height=WINDOW_HEIGHT-70-10)

        # 1st Page: Plot Area
        self.frm_plot_area = ttk.Frame(master=self)
        self.frm_plot_area.place(x=10, y=10)
        self.tabs.add(self.frm_plot_area, text="Measurement Data")

        self.meas_plots_widget = uttaWidgets.MeasurementPlotsWidget(self.frm_plot_area, self.utta_data,
                                                                    (SEC_COL_WIDTH - 2 * 10), 810,
                                                                    screen_dpi)

        # 2nd Page: Measurement Details
        self.frm_meas_details = ttk.Frame(master=self)
        self.frm_meas_details.place(x=10, y=10)
        self.tabs.add(self.frm_meas_details, text="Measurement Info")

        self.meas_info_widget = uttaWidgets.MeasurementInfoWidget(self.frm_meas_details)

        # 3rd Page: Zth Curves
        self.frm_zth_curves = ttk.Frame(master=self)
        self.frm_zth_curves.place(x=10, y=10)
        self.tabs.add(self.frm_zth_curves, text="Zth Curves      ")

        self.zth_plots_widget = uttaWidgets.ZthPlotsWidget(self.frm_zth_curves, self.utta_data,
                                                           (SEC_COL_WIDTH - 2 * 10), 810,
                                                           screen_dpi)

        # 4th Page: Deconvolution
        self.frm_deconv = ttk.Frame(master=self)
        self.frm_deconv.place(x=10, y=10)
        self.tabs.add(self.frm_deconv, text="Deconvolution   ")

        # 5th Page: Settings
        self.frm_settings = ttk.Frame(master=self)
        self.frm_settings.place(x=10, y=10)
        self.tabs.add(self.frm_settings, text="Settings        ")

        self.settings = uttaWidgets.SettingsWidget(self.frm_settings, self.utta_data)

        self.update_widgets()

        if Debug_AutoLoadEnable:
            self.read_measurement_file_callback()

    def update_widgets(self):

        print("\033[94mAttempting to update widgets\033[0m")
        if self.utta_data.flag_import_successful:
            print("\033[94mUpdating widgets\033[0m")
            self.meas_info_widget.update_widget(self.utta_data)
            self.meas_plots_widget.plots.update_plots()
            self.zth_plots_widget.plots.update_plots()
        self.update()

    def read_measurement_file_callback(self):

        if not Debug_AutoLoadEnable:
            measfilename = udProc.select_file("Select the measurement file",
                                              (('uTTA Measurement Files', '*.umf'), ('Text-Files', '*.txt'), ('All files', '*.*')))
        else:
            measfilename = Debug_AutoLoadFile

        if len(measfilename) > 0:  # check if string is not empty
            self.FileNameWExt, self.FileName, self.DirName = udProc.split_file_path(measfilename)

            self.FileOpened = self.utta_data.import_data(measfilename)

            if not self.utta_data.meta_data.FlagTSPCalibrationFile:

                self.utta_data.calculate_cooling_curve()
                self.utta_data.calculate_diode_heating()
                self.utta_data.calculate_tsp_start_voltages()

                self.utta_data.interpolate_zth_curve_start()
                self.update_widgets()

                self.lbl_helpbar.configure(text="File: {fname} was successfully imported.".format(fname=self.FileNameWExt),
                                           style="success.Inverse.TLabel")
                self.frm_help_bar.configure(style="success.TFrame")

                self.btn_interpolation_setup.configure(state="enabled")
                self.btn_export_tdim_master.configure(state="enabled")
                self.btn_export_zth_curve.configure(state="enabled")
                self.btn_report_html.configure(state="enabled")
                self.btn_export_t3i_curve.configure(state="enabled")

                if Debug_AutoExportHTML:
                    self.report_html()

            else:
                self.lbl_helpbar.configure(text="File: {fname} is a TSP calibration measurement.\n"
                                                "Therefore this file can't be processed!".format(fname=self.FileNameWExt),
                                           style="danger.Inverse.TLabel")
                self.frm_help_bar.configure(style="danger.TFrame")

                self.btn_interpolation_setup.configure(state="disabled")
                self.btn_export_tdim_master.configure(state="disabled")
                self.btn_export_zth_curve.configure(state="disabled")
                self.btn_report_html.configure(state="disabled")
                self.btn_export_t3i_curve.configure(state="disabled")


        else:
            self.lbl_helpbar.configure(text="File: {fname} was not imported.".format(fname=self.FileNameWExt),
                                       style="danger.Inverse.TLabel")
            self.frm_help_bar.configure(style="danger.TFrame")

    def open_interpolation_window_callback(self):

        if self.interp_window is None: #  or not self.interp_window.winfo_exists():
            self.interp_window = uttaInterpolWidget.TSPInterpolationApp(self)
        else:
            self.interp_window.lift()

    def recalculate_interpolation(self):
        print("recalculate called")
        self.utta_data.interpolate_zth_curve_start()

    def report_html(self):

        report_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the report shall be stored.",
                                        mustexist=True)
        
        if report_folder:
            outfilename = report_folder + r'/' + self.FileName + "_Measurement_Report.html"

            self.utta_data.report_html(outfilename)

            if Debug_AutoExportHTML:
                self.on_closing()

    def export_to_tdim_master(self):

        output_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the TDIM Master File shall be stored.",
                                        mustexist=True)
        
        if output_folder:
            outfilename = output_folder + r'/' + self.FileName + ".tdim"
            self.utta_data.export_tdim_master(outfilename)

    def export_to_zth_curve(self):

        output_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the Zth raw data shall be stored.",
                                        mustexist=True)
        
        if output_folder:
            outfilename = output_folder + r'/' + self.FileName + "_zth.txt"
            self.utta_data.export_zth_curve(outfilename)
    
    def export_to_t3i_file(self):

        output_folder = fd.askdirectory(parent=self,
                                        title="Select the directory where the t3i-file shall be stored.",
                                        mustexist=True)
        
        if output_folder:
            outfilename = output_folder + r'/' + self.FileName + ".t3i"
            self.utta_data.export_t3i_file(outfilename)

    def interpolation_window_closed(self):
        self.interp_window = None
        self.update_widgets()

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.utta_data.save_settings(__file__)
        self.destroy()


if __name__ == "__main__":

    app = UmfViewerApp()

    app.mainloop()
