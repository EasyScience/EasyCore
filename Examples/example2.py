__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numpy as np
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import Fitter

# In this case we have inherited from `BaseObj` to create a class which has fitable attributes.


class Line(BaseObj):
    """
    Simple descriptor of a line.
    """

    _defaults = [Parameter('m', 1),
                 Parameter('c', 0)]

    def __init__(self):
        super().__init__(self.__class__.__name__,
                         *self._defaults)

    @property
    def gradient(self):
        return self.m.raw_value

    @property
    def intercept(self):
        return self.c.raw_value

    def fit_func(self, x: np.ndarray) -> np.ndarray:
        return self.gradient * x + self.intercept

    def __repr__(self):
        return f'Line: m={self.m}, c={self.c}'


l = Line()
f = Fitter()
f.initialize(l, l.fit_func)

x = np.array([1, 2, 3])
y = np.array([2, 4, 6]) - 1

f_res = f.fit(x, y)

print(f_res.goodness_of_fit)
print(l)