"""
Fitting a dataset with a linear model.
=====================================
This  example shows how to create a dataset and a model, and how to fit using the dataset interface.

Imports
*******

Firstly the necessary imports. Notice that we import numpy from easyCore. This is not done for any reason other than
saving time from multiple imports.
"""
from easyCore import np
from easyCore.models.polynomial import Line
from easyCore.Datasets.xarray import xr
from easyCore.Fitting import Fitter
import matplotlib.pyplot as plt

d = xr.Dataset()
l = Line.from_pars(2.0, 1.0)

m_starting_point = 4.48
c_starting_point = 51.7

l2 = Line.from_pars(m_starting_point, c_starting_point)

x = np.linspace(0, 100, 10001)
y = l(x) + np.random.normal(0, 2, x.shape)

d.easyCore.add_coordinate("x", x)
d.easyCore.add_variable("y", ["x"], y, auto_sigma=True)

f = Fitter()
f.initialize(l2, l2.__call__)


fig, ax = plt.subplots(2, 3, sharey="row")
for idx, minimizer in enumerate(["lmfit", "bumps", "DFO_LS"]):

    l2.m = m_starting_point
    l2.c = c_starting_point
    f.switch_engine(minimizer)

    f_res = d["y"].easyCore.fit(f)
    print(f_res.p)

    d["y"].plot(ax=ax[0, idx])
    f_res.y_calc.unstack().plot(ax=ax[0, idx])
    temp = d["y"] - f_res.y_calc
    temp.plot(ax=ax[1, idx])
    ax[0, idx].set_title(f"Minimizer - {minimizer}")
ax[1, 0].set_ylabel("Difference")
plt.show()

#%%
# Multiple Examples
# *****************
# To include embedded rST, use a line of >= 20 ``#``'s or ``#%%`` between your
# rST and your code. This separates your example
# into distinct text and code blocks. You can continue writing code below the
# embedded rST text block:
