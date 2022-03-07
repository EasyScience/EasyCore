__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from easyCore import np
from easyCore.Datasets.scipp import sc
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting import Fitter

import matplotlib.pyplot as plt

b1 = BaseObj("line", m=Parameter("m", 1), c=Parameter("c", 1))


def fit_fun1(x, *args, **kwargs):
    # In the real case we would gust call the evaluation fn without reference to the BaseObj
    return b1.c.raw_value + b1.m.raw_value * x


f = Fitter(b1, fit_fun1)

nx = 1e3
x_min = 0
x_max = 100

m_ = 2.6
c_1 = 5.2

x = np.linspace(x_min, x_max, num=int(nx))
y1 = m_ * x + c_1 + 5 * (np.random.random(size=x.shape) - 0.5)

d = sc.DataArray(
    data=sc.array(values=y1, dims=["x"]), coords={"x": sc.array(values=x, dims=["x"])}
)

res = d.easyCore.fit(f)
plt.plot(x, res.y_obs, "o", label="data")
plt.plot(x, res.y_calc, "-", label="fit")
plt.show()
