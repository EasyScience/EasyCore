__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.Datasets.Dataset import xr
import matplotlib.pyplot as plt
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import Fitter

d = xr.Dataset()

b = BaseObj('line',
            m=Parameter('m', 1),
            c=Parameter('c', 1))


def fit_fun(x, *args, **kwargs):
    # In the real case we would gust call the evaluation fn without reference to the BaseObj
    return b.c.raw_value + b.m.raw_value * x


nx = 1E3
x_min = 0
x_max = 100

x = np.linspace(x_min, x_max, num=int(nx))
y = 2*x - 1 + 5*(np.random.random(size=x.shape) - 0.5)

fig, ax = plt.subplots(2, 3, sharey='row')
for idx, minimizer in enumerate(['lmfit', 'bumps', 'DFO_LS']):

    f = Fitter()
    f.initialize(b, fit_fun)
    f.switch_engine(minimizer)

    d.easyCore.add_dimension('x', x)
    d.easyCore.add_variable('y', ['x'], y, auto_sigma=False)

    f_res = d['y'].easyCore.fit(f)
    print(f_res.goodness_of_fit)

    d['y'].plot(ax=ax[0, idx])
    f_res.y_calc.unstack().plot(ax=ax[0, idx])
    temp = d['y'] - f_res.y_calc.unstack()
    temp.plot(ax=ax[1, idx])
    ax[0, idx].set_title(f'Minimizer - {minimizer}')
ax[0, 0].set_ylabel('y')
ax[1, 0].set_ylabel('Difference')
plt.show()
