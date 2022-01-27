#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.Objects.Variable import Parameter
from easyCore.Objects.ObjectClasses import BaseObj


class Line(BaseObj):
    """
    Simple descriptor of a line.
    """

    _m = 1
    _c = 0

    def __init__(self, m=None, c=None):
        name = self.__class__.__name__
        if m is None:
            m = Parameter('m', self._m)
        if c is None:
            c = Parameter('c', self._c)
        super().__init__(name, m=m, c=c)

    def func(self, x: np.ndarray, *args) -> np.ndarray:
        # # Getting  the raw_values id not the bottleneck
        # return self.m.raw_value * x + self.c.raw_value
        if len(args) == 0:
            return self.m.raw_value * x + self.c.raw_value
        else:
            return args[1]*x + args[0]

    @classmethod
    def from_pars(cls, m: float, c: float):
        return cls(m=Parameter('m', m), c=Parameter('c', c))

    def __repr__(self):
        return f'Line: m={self.m}, c={self.c}'
