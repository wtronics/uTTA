import numpy as np
from matplotlib.backend_bases import MouseButton

class BlitSnapCursor:
    """
    A cross-hair cursor that snaps to the data point of a line, which is
    closest to the *x* position of the cursor.

    For simplicity, this assumes that *x* values of the data are sorted.
    """

    def __init__(self, ax, line, subplot, line_idx):
        self.ax = ax[subplot]
        self.subplot = subplot
        self.line_idx = line_idx
        self.background = None      # for blitting
        self.horizontal_line = ax[subplot].axhline(color='k', lw=0.8, ls='--')
        self.vertical_line = ax[subplot].axvline(color='k', lw=0.8, ls='--')
        self.x, self.y = line[line_idx].get_data()
        self._last_index = None
        # text location in axes coords
        self.text = ax[subplot].text(0.72, 0.9, '', transform=ax[subplot].transAxes)
        self._creating_background = False       # for blitting
        ax[subplot].figure.canvas.mpl_connect('draw_event', self.on_draw)
        self.cursor_xpos = 0
        self.cursor_ypos = 0
        self.xclick = 0
        self.yclick = 0

    def on_draw(self, event):       # function for blitting
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()

        if not event.inaxes:
            self._last_index = None
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                # self.ax.figure.canvas.draw()
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            x, y = event.xdata, event.ydata
            index = min(np.searchsorted(self.x, x), len(self.x) - 1)
            if index == self._last_index:
                return  # still on the same data point. Nothing to do.
            self._last_index = index
            x = self.x[index]
            y = self.y[index]
            print("Coordinates: {xpos},{ypos}".format(xpos=x, ypos=y))
            self.cursor_xpos = x
            self.cursor_ypos = y
            # update the line positions
            self.horizontal_line.set_ydata([y])
            self.vertical_line.set_xdata([x])
            self.text.set_text(f'x={x:1.1f}, y={y:1.4f}')
            # self.ax.figure.canvas.draw()
            self.ax.figure.canvas.restore_region(self.background)
            self.ax.draw_artist(self.horizontal_line)
            self.ax.draw_artist(self.vertical_line)
            self.ax.draw_artist(self.text)
            self.ax.figure.canvas.blit(self.ax.bbox)

    def on_click(self, event):
        if event.button is MouseButton.LEFT:
            if event.inaxes:
                self.xclick = self.cursor_xpos
                self.yclick = self.cursor_ypos
                print("Click Coordinates: {xpos},{ypos}".format(xpos=self.xclick, ypos=self.yclick))
