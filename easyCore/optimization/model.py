#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import concurrent.futures as cf
import functools
import inspect
import warnings

try:
    import jax.numpy as np
except ImportError:
    from easyCore import np

from time import perf_counter
from typing import (
    Callable,
    TypeVar,
    Iterable,
    Optional,
    List,
    Union,
    Tuple,
    Any,
    Type,
    Dict,
    NoReturn,
)

T = TypeVar("T", bound=Iterable)
M = TypeVar("M", bound="Model")
CM = TypeVar("CM", bound="CompositeModel")


def value_wrapper(value, x):
    return value


def check_model(func: Callable) -> Callable:
    def checker(obj, model) -> Any:
        if not issubclass(model.__class__, Model):
            try:
                model = Model(model)
            except Exception:
                raise TypeError("The model must be a subclass of Model")
        return func(obj, model)

    return checker


class Model:
    def __init__(self, f: Optional[Callable] = None, parameters: Optional[dict] = None):
        if not hasattr(f, "__call__"):
            f = functools.partial(value_wrapper, f)
        self._function = f
        self._parameters = parameters
        s = inspect.signature(f)
        self._idx = sum(
            [
                isinstance(item.default, type(inspect._empty))
                or item.kind == inspect.Parameter.POSITIONAL_ONLY
                for n, item in s.parameters.items()
            ]
        )
        if parameters is None and f is not None:
            if len(s.parameters) == self._idx:
                self._parameters = {}
            else:
                p = s.parameters
                self._parameters = {
                    p[name].name: p[name].default
                    for name in list(s.parameters.keys())[self._idx : :]
                }
        self._count = 0
        self._parameter_history = {}
        self._initialize_parameters()
        self._runtime = []
        self._input_dimensions = 1

    def __call__(self, x, *args, **kwargs):
        self._count += 1
        if len(args) == len(self._parameters):
            for name, value in zip(self._parameters.keys(), args):
                self._parameter_history[name].append(value)
        fn = self._function
        if fn is None:
            return None
        start = perf_counter()
        try:
            results = fn(x, *args, **kwargs)
        except Exception:
            warnings.warn("The fn evaluation has failed", ResourceWarning)
            results = np.zeros_like(x)
        finally:
            self._runtime.append(perf_counter() - start)
        return results

    def _initialize_parameters(
        self, names: Optional[List[str]] = None, values: Optional[List[Any]] = None
    ):
        self.reset_count()
        if names is None or values is None:
            names = list(self._parameter_history.keys())
            values = list(self._parameter_history.values())

        params = [
            inspect.Parameter(
                "x", inspect.Parameter.POSITIONAL_ONLY, annotation=inspect._empty
            )
        ] + [
            inspect.Parameter(
                n,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=inspect._empty,
                default=v[0],
            )
            for n, v in zip(names, values)
        ]
        # Sign the function
        self.__call__.__func__.__signature__ = inspect.Signature(params)

    @property
    def count(self) -> int:
        return self._count

    def reset_count(self) -> NoReturn:
        names = []
        values = []
        for n, v in self._parameters.items():
            names.append(n)
            values.append(v)
            if hasattr(v, "value"):
                values[-1] = v.value
                if hasattr(values[-1], "raw_value"):
                    values[-1] = values[-1].raw_value
        self._count = 0
        self._parameter_history = {n: [v] for n, v in zip(names, values)}
        self._runtime: List[float] = []

    @property
    def parameter_history(
        self, parameter_name: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, List[float]]:
        if not isinstance(parameter_name, list):
            if isinstance(parameter_name, str):
                parameter_name = [parameter_name]
            else:
                parameter_name = list(self._parameter_history.keys())
        return {name: self._parameter_history[name] for name in parameter_name}

    @property
    def parameters(self) -> dict:
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: dict):
        self._parameters = parameters
        self._initialize_parameters()

    @property
    def function(self) -> Callable:
        return self._function

    @function.setter
    def function(self, function: Callable):
        self._function = function
        self.reset_count()

    @property
    def runtime(self) -> float:
        return np.sum(self._runtime, axis=0)

    @check_model
    def __add__(self, other: M) -> CM:
        return CompositeModel(self, other, np.add)

    @check_model
    def __sub__(self, other: M) -> CM:
        return CompositeModel(self, other, np.subtract)

    @check_model
    def __mul__(self, other: M) -> CM:
        return CompositeModel(self, other, np.multiply)

    @check_model
    def __truediv__(self, other: M) -> CM:
        return CompositeModel(self, other, np.divide)


class EasyModel(Model):
    def __init__(self, easy_object, fn_handle: str = None):
        if fn_handle is None:
            fn_handle = "__call__"
        function = getattr(easy_object, fn_handle)
        s = inspect.signature(function)
        parameters = easy_object.get_fit_parameters()
        self._cached_parameters = {param.name: param for param in parameters}
        parameters_dict = {
            parameter.name: parameter.raw_value for parameter in parameters
        }
        super(EasyModel, self).__init__(function, parameters_dict)

    def __call__(self, x, *args, **kwargs) -> Any:
        if len(args) == len(self._cached_parameters):
            for name, value in zip(self._cached_parameters.keys(), args):
                self._cached_parameters[name].value = value
        return super(EasyModel, self).__call__(x, *args, **kwargs)


class CompositeModel(Model):
    def __init__(
        self,
        left_model: Model,
        right_model: Model,
        function: Callable,
        fn_kwargs: Optional[Dict[str, Any]] = None,
    ):
        if fn_kwargs is None:
            fn_kwargs = {}
        self._left_model = left_model
        self._right_model = right_model
        lp = left_model.parameters.copy()
        rp = right_model.parameters.copy()
        super(CompositeModel, self).__init__(None, lp.update(rp))
        self._function = function
        self._function_kwargs = fn_kwargs

    def _initialize_parameters(self) -> NoReturn:
        left_names = list(self._left_model.parameters.keys())
        right_names = list(self._right_model.parameters.keys())
        names = left_names + right_names
        values = []
        for n in left_names:
            if hasattr(self._left_model.parameters[n], "raw_value"):
                values.append([self._left_model.parameters[n].raw_value])
            else:
                values.append([self._left_model.parameters[n]])
        for n in right_names:
            if hasattr(self._right_model.parameters[n], "raw_value"):
                values.append([self._right_model.parameters[n].raw_value])
            else:
                values.append([self._right_model.parameters[n]])
        super(CompositeModel, self)._initialize_parameters(names=names, values=values)

    def __call__(self, x, *args, **kwargs) -> Any:
        left = dict.fromkeys(self._left_model.parameters.keys())
        right = dict.fromkeys(self._right_model.parameters.keys())

        if len(args) == len(left) + len(right):
            for name, value in zip(left.keys(), args[: len(left)]):
                left[name] = value
            for name, value in zip(right.keys(), args[len(left) :]):
                right[name] = value
        else:
            for key in left.keys():
                if key in kwargs.keys():
                    left[key] = kwargs[key]
            for key in right.keys():
                if key in kwargs.keys():
                    right[key] = kwargs[key]

        return super(CompositeModel, self).__call__(
            self._left_model(x, **left),
            self._right_model(x, **right),
            **self._function_kwargs,
        )
