from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.pyplot as plt     # matplotlib 3.9.2
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)  # matplotlib 3.9.2
import ttkbootstrap as ttk  # ttkbootstrap 1.13.5
import pprint as pprint

class UttaPlotConfiguration:
    def __init__(self, data, title, x_label, y_label, plot_type='line',
                 x_scale='linear',x_scale_formatter = None , y_scale='linear', y_scale_formatter = None, style=None,
                 secondary_data=None, secondary_y_label=None):
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
    def __init__(self, parent, size, rows, cols, dpi=96, padding=3.0, no_gui=False):
        # Creates the Matplotlib-Figure and the subplots in the requested grid
        self.parent = parent
        self.figure = None
        self.axes = None
        self.size = size
        self.dpi = dpi
        self.no_gui = no_gui

        self.plot_mapping = []

        self.figure, self.axes = Figure(figsize=(size[0] / dpi, (size[1]-10) / dpi), dpi=dpi), []

        for i in range(rows):
            for j in range(cols):
                ax = self.figure.add_subplot(rows, cols, i * cols + j + 1)
                self.axes.append(ax)
        self.figure.tight_layout(pad=padding)

        # matplotlib default settings
        mpl.rcParams['axes.labelsize'] = 8
        mpl.rcParams['legend.fontsize'] = 7
        mpl.rcParams['font.size'] = 9.5
        mpl.rcParams['xtick.labelsize'] = 8
        mpl.rcParams['ytick.labelsize'] = 8
        mpl.rcParams['text.usetex'] = False

        if not self.no_gui:
            self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid( sticky="ew")

            # Toolbar Frame
            toolbar_frame = ttk.Frame(master=parent)
            toolbar_frame.place(x=10, y=size[1]-20)
            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()


    def update_plots(self):

        for i, ax in enumerate(self.axes):
            ax.clear()

            mapping_item = next((item for item in self.plot_mapping if item[0] == i), None)

            num_plots = 0
            if mapping_item:
                config_func = mapping_item[1]
                config = config_func()  # calls back the function to get the next configuration object

                # ==========================================================
                # Logic for plots with 2 Y-Axis
                # ==========================================================
                if config.plot_type == 'dual_y_axis':
                    ax2 = ax.twinx()

                    # Axis 1: Primary data
                    for line in config.data:
                        ax.plot(line['x_data'],
                                line['y_data'],
                                label=line['label'],
                                **line['style'])
                        num_plots += 1
                    ax.set_ylabel(config.y_label)

                    # Axis 2: Secondary Data
                    for sec_line in config.secondary_data:
                        ax2.plot(sec_line['x_data'],
                                 sec_line['y_data'],
                                 label=sec_line['label'],
                                 **sec_line['style'])
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

                    ax.set_xscale(config.x_scale)
                    ax.set_yscale(config.y_scale)

                # Common settings for all plots + the legend
                if num_plots > 0:       # check if anything was printed into the plot. Otherwise mpl will generate an error
                    ax.legend(loc='best', fontsize='small')
                ax.set_title(config.title)
                ax.grid("both")
                ax.set_xlabel(config.x_label)
                ax.set_ylabel(config.y_label)

            if self.no_gui:

                plt.show()
            else:
                self.canvas.draw()


