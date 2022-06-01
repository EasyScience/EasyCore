__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from abc import ABCMeta
from types import FunctionType
from typing import List, Callable, TypeVar, Optional

from pkg_resources import PathMetadata


from easyCore import borg, default_fitting_engine, np
from easyCore.Objects.Groups import BaseCollection
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
        constraints = []
        if getattr(self, '__engine_obj', False):
            constraints = self.__engine_obj._constraints
        self.__initialize()
        self.__engine_obj._constraints = constraints

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
        # constraints = self.__engine_obj._constraints
        self.create(engine_name)
        self.__initialize()
        # self.__engine_obj._constraints = constraints

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


class MultiFitter(Fitter):
    """
    Extension of Fitter to enable multiple dataset/fit function fitting
    """

    def __init__(
        self, fit_objects: List[object] = None, fit_functions: List[Callable] = None
    ):

        self._fit_objects = BaseCollection("multi", *fit_objects)
        self._fit_functions = fit_functions
        # Initialize with the first of the fit_functions, without this it is 
        # not possible to change the fitting engine
        super().__init__(self._fit_objects, self._fit_functions[0])

    def fit_lists(
        self,
        x_list: List[np.ndarray],
        y_list: List[np.ndarray],
        weights_list: Optional[List[np.ndarray]] = None,
        model=None,
        parameters=None,
        method: str = None,
        fitting_kwargs: dict = {},
    ):
        """
        Perform a fit using the  engine.

        :param x: points to be calculated at
        :param y: measured points
        :param weights: Weights for supplied measured points
        :param model: Optional Model which is being fitted to
        :param parameters: Optional parameters for the fit
        :param method: method for the minimizer to use.
        :param fitting_kwargs: Additional arguments for the fitting function.
        :return: Fit results
        """
        data_shape = [x.size for x in x_list]
        def unpacked_fit_function(x: np.ndarray) -> np.ndarray:
            """
            Unpacked fitting
            
            :param x: Flattened x values
            :return: Flat y values
            """
            y = np.zeros_like(x)
            start = 0
            for i, fit_function in enumerate(self._fit_functions):
                end = data_shape[i] + start
                y[start:end] = fit_function(x[start:end], self._fit_objects[i].uid)
                start = end
            return y
        self.initialize(self._fit_objects, unpacked_fit_function)
        x = _flatten_list(x_list)
        y = _flatten_list(y_list)
        weights = None
        if weights_list is not None:
            weights = _flatten_list(weights_list)
        res = self.fit(x, y, weights=weights, model=model, parameters=parameters, method=method, **fitting_kwargs)
        return self.unflatten_results(res, data_shape)

    @staticmethod
    def unflatten_results(res, data_shape):
        x = []
        y_calc = []
        y_obs = []
        residual = []
        start = 0
        for i in data_shape:
            end = i + start
            x.append(res.x[start:end])
            y_calc.append(res.y_calc[start:end])
            y_obs.append(res.y_obs[start:end])
            residual.append(res.residual[start:end])
            start = end
        res.x = x
        res.y_calc = y_calc
        res.y_obs = y_obs
        res.residual = residual
        return res


def _flatten_list(this_list: list) -> list:
    """
    Flatten nested lists.

    :param this_list: List to be flattened

    :return: Flattened list
    """
    return np.array([item for sublist in this_list for item in sublist])
