__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

import matplotlib.pyplot as plt

import numpy as np
from easyCore.Datasets.xarray import xr
from easyCore.Fitting.Fitting import Fitter
from easyCore.Objects.ObjectClasses import BaseObj
from easyCore.Objects.ObjectClasses import Parameter

d = xr.Dataset()

b = BaseObj('line',
            m=Parameter('m', 1),
            c=Parameter('c', 1))


def fit_fun(x, *args, **kwargs):
    # In the real case we would gust call the evaluation fn without reference to the BaseObj
    return b.c.raw_value + b.m.raw_value * x


f = Fitter()
f.initialize(b, fit_fun)

nx = 1E3
x_min = 0
x_max = 100

x = np.linspace(x_min, x_max, num=int(nx))
y1 = 2*x - 1 + 5*(np.random.random(size=x.shape) - 0.5)
x2 = x + 20
y2 = 2*x2 - 1 + 5*(np.random.random(size=x2.shape) - 0.5)

d.easyCore.add_coordinate('x1', x)
d.easyCore.add_variable('y1', ['x1'], y1, auto_sigma=True)
d.easyCore.add_coordinate('x2', x2)
d.easyCore.add_variable('y2', ['x2'], y2, auto_sigma=True)

res = d.easyCore.fit(f, ['y1', 'y2'])

fig, axs = plt.subplots(1, len(res), sharey=True)
for idx, r in enumerate(res):
    r.y_obs.plot(ax=axs[idx])
    r.y_calc.plot(ax=axs[idx])
    axs[idx].set_title(f'Dataset {idx}')
plt.show()

