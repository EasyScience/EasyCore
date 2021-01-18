__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Callable

import weakref
import xarray as xr

from easyCore import np


@xr.register_dataset_accessor("easyCore")
class easyCoreAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._core_object = None
        self.__error_mapper = {}
        self.sigma_label_prefix = 's_'

    @property
    def core_object(self):
        if self._core_object is None:
            return None
        return self._core_object()

    @core_object.setter
    def core_object(self, new_core_object):
        self._core_object = weakref.ref(new_core_object)

    def sigma_generator(self, variable_label: str, sigma_func: Callable = np.sqrt, label_prefix: str = 's_'):
        sigma_label = label_prefix + variable_label
        self.__error_mapper[variable_label] = sigma_label
        self._obj[sigma_label] = sigma_func(self._obj[variable_label])

    def sigma_attach(self, variable_label: str, sigma_values, label_prefix: str = None):
        if label_prefix is None:
            label_prefix = self.sigma_label_prefix
        sigma_label = label_prefix + variable_label
        self.__error_mapper[variable_label] = sigma_label
        self._obj[sigma_label] = sigma_values
