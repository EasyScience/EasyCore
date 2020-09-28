__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List
from copy import deepcopy

from easyCore import np
from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
from easyCore.Objects.Groups import BaseCollection

from easyCore.Utils.io.star import StarLoop

_SITE_DETAILS = {
    'label':       {
        'description': 'A unique identifier for a particular site in the crystal',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_label.html',
    },
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

_CIF_CONVERSIONS = [
    ['label', 'atom_site_label'],
    ['specie', 'atom_site_type_symbol'],
    ['occupancy', 'atom_site_occupancy'],
    ['x', 'atom_site_fract_x'],
    ['y', 'atom_site_fract_y'],
    ['z', 'atom_site_fract_z']
]


class Site(BaseObj):

    def __init__(self, label: Descriptor, specie: Descriptor, occupancy: Parameter,
                 x_position: Parameter, y_position: Parameter, z_position: Parameter, interface=None):
        super(Site, self).__init__('site',
                                   label=label,
                                   specie=specie,
                                   occupancy=occupancy,
                                   x=x_position,
                                   y=y_position,
                                   z=z_position)
        self.interface = interface
        if self.interface is not None:
            self.interface.generate_bindings(self)

    @classmethod
    def default(cls, label: str, specie_label: str, interface=None):
        label = Descriptor('label', label, **_SITE_DETAILS['label'])
        specie = Descriptor('specie', specie_label, **_SITE_DETAILS['type_symbol'])
        occupancy = Parameter('occupancy', **_SITE_DETAILS['occupancy'])
        x_position = Parameter('x', **_SITE_DETAILS['position'])
        y_position = Parameter('y', **_SITE_DETAILS['position'])
        z_position = Parameter('z', **_SITE_DETAILS['position'])
        return cls(label, specie, occupancy, x_position, y_position, z_position, interface=interface)

    @classmethod
    def from_pars(cls,
                  label: str,
                  specie: str,
                  occupancy: float = _SITE_DETAILS['occupancy']['value'],
                  x: float = _SITE_DETAILS['position']['value'],
                  y: float = _SITE_DETAILS['position']['value'],
                  z: float = _SITE_DETAILS['position']['value'],
                  interface=None):
        label = Descriptor('label', label, **_SITE_DETAILS['label'])
        specie = Descriptor('specie', specie)
        pos = deepcopy(_SITE_DETAILS['position'])
        del pos['value']
        x_position = Parameter('x', x, **pos)
        y_position = Parameter('y', y, **pos)
        z_position = Parameter('z', z, **pos)
        occ = deepcopy(_SITE_DETAILS['occupancy'])
        del occ['value']
        occupancy = Parameter('occupancy', occupancy, **occ)

        return cls(label, specie, occupancy, x_position, y_position, z_position, interface=interface)

    def __repr__(self) -> str:
        return f'Atom {self.name} ({self.specie.raw_value}) @' \
               f' ({self.x.raw_value}, {self.y.raw_value}, {self.z.raw_value})'

    @property
    def coords(self) -> np.ndarray:
        """
        Get the current sites fractional co-ordinates as an array

        :return: Array containing fractional co-ordinates
        :rtype: np.ndarray
        """
        return np.array([self.x.raw_value, self.y.raw_value, self.z.raw_value])

    def distance(self, other_site: 'Site') -> float:
        """
        Get the distance between two sites

        :param other_site: Second site
        :type other_site: Site
        :return: Distance between 2 sites
        :rtype: float
        """
        return np.linalg.norm(other_site.coords - self.coords)


class Atoms(BaseCollection):
    def __init__(self, name: str, *args, interface=None, **kwargs):
        super(Atoms, self).__init__(name, *args, **kwargs)
        self.interface = interface
        if self.interface is not None:
            self.interface.generate_bindings(self)

    def __repr__(self) -> str:
        return f'Collection of {len(self)} sites.'

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
        return [atom.label.raw_value for atom in self]

    @property
    def atom_species(self) -> List[str]:
        return [atom.specie.raw_value for atom in self]

    @property
    def atom_positions(self) -> np.ndarray:
        return np.array([self.x_positions, self.y_positions, self.z_positions]).transpose()

    @property
    def atom_occupancies(self) -> np.ndarray:
        return np.array([atom.occupancy.raw_value for atom in self])

    def to_star(self) -> StarLoop:
        return StarLoop(self, [name[1] for name in _CIF_CONVERSIONS])

    @classmethod
    def from_string(cls, in_string: str):
        s = StarLoop.from_string(in_string, [name[0] for name in _CIF_CONVERSIONS])
        return s.to_class(cls, Site)