__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numpy as np
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import Fitter

# In this case we have inherited from `BaseObj` to create a class which has fitable attributes.
# This class does not know about the `Calculator`, only the interface.

class Calculator:
    def __init__(self, m=1, c=0):
        self.m = m
        self.c = c

    def calculate(self, x):
        return self.m * x + self.c


class Interface:
    def __init__(self):
        self.calculaor = Calculator()

    def get_value(self, value_label: str):
        return getattr(self.calculaor, value_label, None)

    def set_value(self, value_label: str, value):
        print(f'Value of {value_label} set to {value}')
        setattr(self.calculaor, value_label, value)

    def fit_func(self, x):
        return self.calculaor.calculate(x)


class Line(BaseObj):
    _defaults = [Parameter('m', 1, callback=property()),
                 Parameter('c', 0)]

    def __init__(self):
        self.interface = Interface()
        super().__init__(self.__class__.__name__,
                         *self._defaults)
        self.m._callback = property(lambda: self.interface.get_value('m'),
                                    lambda value: self.interface.set_value('m', value))

        self.c._callback = property(lambda: self.interface.get_value('c'),
                                    lambda value: self.interface.set_value('c', value))

    @property
    def gradient(self):
        return self.interface.get_value('m')

    @property
    def intercept(self):
        return self.interface.get_value('c')

    def fit_func(self, x: np.ndarray) -> np.ndarray:
        return self.interface.fit_func(x)

    def __repr__(self):
        return f'Line: m={self.m}, c={self.c}'


l = Line()
f = Fitter.fitting_engine(l, l.fit_func)

x = np.array([1, 2, 3])
y = np.array([2, 4, 6]) - 1

f_res = f.fit(x, y)

print(f_res.fit_report())
print(l)