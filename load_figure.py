import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
import pickle
import backtrader as bt


fig = pickle.load(open('reports\\sample_plot.pickle', 'rb'))[0][0]

# create a dummy figure() object to hold loaded figures
dummy = plt.figure()
new_manager = dummy.canvas.manager
new_manager.canvas.figure = fig
fig.set_canvas(new_manager.canvas)

fig.set_size_inches(12.8, 7.2)
fig.set_dpi(100)

# add crosshair to cursor
cursor = bt.plot.multicursor.MultiCursor(fig.canvas, fig.axes,
                                         useblit=True,
                                         horizOn=True, vertOn=True,
                                         horizMulti=False, vertMulti=True,
                                         horizShared=True, vertShared=False,
                                         color='black', lw=1, ls=':')

plt.show()
