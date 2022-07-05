#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"


import functools

from easyCore import np
from easyCore.Objects.ObjectClasses import BaseObj, Parameter
from easyCore.Objects.Groups import BaseCollection

from typing import ClassVar, Optional, Iterable, Union


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

    def __init__(self, name: str = "polynomial",
                 coefficients: Optional[Union[Iterable[Union[float, Parameter]], BaseCollection]] = None):
        super(Polynomial, self).__init__(name, coefficients=BaseCollection("coefficients"))
        if coefficients is not None:
            if issubclass(type(coefficients), BaseCollection):
                self.coefficients = coefficients
            elif isinstance(coefficients, Iterable):
                for index, item in enumerate(coefficients):
                    if issubclass(type(item), Parameter):
                        self.coefficients.append(item)
                    elif isinstance(item, float):
                        self.coefficients.append(Parameter(name="c{}".format(index), value=item))
                    else:
                        raise TypeError("Coefficients must be floats or Parameters")
            else:
                raise TypeError("coefficients must be a list or a BaseCollection")

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

    def __init__(self, m: Optional[Union[Parameter, float]] = None,
                 c: Optional[Union[Parameter, float]] = None):
        super(Line, self).__init__("line",
                                   m=Parameter("m", 1.),
                                   c=Parameter("c", 0.))
        if m is not None:
            self.m = m
        if c is not None:
            self.c = c

    # @designate_calc_fn can be used to inject parameters into the calculation function. i.e. _m = m.raw_value
    def __call__(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        return self.m.raw_value * x + self.c.raw_value

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.m, self.c)
