__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numpy as np

from typing import List
from copy import deepcopy

from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
from easyCore.Objects.Groups import BaseCollection

_ATOM_DETAILS = {
    'type_symbol': {
        'description': 'A code to identify the atom species occupying this site.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_type_symbol.html',
        'value':       '',
    },
    'position':    {
        'description': 'Atom-site coordinate as fractions of the unit cell length.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_fract_.html',
        'value':       0,
        'fixed':       True
    },
    'occupancy':   {
        'description': 'The fraction of the atom type present at this site.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_occupancy.html',
        'value':       1,
        'fixed':       True
    },
}


class Atom(BaseObj):

    def __init__(self, name: str, specie: Descriptor, occupancy: Parameter,
                 x_position: Parameter, y_position: Parameter, z_position: Parameter, interface=None):
        super(Atom, self).__init__(name,
                                   specie=specie,
                                   occupancy=occupancy,
                                   x=x_position,
                                   y=y_position,
                                   z=z_position)
        self.interface = interface
        if self.interface is not None:
            self.interface.generate_bindings(self)

    @classmethod
    def default(cls, name: str, specie_label: str, interface=None):
        specie = Descriptor('specie', specie_label, **_ATOM_DETAILS['type_symbol'])
        occupancy = Parameter('occupancy', **_ATOM_DETAILS['occupancy'])
        x_position = Parameter('x', **_ATOM_DETAILS['position'])
        y_position = Parameter('y', **_ATOM_DETAILS['position'])
        z_position = Parameter('z', **_ATOM_DETAILS['position'])
        return cls(name, specie, occupancy, x_position, y_position, z_position, interface=interface)

    @classmethod
    def from_pars(cls, name: str, specie_label: str,
                  occupancy: float = _ATOM_DETAILS['occupancy']['value'],
                  x: float = _ATOM_DETAILS['position']['value'],
                  y: float = _ATOM_DETAILS['position']['value'],
                  z: float = _ATOM_DETAILS['position']['value'],
                  interface=None):
        specie = Descriptor('specie', specie_label)
        pos = deepcopy(_ATOM_DETAILS['position'])
        del pos['value']
        x_position = Parameter('x', x, **pos)
        y_position = Parameter('y', y, **pos)
        z_position = Parameter('z', z, **pos)
        occ = deepcopy(_ATOM_DETAILS['occupancy'])
        del occ['value']
        occupancy = Parameter('occupancy', occupancy, **occ)

        return cls(name, specie, occupancy, x_position, y_position, z_position, interface=interface)

    def __repr__(self) -> str:
        return f'Atom {self.name} ({self.specie.raw_value}) @' \
               f' ({self.x.raw_value}, {self.y.raw_value}, {self.z.raw_value})'


class Atoms(BaseCollection):
    def __init__(self, name: str, *args, interface=None, **kwargs):
        super(Atoms, self).__init__(name, *args, **kwargs)
        self.interface = interface
        if self.interface is not None:
            self.interface.generate_bindings(self)

    def __repr__(self) -> str:
        return f'Collection of {len(self)} Atoms.'

    @property
    def x_positions(self) -> np.ndarray:
        return np.array([atom.x.raw_value for atom in self])

    @property
    def y_positions(self) -> np.ndarray:
        return np.array([atom.y.raw_value for atom in self])

    @property
    def z_positions(self) -> np.ndarray:
        return np.array([atom.z.raw_value for atom in self])

    @property
    def atom_labels(self) -> List[str]:
        return [atom.name.raw_value for atom in self]

    @property
    def atom_species(self) -> List[str]:
        return [atom.specie.raw_value for atom in self]

    @property
    def atom_positions(self) -> np.ndarray:
        return np.array([self.x_positions, self.y_positions, self.z_positions]).transpose()

    @property
    def atom_occupancies(self) -> np.ndarray:
        return np.array([atom.occupancy.raw_value for atom in self])
