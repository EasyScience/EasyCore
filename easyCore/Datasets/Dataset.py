__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List, Union, TypeVar, Callable


from xarray.core.utils import FrozenDict
import matplotlib.pyplot as plt

from easyCore import np, ureg
from .xarray import xr #This xarray has the easyCore accessor

T_ = TypeVar('T_')


class Dataset:
    def __init__(self, name: str = '', description: str = '', url: str = '', core_obj=None):
        self._data = xr.Dataset()
        self._data.attrs['units'] = {}
        self._data.attrs['name'] = name
        self._data.attrs['description'] = description
        self._data.attrs['url'] = url

        if core_obj is not None:
            self._data.easyCore.core_object = core_obj

    @property
    def dataset(self) -> xr.Dataset:
        return self._data

    def plot(self, variable: str, *args, plot_type: str = 'line', **kwargs):
        p_fun = getattr(xr.plot, plot_type, None)
        if p_fun is None:
            raise ValueError
        if not isinstance(variable, list):
            variable = [variable]
        p_res = []
        for var in variable:
            res = p_fun(self._data[var], *args, **kwargs)
            if isinstance(res, list):
                p_res = [*p_res, *res]
            else:
                p_res = p_res.append(res)    
        if self.name:
            plt.title(self.name)
        return p_res

    @property
    def name(self) -> str:
        return self._data.attrs['name']

    @name.setter
    def name(self, value: str):
        self._data.attrs['name'] = value

    @property
    def description(self) -> str:
        return self._data.attrs['description']

    @description.setter
    def description(self, value: str):
        self._data.attrs['description'] = value

    @property
    def url(self) -> str:
        return self._data.attrs['url']

    @url.setter
    def url(self, value: str):
        self._data.attrs['url'] = value

    @property
    def core_obj(self):
        return self._data.easyCore.core_object

    @core_obj.setter
    def core_obj(self, new_obj):
        self._data.easyCore.core_object = new_obj

    @property
    def units(self) -> FrozenDict:
        return FrozenDict(**self._data.attrs['units'])

    @property
    def tools(self):
        return self._data.easyCore

    def add_dimension(self, axis_name: str, axis_values: Union[List[T_], np.ndarray], unit=''):
        self._data.coords[axis_name] = axis_values
        self._data.attrs['units'][axis_name] = ureg.Unit(unit)

    def remove_dimension(self, axis_name: str):
        # TODO This should check coords and fail if coord is in use
        self._data.re
        del self._data.coords[axis_name]
        del self._data.attrs['units'][axis_name]

    def add_variable(self, variable_name, variable_dimension: Union[str, List[str]],
                     variable_values: Union[List[T_], np.ndarray], variable_sigma: Union[List[T_], np.ndarray] = None,
                     unit: str = '', auto_sigma: bool = False):
        if isinstance(variable_dimension, str):
            variable_dimension = [variable_dimension]

        if not isinstance(variable_dimension, (list, tuple)):
            raise ValueError

        known_keys = self._data.coords.keys()
        for dimension in variable_dimension:
            if dimension not in known_keys:
                raise ValueError

        self._data[variable_name] = (variable_dimension, variable_values)

        if variable_sigma is not None:
            if isinstance(variable_sigma, (Callable, np.ndarray)):
                self.tools.sigma_generator(variable_name, variable_sigma)
            elif isinstance(variable_sigma, list):
                self.tools.sigma_generator(variable_name, np.array(variable_sigma))
        else:
            if auto_sigma:
                self.tools.sigma_generator(variable_name)

        self._data.attrs['units'][variable_name] = ureg.Unit(unit)
        if unit and variable_sigma is None and auto_sigma:
            self._data.attrs['units'][self.tools.sigma_label_prefix + variable_name] = ureg.Unit(unit + ' ** 0.5')
        else:
            if auto_sigma:
                self._data.attrs['units'][self.tools.sigma_label_prefix + variable_name] = ureg.Unit('')

    def remove_variable(self, variable_name: str):
        del self._data[variable_name]

    def set_unit(self, axis_name: str, unit: str):
        if axis_name not in self._data.keys():
            raise ValueError
        self._data.attrs['units'][axis_name] = ureg.Unit(unit)

