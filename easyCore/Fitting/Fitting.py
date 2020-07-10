__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from typing import Callable, Union, List
from lmfit import Parameter, Parameters
from lmfit import Model as lmModel


class Model(lmModel):
    def copy(self, **kwargs):
        super().copy(**kwargs)

    def __init__(self, func, params: Union[List, Parameters, type(None)] = None, **kwargs):

        super().__init__(func, params, **kwargs)
        parameters = self.param_names

        for parameter in parameters:
            setattr(
                self.__class__,
                parameter,
                property(self.__gitem(parameter), self.__sitem(parameter)),
            )

    def __repr__(self):
        info = ""
        params = self.make_params()
        for name, item in params.items():
            info += f"{name}={item.value}"
            if item.vary:
                info += f" ({item.min}, {item.max})"
            info += ", "
        if len(params) > 0:
            info = info[:-2]
        return f"{self.name}: {info}"

    @property
    def x0(self):
        params = self.make_params()
        return [
            params[key].value
            for key in params.keys()
            if params[key].vary
        ]

    @staticmethod
    def __gitem(key: str) -> Callable:
        def inner(obj):
            params = obj.make_params()
            try:
                data = params[key]
                return data.value
            except KeyError:
                raise AttributeError

        return lambda obj: inner(obj)

    @staticmethod
    def __sitem(key):
        return lambda obj, value: obj.set_param_hint(key, value=value)
