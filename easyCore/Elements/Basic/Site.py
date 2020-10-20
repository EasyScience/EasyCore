__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List, Union

from easyCore import np
from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
from easyCore.Objects.Groups import BaseCollection
from easyCore.Elements.Basic.AtomicDisplacement import AtomicDisplacement
from easyCore.Utils.classTools import addLoggedProp
from easyCore.Utils.io.star import StarLoop

_SITE_DETAILS = {
    'label':       {
        'description': 'A unique identifier for a particular site in the crystal',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_label.html',
    },
    'type_symbol': {
        'description': 'A code to identify the atom species occupying this site.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_type_symbol.html',
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


class Site(BaseObj):
    _CIF_CONVERSIONS = [
        ['label', 'atom_site_label'],
        ['specie', 'atom_site_type_symbol'],
        ['occupancy', 'atom_site_occupancy'],
        ['fract_x', 'atom_site_fract_x'],
        ['fract_y', 'atom_site_fract_y'],
        ['fract_z', 'atom_site_fract_z']
    ]

    def __init__(self, label: Descriptor, specie: Descriptor, occupancy: Parameter,
                 fract_x: Parameter, fract_y: Parameter, fract_z: Parameter,
                 interface=None, **kwargs):
        # We can attach adp etc, which would be in kwargs. Filter them out...
        # But first, check if we've been given an adp..
        adp = None
        if 'adp' in kwargs.keys():
            adp = kwargs['adp']
            del kwargs['adp']
        k_wargs = {k: kwargs[k] for k in kwargs.keys() if issubclass(kwargs[k].__class__, (Descriptor, Parameter, BaseObj))}
        kwargs = {k: kwargs[k] for k in kwargs.keys() if not issubclass(kwargs[k].__class__, (Descriptor, Parameter, BaseObj))}
        super(Site, self).__init__('site',
                                   label=label,
                                   specie=specie,
                                   occupancy=occupancy,
                                   fract_x=fract_x,
                                   fract_y=fract_y,
                                   fract_z=fract_z,
                                   **k_wargs)
        self.interface = interface
        if adp is not None:
            self.add_adp(adp)

    @classmethod
    def default(cls, label: str, specie: str, interface=None):
        label = Descriptor('label', label, **_SITE_DETAILS['label'])
        specie = Descriptor('specie', specie, **_SITE_DETAILS['type_symbol'])
        occupancy = Parameter('occupancy', **_SITE_DETAILS['occupancy'])
        x_position = Parameter('fract_x', **_SITE_DETAILS['position'])
        y_position = Parameter('fract_y', **_SITE_DETAILS['position'])
        z_position = Parameter('fract_z', **_SITE_DETAILS['position'])
        return cls(label, specie, occupancy, x_position, y_position, z_position, interface=interface)

    @classmethod
    def from_pars(cls,
                  label: str,
                  specie: str,
                  occupancy: float = _SITE_DETAILS['occupancy']['value'],
                  fract_x: float = _SITE_DETAILS['position']['value'],
                  fract_y: float = _SITE_DETAILS['position']['value'],
                  fract_z: float = _SITE_DETAILS['position']['value'],
                  interface=None):

        label = Descriptor('label', label, **_SITE_DETAILS['label'])
        specie = Descriptor('specie', value=specie, **_SITE_DETAILS['type_symbol'])

        pos = {k: _SITE_DETAILS['position'][k]
               for k in _SITE_DETAILS['position'].keys()
               if k != 'value'}

        x_position = Parameter('fract_x', value=fract_x, **pos)
        y_position = Parameter('fract_y', value=fract_y, **pos)
        z_position = Parameter('fract_z', value=fract_z, **pos)
        occupancy = Parameter('occupancy', value=occupancy, **{k: _SITE_DETAILS['occupancy'][k]
                                                               for k in _SITE_DETAILS['occupancy'].keys()
                                                               if k != 'value'})

        return cls(label, specie, occupancy, x_position, y_position, z_position, interface=interface)

    def add_adp(self, adp_type: Union[str, AtomicDisplacement], **kwargs):
        if isinstance(adp_type, str):
            adp_type = AtomicDisplacement.from_pars(adp_type, interface=self.interface, **kwargs)
        self.add_component(adp_type)

    def add_component(self, component):
        key = ''
        if isinstance(component, AtomicDisplacement):
            key = 'adp'
        if not key:
            raise ValueError
        self._kwargs[key] = component
        self._borg.map.add_edge(self, component)
        self._borg.map.reset_type(component, 'created_internal')
        addLoggedProp(self, key, self.__getter(key), self.__setter(key), get_id=key, my_self=self,
                      test_class=BaseObj)

    def __repr__(self) -> str:
        return f'Atom {self.name} ({self.specie.raw_value}) @' \
               f' ({self.fract_x.raw_value}, {self.fract_y.raw_value}, {self.fract_z.raw_value})'

    @property
    def name(self):
        return self.label.raw_value

    @property
    def fract_coords(self) -> np.ndarray:
        """
        Get the current sites fractional co-ordinates as an array

        :return: Array containing fractional co-ordinates
        :rtype: np.ndarray
        """
        return np.array([self.fract_x.raw_value, self.fract_y.raw_value, self.fract_z.raw_value])

    def fract_distance(self, other_site: 'Site') -> float:
        """
        Get the distance between two sites

        :param other_site: Second site
        :type other_site: Site
        :return: Distance between 2 sites
        :rtype: float
        """
        return np.linalg.norm(other_site.fract_coords - self.fract_coords)

    @staticmethod
    def __getter(key: str):

        def getter(obj):
            return obj._kwargs[key]

        return getter

    @staticmethod
    def __setter(key):
        def setter(obj, value):
            if issubclass(obj._kwargs[key].__class__, Descriptor):
                obj._kwargs[key].value = value
            else:
                obj._kwargs[key] = value

        return setter


class PeriodicSite(Site):

    def __init__(self, lattice, label: Descriptor, specie: Descriptor, occupancy: Parameter,
                 x_position: Parameter, y_position: Parameter, z_position: Parameter,
                 interface=None, **kwargs):
        super(PeriodicSite, self).__init__(label, specie, occupancy,
                 x_position, y_position, z_position, interface, **kwargs)
        self.lattice = lattice


class Atoms(BaseCollection):
    def __init__(self, name: str, *args, interface=None, **kwargs):
        super(Atoms, self).__init__(name, *args, **kwargs)
        self.interface = interface

    def __repr__(self) -> str:
        return f'Collection of {len(self)} sites.'

    def __getitem__(self, idx: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, 'BaseCollection']:
        if isinstance(idx, str) and idx in self.atom_labels:
            idx = self.atom_labels.index(idx)
        return super(Atoms, self).__getitem__(idx)

    def append(self, item: Site):
        if not isinstance(item, Site):
            raise TypeError('Item must be a Site')
        if item.label.raw_value in self.atom_labels:
            raise AttributeError(f'An atom of name {item.label.raw_value} already exists.')
        super(Atoms, self).append(item)

    @property
    def atom_labels(self) -> List[str]:
        return [atom.label.raw_value for atom in self]

    @property
    def atom_species(self) -> List[str]:
        return [atom.specie.raw_value for atom in self]

    @property
    def atom_occupancies(self) -> np.ndarray:
        return np.array([atom.occupancy.raw_value for atom in self])

    def to_star(self) -> List[StarLoop]:
        adps = [hasattr(item, 'adp') for item in self]
        has_adp = any(adps)
        main_loop = StarLoop(self, exclude=['adp'])
        if not has_adp:
            return [main_loop]
        add_loops = []
        adp_types = [item.adp.adp_type.raw_value for item in self]
        if all(adp_types):
            if adp_types[0] in ['Uiso', 'Biso']:
                main_loop = main_loop.join(StarLoop.from_StarSections([getattr(item, 'adp').to_star(item.label) for item in self]), 'label')
            else:
                entries = []
                for item in self:
                    entries.append(item.adp.to_star(item.label))
                add_loops.append(StarLoop.from_StarSections(entries))
        else:
            raise NotImplementedError('Multiple types of ADP are not supported')
        loops = [main_loop, *add_loops]
        return loops

    @classmethod
    def from_string(cls, in_string: str):
        s = StarLoop.from_string(in_string, [name[0] for name in Site._CIF_CONVERSIONS])
        return s.to_class(cls, Site)
