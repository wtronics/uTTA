import matplotlib.pyplot as plt
import numpy as np
import blittedsnappycursor as bsc
from matplotlib.backend_bases import MouseEvent


x = np.arange(0, 10, 0.01)
y = np.sin(2 * 2 * np.pi * x)

fig, ax = plt.subplots()
ax.set_title('Blitted Snapping cursor')
line, = ax.plot(x, y)
snap_cursor = bsc.BlitSnapCursor(ax, line)
fig.canvas.mpl_connect('motion_notify_event', snap_cursor.on_mouse_move)

# Simulate a mouse move to (0.5, 0.5), needed for online docs
# t = ax.transData
# MouseEvent("motion_notify_event", ax.figure.canvas, *t.transform((0.5, 0.5)))._process()

plt.connect('button_press_event', snap_cursor.on_click)

plt.show()
