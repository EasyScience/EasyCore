__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List, Union, TypeVar, Tuple

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt


T_ = TypeVar('T_')


class Dataset:
    def __init__(self, name: str = '', description: str = '', url: str = '', linked=None):
        self.name = name
        self.description = description
        self.url = url
        self.linked = linked
        self.data = xr.Dataset()

    @property
    def dimensions(self) -> List[int]:
        return list(self.data.dims.values())

    def add_coordinates(self, axis_name: str, axis_values: Union[List[T_], np.ndarray]):
        self.data[axis_name] = axis_values

    def add_variable(self, variable_name, variable_coords: Tuple[str, str], variable_values: Union[List[T_], np.ndarray]):
        self.data[variable_name] = (variable_coords, variable_values)

    def __call__(self):
        return self.data