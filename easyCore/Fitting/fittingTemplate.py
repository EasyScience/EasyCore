__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from abc import ABCMeta, abstractmethod
from collections import Callable

import numpy as np


class FittingTemplate(metaclass=ABCMeta):
    calculators = []

    def __init_subclass__(cls, is_abstract=False, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_abstract:
            cls.calculators.append(cls)

    def __init__(self, obj, x=None):
        self._model = obj
        self._x = np.ndarray(x)
        self._store = {}

    @property
    def x(self) -> np.ndarray:
        return self._x

    @x.setter
    def x(self, value: np.ndarray):
        self._x = value

    @property
    def fit_keys(self):
        return self._store.keys()

    @abstractmethod
    def fit(self, data, **kwargs):
        pass

    def _fit(self, data, **kwargs):
        return self._model.fit(data, **self._store, **kwargs)

    def eval(self, params=None, **kwargs):
        if self._model.independent_vars[0] not in kwargs.keys():
            kwargs[self._model.independent_vars[0]] = self._x

        if params is None:
            params = self._model.make_pars()

        for key in kwargs.keys():
            if key not in self._model.independent_vars:
                if key in params.keys():
                    params[key].value = kwargs[key]
                    kwargs.pop(key)
                else:
                    if key in self._model.param_names:
                        params.add(key, kwargs[key])
                        kwargs.pop(key)
        self._model.eval(params=params, **kwargs)

    @staticmethod
    def __gitem(key: str) -> Callable:
        def inner(obj):
            if key in obj._store.keys():
                return obj._store[key]
            else:
                raise KeyError
        return lambda obj: inner(obj)

    @staticmethod
    def __sitem(key):
        return lambda obj, value: obj._store.__setattr__(key, value)
