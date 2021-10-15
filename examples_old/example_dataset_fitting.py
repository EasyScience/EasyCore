#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"


# !! WARNING !!!
# THIS SCRIPT WILL USE ~ 80Gb of memory. Adjust `nx` to something your system can do
# !! WARNING !!!

from easyCore import np
from easyCore.Datasets.xarray import xr
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import Fitter

import time

# def no_calls(func):
#     setattr(func, 'n_calls', 0)
#
#     re


class Sins(BaseObj):
    """
    Simple descriptor of a line.
    """

    _defaults = {"a1": 1, "a2": 1}

    def __init__(self):
        super().__init__(
            self.__class__.__name__,
            *[
                Parameter(key, value, fixed=False)
                for key, value in self._defaults.items()
            ],
        )

    @property
    def A1(self):
        return self.a1.raw_value

    @property
    def A2(self):
        return self.a2.raw_value

    def fit_function(self, x: np.ndarray) -> np.ndarray:
        return np.sin(self.A1 * x[:, 0]) * np.cos(self.A2 * x[:, 1])

    def __repr__(self):
        return f"Sins: a1={self.a1}, a2={self.a2}"


d = xr.Dataset()
model_fit = Sins()
model_ref = Sins()
model_ref.a1 = 1.15
model_ref.a2 = 0.85

nx = int(5e2)
x_min = 0
x_max = 3 * np.pi

x = np.linspace(x_min, x_max, num=int(nx))

d.easyCore.add_coordinate("x", x)
d.easyCore.add_coordinate("y", x + np.pi)
points = d.easyCore.generate_points(["x", "y"]).T
d.easyCore.add_variable(
    "z",
    ["x", "y"],
    np.reshape(model_ref.fit_function(points.data), (nx, nx))
    + 0.1 * (0.5 * np.random.rand(nx, nx)),
)

f = Fitter(model_fit, model_fit.fit_function)

result = d["z"].easyCore.fit(f)
print(result)


# bdims, initial_array, f = d["z"].easyCore.fit_prep(func)
# d["x_broadcast"], d["y_broadcast"] = bdims
#
# print("Applying func - No dask")
# t = time.time()
# d["computed_no_dask"] = xr.apply_ufunc(f, d["x_broadcast"], d["y_broadcast"])
# temp = initial_array - d["computed_no_dask"]
# print(f"Time taken: {time.time() - t}")
# # temp.plot()
# # plt.show()
#
# print("Applying func - Dask")
# t = time.time()
# dims, initial_array, f = d["z"].easyCore.fit_prep(
#     func, dask_chunks={"x": int(nx / 5), "y": int(nx / 5)}
# )
# print(f"-- Broadcasting time taken: {time.time() - t}")
# d["computed_dask"] = xr.apply_ufunc(f, *dims, dask="parallelized")
# print(f"-- B + Ufunc time taken: {time.time() - t}")
# temp = initial_array - d["computed_dask"]
# print(f"-- B + Ufunc + substraction time taken: {time.time() - t}")
# temp.compute()
# print(f"Time taken: {time.time() - t}")
# # temp.plot()
# # plt.show()
#
# print("All done :-)")
