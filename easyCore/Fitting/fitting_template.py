__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from abc import ABCMeta, abstractmethod
from typing import Union, Callable
from easyCore.Utils.typing import noneType


class FittingTemplate(metaclass=ABCMeta):

    _engines = []
    property_type = None
    name = None

    def __init_subclass__(cls, is_abstract=False, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_abstract:
            cls._engines.append(cls)

    def __init__(self, obj, fit_function: Callable):
        self._object = obj
        self._fit_function = fit_function

    @abstractmethod
    def make_model(self):
        pass

    @abstractmethod
    def _generate_fit_function(self):
        pass

    @abstractmethod
    def fit(self, data, model, parameters, **kwargs):
        pass

    @abstractmethod
    def convert_to_pars_obj(self, par_list: Union[list, noneType] = None):
        pass

    @staticmethod
    @abstractmethod
    def convert_to_par_object(obj):
        pass
