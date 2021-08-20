import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
import pickle

fig = pickle.load(open('fig.pickle', 'rb'))
multi = MultiCursor(fig.canvas, fig.axes, color='r', lw=.5, horizOn=True, vertOn=True)
plt.subplots_adjust(left=0.03, bottom=0.025, right=0.98, top=0.97, wspace=0.0, hspace=0.0)
plt.show()
