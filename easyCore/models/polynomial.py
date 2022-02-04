#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"


import functools

from easyCore import np
from easyCore.Objects.Variable import Parameter
from easyCore.Objects.Base import BaseObj
from easyCore.Objects.Groups import BaseCollection

from typing import ClassVar, Optional, List, Iterable


def designate_calc_fn(func):
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        for name in list(obj.__annotations__.keys()):
            func.__globals__["_" + name] = getattr(obj, name).raw_value
        return func(obj, *args, **kwargs)

    return wrapper


class Polynomial(BaseObj):
    """
    A polynomial model.

    Parameters
    ----------
    name : str
        The name of the model.
    degree : int
        The degree of the polynomial.
    """

    coefficients: ClassVar[BaseCollection]

    def __init__(self, name: str, coefficients: BaseCollection):
        super(Polynomial, self).__init__(name, coefficients=coefficients)

    @classmethod
    def from_pars(
        cls, coefficients: Optional[Iterable[float]] = None, name: str = "polynomial"
    ):
        if coefficients is None:
            coefficients = BaseCollection("coefficients")
        elif isinstance(coefficients, Iterable):
            coefficients = BaseCollection(
                "coefficients",
                *[
                    Parameter(name="c{}".format(i), value=c)
                    for i, c in enumerate(coefficients)
                ],
            )
        return cls(name=name, coefficients=coefficients)

    def __call__(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        return np.polyval([c.raw_value for c in self.coefficients], x)

    def __repr__(self):
        s = []
        if len(self.coefficients) >= 1:
            s += [f"{self.coefficients[0].raw_value}"]
            if len(self.coefficients) >= 2:
                s += [f"{self.coefficients[1].raw_value}x"]
                if len(self.coefficients) >= 3:
                    s += [
                        f"{c.raw_value}x^{i+2}"
                        for i, c in enumerate(self.coefficients[2:])
                        if c.raw_value != 0
                    ]
        s.reverse()
        s = " + ".join(s)
        return "Polynomial({}, {})".format(self.name, s)


class Line(BaseObj):

    m: ClassVar[Parameter]
    c: ClassVar[Parameter]

    def __init__(self, m: Parameter, c: Parameter):
        super(Line, self).__init__("line", m=m, c=c)

    @classmethod
    def from_pars(cls, m: float, c: float):
        m = Parameter("m", m)
        c = Parameter("c", c)
        return cls(m=m, c=c)

    # @designate_calc_fn can be used to inject parameters into the calculation function. i.e. _m = m.raw_value
    def __call__(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        return self.m.raw_value * x + self.c.raw_value

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.m, self.c)
