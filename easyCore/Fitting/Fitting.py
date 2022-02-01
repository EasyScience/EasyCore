__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from abc import ABCMeta
from types import FunctionType
from typing import List, Callable, TypeVar


from easyCore import borg, default_fitting_engine
import easyCore.Fitting as Fitting

_C = TypeVar("_C", bound=ABCMeta)
_M = TypeVar("_M", bound=Fitting.FittingTemplate)


class Fitter:
    """
    Wrapper to the fitting engines
    """

    _borg = borg

    def __init__(self, fit_object: object = None, fit_function: Callable = None):

        self._fit_object = fit_object
        self._fit_function = fit_function

        can_initialize = False
        # We can only proceed if both obj and func are not None
        if (fit_object is not None) & (fit_function is not None):
            can_initialize = True
        else:
            if (fit_object is not None) or (fit_function is not None):
                raise AttributeError

        self._engines: List[_C] = Fitting.engines
        self._current_engine: _C = None
        self.__engine_obj: _M = None
        self._is_initialized: bool = False
        self.create()

        fit_methods = [
            x
            for x, y in Fitting.FittingTemplate.__dict__.items()
            if isinstance(y, FunctionType) and not x.startswith("_")
        ]
        for method_name in fit_methods:
            setattr(self, method_name, self.__pass_through_generator(method_name))

        if can_initialize:
            self.__initialize()

    def initialize(self, fit_object: object, fit_function: Callable):
        self._fit_object = fit_object
        self._fit_function = fit_function
        self.__initialize()

    def __initialize(self):
        self.__engine_obj = self._current_engine(self._fit_object, self._fit_function)
        self._is_initialized = True

    def create(self, engine_name: str = default_fitting_engine):
        engines = self.available_engines
        if engine_name in engines:
            self._current_engine = self._engines[engines.index(engine_name)]

    def switch_engine(self, engine_name: str):
        # There isn't any state to carry over
        if not self._is_initialized:
            print("The fitting engine must first be initialized")
            raise ReferenceError
        constraints = self.__engine_obj._constraints
        self.create(engine_name)
        self.__initialize()
        self.__engine_obj._constraints = constraints

    @property
    def available_engines(self) -> List[str]:
        """
        Get a list of the names of available fitting engines

        :return: List of available fitting engines
        :rtype: List[str]
        """
        if Fitting.engines is None:
            print("Fitting not instantiated yet")
            raise ImportError
        return [engine.name for engine in Fitting.engines]

    @property
    def can_fit(self) -> bool:
        """
        Can a fit be performed. i.e has the object been created properly

        :return: Can a fit be performed
        :rtype: bool
        """
        return self._is_initialized

    @property
    def current_engine(self) -> _C:
        """
        Get the class object of the current fitting engine.

        :return: Class of the current fitting engine (based on the `FittingTemplate` class)
        :rtype: _T
        """
        return self._current_engine

    @property
    def engine(self) -> _M:
        """
        Get the current fitting engine object.

        :return:
        :rtype: _M
        """
        return self.__engine_obj

    @property
    def fit_function(self) -> Callable:
        return self._fit_function

    @fit_function.setter
    def fit_function(self, fit_function: Callable):
        self._fit_function = fit_function
        self.__initialize()

    @property
    def fit_object(self) -> object:
        return self._fit_object

    @fit_object.setter
    def fit_object(self, fit_object: object):
        self._fit_object = fit_object
        self.__initialize()

    def __pass_through_generator(self, name: str):
        obj = self

        def inner(*args, **kwargs):
            if not obj.can_fit:
                raise ReferenceError("The fitting engine must first be initialized")
            func = getattr(obj.engine, name, None)
            if func is None:
                raise ValueError
            return func(*args, **kwargs)

        return inner
