__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numpy as np

from typing import List

from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
from easyCore.Objects.Groups import BaseCollection


class Atom(BaseObj):

    def __int__(self, label: str, specie: Descriptor,
                x_position: Parameter, y_position: Parameter, z_position: Parameter):
        super(Atom, self).__int__(label,
                                  specie=specie,
                                  x_position=x_position,
                                  y_position=y_position,
                                  z_position=z_position)

    @classmethod
    def default(cls, label: str, specie_label: str):
        specie = Descriptor('specie', specie_label)
        x_position = Parameter('x', 0.0)
        y_position = Parameter('y', 0.0)
        z_position = Parameter('z', 0.0)

        return cls(label, specie, x_position, y_position, z_position)

    @classmethod
    def from_pars(cls, label: str, specie_label: str, x: float, y: float, z: float):
        specie = Descriptor('specie', specie_label)
        x_position = Parameter('x', x)
        y_position = Parameter('y', y)
        z_position = Parameter('z', z)

        return cls(label, specie, x_position, y_position, z_position)

    def __repr__(self) -> str:
        return f'Atom {self.name} ({self.specie.raw_value}) @' \
               f' ({self.x.raw_value}, {self.y.raw_value}, {self.z.raw_value})'


class Atoms(BaseCollection):
    def __init__(self, name: str, *args, **kwargs):
        super(Atoms, self).__init__(name, *args, **kwargs)

    def __repr__(self) -> str:
        return f'Collection of {len(self)} Atoms.'
    
    @property
    def x_list(self) -> List[float]:
        return [atom.x.raw_value for atom in self]
    
    @property
    def y_list(self) -> List[float]:
        return [atom.y.raw_value for atom in self]
    
    @property
    def z_list(self) -> List[float]:
        return [atom.z.raw_value for atom in self]
    
    @property
    def positions(self) -> np.ndarray:
        return np.array([self.x_list, self.y_list, self.z_list]).transpose()
