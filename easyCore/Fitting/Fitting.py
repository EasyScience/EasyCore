__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from types import FunctionType
from typing import List, Callable
from easyCore import borg

import easyCore.Fitting as Fitting
import numpy as np


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

        self._engines = Fitting.engines
        self._current_engine = None
        self.__engine_obj = None
        self._is_initialized = False
        self.create()

        fit_methods = [x for x, y in Fitting.FittingTemplate.__dict__.items()
                       if type(y) == FunctionType
                       and not x.startswith('_')]
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

    def create(self, engine_name: str = 'lmfit'):
        engines = self.available_engines
        if engine_name in engines:
            self._current_engine = self._engines[engines.index(engine_name)]

    def switch_engine(self, engine_name: str):
        # There isn't any state to carry over
        if not self._is_initialized:
            print('The fitting engine must first be initialized')
            raise ReferenceError
        self.create(engine_name)
        self.__initialize()

    @property
    def available_engines(self) -> List[str]:
        """
        Get a list of the names of available fitting engines
        :return: List of available fitting engines
        :rtype: List[str]
        """
        if Fitting.engines is None:
            print('Fitting not instantiated yet')
            raise ImportError
        return [engine.name for engine in Fitting.engines]

    @property
    def can_fit(self):
        return self._is_initialized

    @property
    def current_engine(self) -> Callable:
        return self._current_engine

    @property
    def engine(self) -> Fitting.FittingTemplate:
        return self.__engine_obj

    @property
    def fit_function(self) -> Callable:
        return self._fit_function

    @fit_function.setter
    def fit_function(self, fit_function: Callable):
        self._fit_function = fit_function

    @property
    def fit_object(self):
        return self._fit_object

    @fit_object.setter
    def fit_object(self, fit_object: object):
        self._fit_object = fit_object

    def __pass_through_generator(self, name):
        obj = self

        def inner(*args, **kwargs):
            if not obj.can_fit:
                print('The fitting engine must first be initialized')
                raise ReferenceError
            func = getattr(obj.engine, name, None)
            if func is None:
                raise ValueError
            return func(*args, **kwargs)
        return inner
