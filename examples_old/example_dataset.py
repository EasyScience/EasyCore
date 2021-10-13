__author__ = "github.com/wardsimon"
__version__ = "0.1.0"


# !! WARNING !!!
# THIS SCRIPT WILL USE ~ 80Gb of memory. Adjust `nx` to something your system can do
# !! WARNING !!!

from easyCore import np
from easyCore.Datasets.xarray import xr
import time

# import matplotlib.pyplot as plt

d = xr.Dataset()

nx = 5e4
x_min = 0
x_max = 3 * np.pi

x = np.linspace(x_min, x_max, num=int(nx))

d.easyCore.add_coordinate("x", x)
d.easyCore.add_variable("y", ["x"], np.sin(x), auto_sigma=False)

# d['y'].plot()
# plt.show()


d.easyCore.remove_variable("y")
d.easyCore.add_coordinate("y", x + np.pi)
d.easyCore.add_variable(
    "z",
    ["x", "y"],
    np.sin(x).reshape((-1, 1)) * np.cos(x).reshape((1, -1))
    + (0.5 - np.random.random(size=(int(nx), int(nx)))),
)


def func(x, *args, **kwargs):
    return np.sin(x[:, 0]) * np.cos(x[:, 1])


bdims, initial_array, f = d["z"].easyCore.fit_prep(func)
d["x_broadcast"], d["y_broadcast"] = bdims

print("Applying func - No dask")
t = time.time()
d["computed_no_dask"] = xr.apply_ufunc(f, d["x_broadcast"], d["y_broadcast"])
temp = initial_array - d["computed_no_dask"]
print(f"Time taken: {time.time() - t}")
# temp.plot()
# plt.show()

print("Applying func - Dask")
t = time.time()
dims, initial_array, f = d["z"].easyCore.fit_prep(
    func, dask_chunks={"x": int(nx / 5), "y": int(nx / 5)}
)
print(f"-- Broadcasting time taken: {time.time() - t}")
d["computed_dask"] = xr.apply_ufunc(f, *dims, dask="parallelized")
print(f"-- B + Ufunc time taken: {time.time() - t}")
temp = initial_array - d["computed_dask"]
print(f"-- B + Ufunc + substraction time taken: {time.time() - t}")
temp.compute()
print(f"Time taken: {time.time() - t}")
# temp.plot()
# plt.show()

print("All done :-)")
