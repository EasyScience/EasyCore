__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np

from easyCore.Datasets.Dataset import xr
import time
import matplotlib.pyplot as plt

from easyCore.Fitting.Fitting import Fitter
from easyCore.Objects.Base import BaseObj, Parameter
d = xr.Dataset()

nx = 5E4
x_min = 0
x_max = 3*np.pi

sin_offest = - 1.25
cos_offset = 0.4

x = np.linspace(x_min, x_max, num=int(nx))

d.easyCore.add_dimension('x', x)
d.easyCore.add_dimension('y', x + np.pi)
d.easyCore.add_variable('z', ['x', 'y'], np.sin(x + sin_offest).reshape((-1, 1))*np.cos(x + cos_offset).reshape((1, -1)) + 5*(0.5 - np.random.random(size=(int(nx), int(nx)))))

b = BaseObj('line',
            s_off=Parameter('s_off', 0),
            c_off=Parameter('c_off', 0))


def fit_fun(x, *args, **kwargs):
    # In the real case we would gust call the evaluation fn without reference to the BaseObj
    return np.sin(x[:, 0] + b.s_off.raw_value) * np.cos(x[:, 1] + b.c_off.raw_value)


f = Fitter()
f.initialize(b, fit_fun)

print('Performing fit - No dask')
t = time.time()
f_res = d['z'].easyCore.fit(f)
d['computed_no_dask'] = f_res.y_calc.unstack()
temp = d['z'] - d['computed_no_dask']
print(f'Time taken: {time.time() - t}')

fig, axes = plt.subplots(ncols=2, nrows=2)
d['z'].plot(ax=axes[0, 0])
d['computed_no_dask'].plot(ax=axes[0, 1])
temp.plot(ax=axes[1, 0])
plt.tight_layout()
plt.show()

print('Performing fit - Dask')
t = time.time()
to_chunk = ['x_broadcast', 'y_broadcast', 'z']
for name in to_chunk:
    d[name] = d[name].chunk({'x': 4000, 'y': 4000})
f_res = d['z'].easyCore.fit(f, dask='parallelized')
d['computed_dask'] = f_res.y_calc.unstack()
temp = d['z'] - d['computed_dask']
print(f'Time taken: {time.time() - t}')

fig, axes = plt.subplots(ncols=2, nrows=2)
d['z'].plot(ax=axes[0, 0])
d['computed_dask'].plot(ax=axes[0, 1])
temp.plot(ax=axes[1, 0])
plt.tight_layout()
plt.show()

print('All done :-)')
