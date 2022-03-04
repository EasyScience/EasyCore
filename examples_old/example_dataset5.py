__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from easyCore import np
from easyCore.Datasets.xarray import xr
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import MultiFitter
from easyCore.Fitting.Constraints import ObjConstraint

import matplotlib.pyplot as plt

d = xr.Dataset()

b1 = BaseObj("line", m=Parameter("m", 1), c=Parameter("c", 1))

b2 = BaseObj("line", m=Parameter("m", 1), c=Parameter("c", 1))

b1.m.user_constraints["constrain_m"] = ObjConstraint(b2.m, "", b1.m)


def fit_fun1(x, *args, **kwargs):
    # In the real case we would gust call the evaluation fn without reference to the BaseObj
    return b1.c.raw_value + b1.m.raw_value * x


def fit_fun2(x, *args, **kwargs):
    # In the real case we would gust call the evaluation fn without reference to the BaseObj
    return b2.c.raw_value + b2.m.raw_value * x


f = MultiFitter([b1, b2], [fit_fun1, fit_fun2])

nx = 1e3
x_min = 0
x_max = 100

common_m = 2.6
c_1 = 5.2
c_2 = -1.2

x = np.linspace(x_min, x_max, num=int(nx))
y1 = common_m * x + c_1 + 5 * (np.random.random(size=x.shape) - 0.5)
x2 = x + 20
y2 = common_m * x2 + c_2 + 5 * (np.random.random(size=x2.shape) - 0.5)

d.easyCore.add_coordinate("x1", x)
d.easyCore.add_variable("y1", ["x1"], y1, auto_sigma=True)
d.easyCore.add_coordinate("x2", x2)
d.easyCore.add_variable("y2", ["x2"], y2, auto_sigma=True)

res = d.easyCore.fit(f, ["y1", "y2"])

fig, axs = plt.subplots(1, len(res), sharey=True)
for idx, r in enumerate(res):
    r.y_obs.plot(ax=axs[idx])
    r.y_calc.plot(ax=axs[idx])
    axs[idx].set_title(f"Dataset {idx}")
plt.show()
