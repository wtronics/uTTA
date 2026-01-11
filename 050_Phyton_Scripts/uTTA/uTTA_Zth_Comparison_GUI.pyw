import os
import matplotlib # matplotlib 3.9.2
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # type: ignore # matplotlib 3.9.2
from matplotlib.figure import Figure
import numpy as np
from numpy import genfromtxt            # numpy 2.1.0
from tksheet import (Sheet, float_formatter)
from tkinter import filedialog as fd
import ttkbootstrap as ttk  # ttkbootstrap 1.13.5
import library.uTTA_data_processing as udpc

matplotlib.use("TkAgg")

WINDOW_WIDTH = 1580
WINDOW_HEIGHT = 960
FIRST_COL_WIDTH = 300
BTN_HEIGHT = 40
SEC_COL_WIDTH = (WINDOW_WIDTH - FIRST_COL_WIDTH - 3*10)

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

        udp = udpc.UttaZthProcessing()

        self.iconbitmap(r'library/uTTA_Icon.ico')
        print("DPI: " + str(screen_dpi) + " Geometry: " + str(geometry))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # window closing event

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # LEFT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#

        # Measurement File Button Frame
        self.frm_file_btns = ttk.Labelframe(self, text="Files",
                                            width=FIRST_COL_WIDTH, style="secondary.TLabelframe")
        self.frm_file_btns.place(x=10, y=10, height=500)
        self.btn_add_file = ttk.Button(master=self.frm_file_btns,
                                           text="Add File",
                                           command=self.add_measurement_file_callback, style="dark")
        self.btn_add_file.place(x=10, y=10, height=BTN_HEIGHT, width=180)

        self.btn_del_file = ttk.Button(master=self.frm_file_btns,
                                           text="Delete File",
                                           command=self.delete_measurement_file_callback, style="dark", state="disabled")
        self.btn_del_file.place(x=10, y=BTN_HEIGHT + 2*10, height=BTN_HEIGHT, width=180)

        tab_heading = ["Show", "File"]
        self.files_sheet = Sheet(self.frm_file_btns, startup_select=(0, 1, "rows"),
                                  page_up_down_select_row=True, height=230, width=FIRST_COL_WIDTH-2*10,
                                  total_columns=2, row_index_width=30)
        self.files_sheet.place(x=10, y=2*BTN_HEIGHT + 3*10)
        self.files_sheet.enable_bindings(('single_select', 'edit_cell')) # type: ignore
        #self.files_sheet.extra_bindings("cell_select", self.on_cell_select)
        self.files_sheet.extra_bindings("edit_cell", self.after_cell_edit)
        #self.files_sheet.extra_bindings("end_edit_cell", self.after_cell_edit)
        self.files_sheet.headers(tab_heading)
        self.files_sheet.set_all_column_widths(200)
        self.files_sheet.align_columns(0, "center")
        self.files_sheet.column_width(0, 60)
        self.files_sheet.hide("row_index")
  
        self.files_sheet.checkbox("A", checked=False)

        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#
        # RIGHT GUI COLUMN
        # +#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#+#

        self.lbl_helpbar = ttk.Label(master=self, anchor="w", style="inverse-info", wraplength=1080)
        self.lbl_helpbar.place(x=FIRST_COL_WIDTH + 20, y=10, width=SEC_COL_WIDTH, height=50)
        self.lbl_helpbar.configure(text="Welcome to the uTTA Zth comparison tool.\n")

        # Plot Area
        self.frm_plot_area = ttk.Frame(master=self)
        self.frm_plot_area.place(x=FIRST_COL_WIDTH + 20, y=70, width=SEC_COL_WIDTH, height=790)

        self.fig = Figure(figsize=((SEC_COL_WIDTH-20)/screen_dpi, 770/screen_dpi), dpi=96, tight_layout = True)
        self.plots = self.fig.subplots(3, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot_area)
        
        self.canvas.get_tk_widget().place(x=10, y=10)
        self.canvas.draw()
        # Toolbar #########
        toolbar_frame = ttk.Frame(master=self, width=SEC_COL_WIDTH, style="secondary.TFrame")
        toolbar_frame.place(x=FIRST_COL_WIDTH+20, y=850)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.update_widgets()
    
    def after_cell_edit(self, event):

        content = event["selected"]
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
        # print(self.plots)
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
                self.plots[0].set_xlabel("Time / [s]")
                self.plots[0].set_ylabel("Zth / [K/W]")
                self.plots[0].grid(True)
                self.plots[0].legend(loc='lower right' )

                self.plots[1].set_xlabel("Time / [s]")
                self.plots[1].set_ylabel("Zth / [K/W]")
                self.plots[1].grid(True)
                self.plots[1].legend(loc='lower right')

                self.plots[2].set_xlabel("Time / [s]")
                self.plots[2].set_ylabel("Zth / [K/W]")
                self.plots[2].grid(True)
                self.plots[2].legend(loc='lower right')

        print("\033[94mAttempting to update widgets\033[0m")
        self.canvas.draw()
        self.update()

    def on_closing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.destroy()


if __name__ == "__main__":

    app = ZthComparatorApp()
    app.mainloop()
