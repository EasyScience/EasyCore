__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.Datasets.Dataset import Dataset, xr
# import dask
# from dask.distributed import Client
# client = Client(dashboard_address=':8787')
from dask.diagnostics import ProgressBar
import time
import matplotlib.pyplot as plt

d = xr.Dataset()

nx = 5E4
x_min = 0
x_max = 3*np.pi

x = np.linspace(x_min, x_max, num=int(nx))

d.easyCore.add_dimension('x', x)
d.easyCore.add_variable('y', ['x'], np.sin(x), auto_sigma=False)

d['y'].plot()
plt.show()


d.easyCore.remove_variable('y')
d.easyCore.add_dimension('y', x + np.pi)
d.easyCore.add_variable('z', ['x', 'y'], np.sin(x).reshape((-1, 1))*np.cos(x).reshape((1, -1)) + (0.5 - np.random.random(size=(int(nx), int(nx)))))

def func(x, *args, **kwargs):
    return np.sin(x[0, :]) * np.cos(x[1, :])

bdims, f = d['z'].easyCore.fit_prep(func)
d['x_broadcast'], d['y_broadcast'] = bdims

print('Applying func - No dask')
t = time.time()
d['computed_no_dask'] = xr.apply_ufunc(f, d['x_broadcast'], d['y_broadcast'])
temp = d['z'] - d['computed_no_dask']
print(f'Time taken: {time.time() - t}')
temp.plot()
plt.show()

print('Applying func - Dask')
t = time.time()
to_chunk = ['x_broadcast', 'y_broadcast', 'z']
for name in to_chunk:
    d[name] = d[name].chunk({'x': 4000, 'y': 4000})
d['computed_dask'] = xr.apply_ufunc(f, d['x_broadcast'], d['y_broadcast'], dask='parallelized')
temp = d['z'] - d['computed_dask']
with ProgressBar():
    temp.compute()
print(f'Time taken: {time.time() - t}')
temp.plot()
plt.show()

print('All done :-)')
