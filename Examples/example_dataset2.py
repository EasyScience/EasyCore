__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.Datasets.xarray import xr
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


f = Fitter()
f.initialize(b, fit_fun)

nx = 1E3
x_min = 0
x_max = 100

x = np.linspace(x_min, x_max, num=int(nx))
y = 2*x - 1 + 5*(np.random.random(size=x.shape) - 0.5)

d.easyCore.add_coordinate('x', x)
d.easyCore.add_variable('y', ['x'], y, auto_sigma=True)

def post(result, addition=10):
    return result + addition

d['y'].easyCore.postcompute_func = post

# d['y'] = d['y'].chunk({'x': 1000})
f_res = d['y'].easyCore.fit(f, dask='parallelized')

print(f_res.goodness_of_fit)

d['y'].plot()
d['computed'] = f_res.y_calc
d['computed'].plot()
plt.show()
