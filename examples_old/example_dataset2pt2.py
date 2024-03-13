__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

import matplotlib.pyplot as plt

import numpy as np
from easyCore.Datasets.xarray import xr
from easyCore.Fitting.Fitting import Fitter
from easyCore.Objects.ObjectClasses import BaseObj
from easyCore.Objects.ObjectClasses import Parameter

d = xr.Dataset()

m_starting_point = 1
c_starting_point = 1


b = BaseObj('line',
            m=Parameter('m', m_starting_point),
            c=Parameter('c', c_starting_point))


def fit_fun(x, *args, **kwargs):
    # In the real case we would gust call the evaluation fn without reference to the BaseObj
    return b.c.raw_value + b.m.raw_value * x


nx = 1E3
x_min = 0
x_max = 100

x = np.linspace(x_min, x_max, num=int(nx))
y = 2*x - 1 + 5*(np.random.random(size=x.shape) - 0.5)

d.easyCore.add_coordinate('x', x)
d.easyCore.add_variable('y', ['x'], y, auto_sigma=False)

f = Fitter()
f.initialize(b, fit_fun)

fig, ax = plt.subplots(2, 3, sharey='row')
for idx, minimizer in enumerate(['lmfit', 'bumps', 'DFO_LS']):

    b.m = m_starting_point
    b.c = c_starting_point
    f.switch_engine(minimizer)

    f_res = d['y'].easyCore.fit(f, vectorize=True)
    print(f_res.p)

    d['y'].plot(ax=ax[0, idx])
    f_res.y_calc.unstack().plot(ax=ax[0, idx])
    temp = d['y'] - f_res.y_calc
    temp.plot(ax=ax[1, idx])
    ax[0, idx].set_title(f'Minimizer - {minimizer}')
ax[1, 0].set_ylabel('Difference')
plt.show()
