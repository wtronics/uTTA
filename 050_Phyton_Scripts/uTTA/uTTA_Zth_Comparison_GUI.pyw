import matplotlib
from matplotlib.ticker import LogLocator
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # type: ignore
from matplotlib.figure import Figure
import numpy as np
from numpy import genfromtxt       
from tksheet import Sheet
import tkinter as tk
import ttkbootstrap as ttk
import library.uTTA_data_processing as udpc

matplotlib.use("TkAgg")

WINDOW_WIDTH = 1580
WINDOW_HEIGHT = 960

class ZthData():
    def __init__(self):
        self.filename :str = ""
        self.filepath :str = ""
        self.monitor_ch_first_value_idx :int = 0
        self.timebase :list = []
        self.zth_data_driver :list = []
        self.zth_data_monitors :list = []
        self.channel_names :list = []

    
    def read_file(self, filepath):
        datafile, self.filename, folderpath = udpc.split_file_path(filepath)
        self.filepath = filepath

        print(f"reading file {self.filepath}")

        fil_import = genfromtxt(self.filepath, delimiter='\t', dtype=float, names=True)
        cols = fil_import.dtype.names

        # find the index at which the real measurement data on the monitor channels (without interpolation) starts
        self.monitor_ch_first_value_idx = np.argmax(fil_import[cols[2]] > 0) # type: ignore
        self.timebase = fil_import[cols[0]] # type: ignore
        self.zth_data_driver = fil_import[cols[1]] # type: ignore
        self.zth_data_monitors = np.stack((fil_import[cols[2]], fil_import[cols[3]]),axis=1) # type: ignore
        self.channel_names = [cols[1], cols[2], cols[3]]    # type: ignore
    
    def __repr__(self) -> str:
        retstr = f"Filename {self.filename}\n"
        retstr += f"Filepath {self.filepath}\n"
        retstr += f"Timebase {self.timebase}\n"
        retstr += f"Zth Driver  {self.zth_data_driver}\n"
        retstr += f"Zth Monitor {self.zth_data_monitors}\n"
        retstr += f"Monitor First Index {self.monitor_ch_first_value_idx}\n"
        return retstr


class ZthComparatorApp(ttk.Window):
    def __init__(self):
        super().__init__()
        self.title("uTTA Zth Comparison GUI")
        self.geometry("1480x960")
        self.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        screen_dpi = self.winfo_fpixels('1i')
        geometry = self.winfo_geometry()

        self.files_selected = 0
        self.file_data :dict = {}
        self.plots :list = []

        matplotlib.rcParams['axes.labelsize'] = 9
        matplotlib.rcParams['legend.fontsize'] = 9
        matplotlib.rcParams['font.size'] = 11
        matplotlib.rcParams['xtick.labelsize'] = 9
        matplotlib.rcParams['ytick.labelsize'] = 9

        self.iconbitmap(r'library/uTTA_Icon.ico')
        print(f"DPI: {screen_dpi}, Geometry: {geometry}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        self.paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # LEFT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#

        # Measurement File Button Frame
        self.frm_left = ttk.Frame(self.paned)
        self.frm_left.pack(fill=tk.X, padx=10, pady=10)
        self.frm_file_btns = ttk.Labelframe(self.frm_left, text="Files",
                                             style="secondary.TLabelframe")
        self.frm_file_btns.pack(fill=tk.X, padx=10, pady=10)
        self.btn_add_file = ttk.Button(master=self.frm_file_btns,
                                           text="Add File",
                                           command=self.add_measurement_file_callback, style="dark")
        self.btn_add_file.pack(fill=tk.X, padx=10, pady=10)

        self.btn_del_file = ttk.Button(master=self.frm_file_btns,
                                           text="Delete File",
                                           command=self.delete_measurement_file_callback, style="dark", state="disabled")
        self.btn_del_file.pack(fill=tk.X, padx=10, pady=10)

        tab_heading = ["Show", "File"]
        self.files_sheet = Sheet(self.frm_file_btns, startup_select=(0, 1, "rows"),
                                 page_up_down_select_row=True, height=230, 
                                 total_columns=2, row_index_width=30)
        self.files_sheet.pack(fill=tk.X, padx=10, pady=10)
        self.files_sheet.enable_bindings(('single_select', 'edit_cell')) # type: ignore
        self.files_sheet.extra_bindings("edit_cell", self.after_cell_edit)
        self.files_sheet.headers(tab_heading)
        self.files_sheet.set_all_column_widths(200)
        self.files_sheet.align_columns(0, "center")
        self.files_sheet.column_width(0, 60)
        self.files_sheet.hide("row_index")
  
        self.files_sheet.checkbox("A", checked=False)

        self.paned.add(self.frm_left)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # RIGHT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        self.frm_right = ttk.Frame(self.paned)
        self.frm_right.pack(fill=tk.X, padx=10, pady=10)

        self.lbl_helpbar = ttk.Label(master=self.frm_right, anchor="w", style="inverse-info", wraplength=1080)
        self.lbl_helpbar.pack(fill=tk.X, padx=10, pady=10)
        self.lbl_helpbar.configure(text="Welcome to the uTTA Zth comparison tool.\n")

        # Plot Area
        self.frm_plot_area = ttk.Frame(master=self.frm_right)
        self.frm_plot_area.pack(fill=tk.BOTH, padx=10, pady=10)

        self.fig = Figure(figsize=(1230/screen_dpi, 770/screen_dpi), dpi=96, tight_layout = True)
        self.plots = self.fig.subplots(3, 1)

        for plot in self.plots:
            plot.set_xscale('log')
            plot.xaxis.set_major_locator(LogLocator(base=10.0, subs=[1.0], numticks=999))
            plot.grid(True , axis='both', which='major', ls="-", color='black') 
            plot.grid(True , axis='x', which="minor", ls="-", alpha=0.5)
            plot.set_yscale('log')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot_area)
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, padx=10, pady=10)
        self.canvas.draw()
        # Toolbar #########
        toolbar_frame = ttk.Frame(master=self.frm_right, style="secondary.TFrame")
        toolbar_frame.pack(fill=tk.X, padx=10, pady=10)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        self.paned.add(self.frm_right)

        self.update_widgets()
    
    def after_cell_edit(self, event):
        # content = event["selected"]
        # print(f"Cell edited in row {content.row}, {content.column}, with value {self.files_sheet.get_cell_data(content.row, content.column)}")
        self.update_widgets()

    def on_cell_select(self, event):
        pass
                                
    def add_measurement_file_callback(self):

        if self.files_selected < 5:
            FileNam = udpc.select_file('Open a t3i-File',
                                (('T3I Intermediate Files', '*.t3i'), ('All files', '*.*')))
            DataFile, DataFileNoExt, FilePath = udpc.split_file_path(FileNam)
            if DataFile in self.file_data.keys():
                self.lbl_helpbar.configure(text="This file was already imported. Each file can only be imported once!\n", style='danger.Inverse.TLabel')
            else:
                if len( DataFile)>1:
                    self.files_sheet.insert_row(idx=0)
                    self.files_sheet["A1"].data = True
                    self.files_sheet["B1"].data = DataFile

                    self.files_selected += 1

                    data = ZthData()
                    data.read_file(FileNam)                    

                    self.file_data[DataFile] = data

                    for dat in self.file_data:
                        print(repr(self.file_data[dat]))

                    self.btn_del_file.configure(state="enabled")
                    if self.files_selected >= 5:
                        self.btn_add_file.configure(state="disabled")
                    self.update_widgets()

        else:
            self.lbl_helpbar.configure(text="There were already 5 files selected for comparison.\n", style='danger.Inverse.TLabel')

    def delete_measurement_file_callback(self):
        row_number = None
        tbl = self.files_sheet
        for box in tbl.get_all_selection_boxes():
            row_number = tbl.datarn(box.from_r) # type: ignore

        if row_number is not None:
            data_set = tbl.get_cell_data(r=row_number,c=1)

            del self.file_data[data_set]
            tbl.delete_row(row_number)
            self.files_selected -= 1
            self.update_widgets()
            if self.files_selected == 0:
                self.btn_del_file.configure(state="disabled")
            if self.files_selected < 5:
                self.btn_add_file.configure(state="enabled")

    def update_widgets(self):

        if self.plots.any() : # type: ignore
            self.plots[0].clear()
            self.plots[1].clear()
            self.plots[2].clear()

            shown_plots = 0
            filenames = self.files_sheet.get_column_data(c=1)
            enabled = self.files_sheet.get_column_data(c=0)

            for dat in self.file_data:
                if dat in filenames:
                    if enabled[filenames.index(dat)]:
                        shown_plots += 1
                        fil_data = self.file_data[dat]
                        self.plots[0].loglog(fil_data.timebase, 
                                             fil_data.zth_data_driver, 
                                             label=f"{fil_data.filename} - {fil_data.channel_names[0]}")
                        self.plots[1].loglog(fil_data.timebase[fil_data.monitor_ch_first_value_idx:], 
                                             fil_data.zth_data_monitors[fil_data.monitor_ch_first_value_idx:, 0], 
                                             label=f"{fil_data.filename} - {fil_data.channel_names[1]}")
                        self.plots[2].loglog(fil_data.timebase[fil_data.monitor_ch_first_value_idx:], 
                                             fil_data.zth_data_monitors[fil_data.monitor_ch_first_value_idx:, 1], 
                                             label=f"{fil_data.filename} - {fil_data.channel_names[2]}")

            if shown_plots > 0: 
                for plot in self.plots:
                    plot.xaxis.set_major_locator(LogLocator(base=10.0, subs=[1.0], numticks=999))
                    plot.grid(True , axis='both', which='major', ls="-", color='black') 
                    plot.grid(True , axis='both', which="minor", alpha=0.7)
                    plot.set_xlabel("Time / [s]")
                    plot.set_ylabel("Zth / [K/W]")
                    plot.legend(loc='lower right' )

        self.canvas.draw()
        self.update()

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.destroy()


if __name__ == "__main__":

    app = ZthComparatorApp()
    app.mainloop()
