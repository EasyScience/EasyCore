#  SPDX-FileCopyrightText: 2021 European Spallation Source <info@ess.eu>
#  SPDX-License-Identifier: BSD-3-Clause

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from typing import TypeVar, List, Callable
from collections import namedtuple
from easyCore import np
from easyCore.Fitting.fitting_template import NameConverter

Parameter = TypeVar('Parameter', bound='Parameter')
FunctionStack = namedtuple("FunctionStack", 'func fun')


class FitFunctional:
    def __init__(self, function: Callable, *pars):
        self._function = function
        self.cache = {'results': None}
        self._parameters = {
            NameConverter().get_key(par): par for par in pars
        }
        self._cached_pars = {
            NameConverter().get_key(par): par.raw_value for par in pars
        }
        self.do_eval = True
        self.__invalidate = True
        self._cached_x = None

    @property
    def parameters(self) -> List[Parameter]:
        return list(self._parameters.values())

    @parameters.setter
    def parameters(self, pars: List[Parameter]):
        self._parameters = {
            NameConverter().get_key(par): par for par in pars
        }

    @property
    def function(self) -> Callable:
        return self._function

    @function.setter
    def function(self, new_function: Callable):
        self._function = new_function
        self.__invalidate = True

    def __call__(self, independent: np.ndarray, **pars) -> np.ndarray:
        self.par_update(**pars)
        return self._callfn(independent)

    def _callfn(self, independent: np.ndarray) -> np.ndarray:
        if self._cached_x is None:
            self._cached_x = independent
            self.do_eval = True
        else:
            if not np.all(independent == self._cached_x):
                self._cached_x = independent
                self.do_eval = True
        if self.do_eval:
            self.cache['results'] = self.function(self._cached_x)
            self.__invalidate = False
        return self.cache['results']

    def par_update(self, **pars):
        update = False
        for name, value in pars.items():
            par_name = int(name[1:])
            if self._cached_pars[par_name] != value:
                self._parameters[par_name].raw_value = value
                self._cached_pars[par_name] = value
                update = True
        self.do_eval = update or self.cache['results'] is None or self.__invalidate

    def __add__(self, other):
        return FitStack(self._function) + other

    def __sub__(self, other):
        return FitStack(self._function) - other

    def __mul__(self, other):
        return FitStack(self._function) * other


class FitStack:

    def __init__(self, initial_fn):
        self.initial = initial_fn
        self._stack = []

    def __call__(self, *args, **kwargs):
        output = self.initial(*args, **kwargs)
        for todo in self._stack:
            output = todo.fun(output, todo.func(*args, **kwargs))
        return output

    def __add__(self, other):
        self._stack.append(FunctionStack(other, np.add))
        return self

    def __sub__(self, other):
        self._stack.append(FunctionStack(other, np.subtract))
        return self

    def __mul__(self, other):
        self._stack.append(FunctionStack(other, np.multiply))
        return self
