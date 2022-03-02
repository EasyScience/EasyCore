#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

try:
    import jax
    import jax.numpy as np
except ImportError:
    jax = None
    from easyCore import np

import inspect
from time import perf_counter
from typing import (
    Optional,
    Callable,
    NoReturn,
    List,
    Any,
    TypeVar,
    Iterable,
    Dict,
    ClassVar,
)

from easyCore.Objects.ObjectClasses import BaseObj, BasedBase, tree_creator
from easyCore.Objects.Variable import Descriptor, Parameter


T = TypeVar("T", bound=Iterable)
M = TypeVar("M", bound="Model")
CM = TypeVar("CM", bound="CompositeModel")


def check_model(func: Callable) -> Callable:
    def checker(obj, model) -> Any:
        if not issubclass(model.__class__, Model):
            try:
                model = Model(model)
            except Exception:
                raise TypeError("The model must be a subclass of Model")
        return func(obj, model)

    return checker


def tree_flatten_Model(self):
    children = list(self._kwargs.values())
    aux_data = {"name": self.name, "keys": list(self._kwargs.keys()), "aux": {}}
    aux_data["aux"]["func"] = self._func
    if hasattr(self, "fn_kwargs"):
        aux_data["aux"]["fn_kwargs"] = self.fn_kwargs
    return children, aux_data


def tree_creator_Model(cls):
    def tree_unflatten(aux_data, children) -> cls:
        kw = inspect.signature(cls).parameters.keys()
        kwargs = {}
        if "name" in kw:
            kwargs["name"] = aux_data["name"]
        if "parameters" in kw:
            kwargs["parameters"] = dict(zip(aux_data["keys"], children))
        else:
            if "left_model" in kw and "right_model" in kw:
                kwargs["left_model"] = children[0]
                kwargs["right_model"] = children[1]
            else:
                raise ValueError("The model must have a left_model or right_model")
        if "fn_kwargs" in kw:
            kwargs["fn_kwargs"] = aux_data["aux"]["fn_kwargs"]
        kwargs.update(aux_data["aux"])
        return cls(**kwargs)

    return tree_unflatten


class Model(BaseObj):
    def __init__(
        self,
        func: Optional[Callable] = None,
        parameters: Optional[dict] = None,
        fn_kwargs: Optional[dict] = None,
        register_jax: Optional[bool] = True,
    ):
        easy_par = {}
        if parameters is None:
            parameters = {}
        self._user_supplied = list(parameters.keys())
        for key, value in parameters.items():
            if not issubclass(value.__class__, (Descriptor, BasedBase)):
                easy_par[key] = Parameter(key, value)
            else:
                easy_par[key] = value
        super().__init__(f"Model_{func.__name__}", **easy_par, register_jax=False)
        self._func = func
        self._count = 0
        self._parameter_history = {}
        self._runtime = []
        self._input_dimensions = 1
        if fn_kwargs is None:
            fn_kwargs = {}
        self._fn_kwargs = fn_kwargs
        self._checkpoint = 0
        if jax is not None and register_jax:
            try:
                # The better way of doing this would be to use jax.tree_util._registry, but we can't query it
                jax.tree_util.register_pytree_node(
                    self.__class__,
                    tree_flatten_Model,
                    tree_creator_Model(self.__class__),
                )
                self._jax_registered = True
            except ValueError:
                pass

    @property
    def _encoded_parameter_names(self):
        return [
            str(self._borg.map.convert_id_to_key(item))
            for item in self.get_fit_parameters()
        ]

    def __call__(self, x, *args, **kwargs):
        self._count += 1
        pars = self.get_fit_parameters()
        generic_names = [par.name for par in pars]
        possible_names = self._encoded_parameter_names

        if len(args) == len(pars):
            for par, arg in zip(pars, args):
                par.value = arg
        for key, item in kwargs.items():
            if key in generic_names:
                pars[generic_names.index(key)].value = item
            elif key in possible_names:
                pars[possible_names.index(key)].value = item
        for par, possible in zip(pars, possible_names):
            a = self._parameter_history.get(possible, [])
            a.append(par.raw_value)
            self._parameter_history[possible] = a

        aargs = {
            key: pars[generic_names.index(key)].raw_value
            for key in self._user_supplied
            if key in generic_names
        }
        fn = self._func
        if fn is None:
            return None
        start = perf_counter()
        try:
            results = fn(x, *args, **aargs, **kwargs, **self._fn_kwargs)
        finally:
            self._runtime.append(perf_counter() - start)
        return results

    def model(self, theta, x):
        return self(x, *theta)

    @property
    def count(self) -> int:
        return self._count

    @property
    def function(self) -> Callable:
        return self._func

    def checkpoint(self):
        self._checkpoint = self._count

    def reset_checkpoint(self) -> NoReturn:
        self._checkpoint = 0

    def reset(self) -> NoReturn:
        c_pars = self.get_fit_parameters()
        c_names = self._encoded_parameter_names
        for name, par in zip(c_names, c_pars):
            if name in self._parameter_history.keys():
                par.value = self._parameter_history[name][self._checkpoint]
        self._count = 0
        self._parameter_history = {}
        self._runtime: List[float] = []
        self._checkpoint = 0

    @property
    def fn_kwargs(self) -> dict:
        return self._fn_kwargs

    @fn_kwargs.setter
    def fn_kwargs(self, fn_kwargs: dict):
        self._fn_kwargs = fn_kwargs

    @property
    def runtime(self) -> float:
        return np.sum(np.array(self._runtime), axis=0)

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

    def plot(self, plt, x, fn_args, *args, fn_kwargs, **kwargs):
        plt.plot(x, self(x, *fn_args, **fn_kwargs), *args, **kwargs)


def tree_flatten_easyModel(self):
    children = list(self._kwargs.values())
    aux_data = {"name": self.name, "keys": list(self._kwargs.keys()), "aux": {}}
    if hasattr(self, "_fn_handle"):
        aux_data["aux"]["fn_handle"] = self._fn_handle
        if getattr(aux_data["aux"], "func", None) is not None:
            del aux_data["aux"]["func"]
    return children, aux_data


class EasyModel(Model):

    easy_model: ClassVar[Model]

    def __init__(self, easy_model, fn_handle: str = None):
        self._fn_handle = fn_handle
        if fn_handle is None:
            fn_handle = "__call__"
            self._fn_handle = fn_handle
        function = getattr(easy_model, fn_handle)
        super(EasyModel, self).__init__(
            function, parameters={"easy_model": easy_model}, register_jax=False
        )
        if jax is not None:
            try:
                # The better way of doing this would be to use jax.tree_util._registry, but we can't query it
                jax.tree_util.register_pytree_node(
                    self.__class__, tree_flatten_easyModel, tree_creator(self.__class__)
                )
                self._jax_registered = True
            except ValueError:
                pass


class CompositeModel(Model):

    left_model: ClassVar[Model]
    right_model: ClassVar[Model]

    def __init__(
        self,
        left_model: Model,
        right_model: Model,
        func: Callable,
        fn_kwargs: Optional[Dict[str, Any]] = None,
    ):
        if fn_kwargs is None:
            fn_kwargs = {}
        parameters = {"left_model": left_model, "right_model": right_model}
        super(CompositeModel, self).__init__(
            func, parameters=parameters, fn_kwargs=fn_kwargs
        )

    def __call__(self, x, *args, **kwargs) -> Any:
        left_items = self.left_model.get_fit_parameters()
        right_items = self.right_model.get_fit_parameters()
        left_keys = self.left_model._encoded_parameter_names
        right_keys = self.right_model._encoded_parameter_names
        left_names = [item for item in left_items]
        right_names = [item.name for item in right_items]

        left_kwargs = {}
        right_kwargs = {}

        for arg in kwargs.keys():
            if arg in left_keys:
                left_kwargs[arg] = kwargs[arg]
            elif arg in left_names:
                left_kwargs[left_names.index(arg)] = kwargs[arg]
            elif arg in right_keys:
                right_kwargs[arg] = kwargs[arg]
            elif arg in right_names:
                right_kwargs[right_names.index(arg)] = kwargs[arg]
            else:
                raise ValueError(f"{arg} is not a parameter of the composite model")

        if len(args) == len(left_keys) + len(right_keys):
            for name, value in zip(left_keys, args[: len(left_keys)]):
                left_kwargs[name] = value
            for name, value in zip(right_keys, args[len(left_keys) :]):
                right_kwargs[name] = value

        return super(CompositeModel, self).__call__(
            self.left_model(x, **left_kwargs), self.right_model(x, **right_kwargs)
        )
