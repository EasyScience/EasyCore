#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from typing import List, Union

from easyCore import np
from easyCore.Elements.Basic.Lattice import PeriodicLattice
from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
from easyCore.Objects.Groups import BaseCollection
from easyCore.Elements.Basic.Specie import Specie
from easyCore.Elements.Basic.AtomicDisplacement import AtomicDisplacement
from easyCore.Utils.io.star import StarLoop

_SITE_DETAILS = {
    'label':       {
        'description': 'A unique identifier for a particular site in the crystal',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_label.html',
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

    def __init__(self, label: Descriptor, specie: Specie, occupancy: Parameter,
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
    def default(cls, label: str, specie: str = '', interface=None):
        label = Descriptor('label', label, **_SITE_DETAILS['label'])
        if not specie:
            specie = label.raw_value
        specie = Specie(specie)
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
        specie = Specie(specie)

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
        self._add_component('adp', adp_type)
        if self.interface is not None:
            self.interface.generate_bindings()

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
        :param other_site: Second site
        :type other_site: Site
        :return: Distance between 2 sites
        :rtype: float
        """
        return np.linalg.norm(other_site.fract_coords - self.fract_coords)

    @property
    def x(self):
        return self.fract_x

    @property
    def y(self):
        return self.fract_y

    @property
    def z(self):
        return self.fract_z

    @property
    def is_magnetic(self):
        return self.specie.spin is not None


class PeriodicSite(Site):

    def __init__(self, lattice: PeriodicLattice, label: Descriptor, specie: Descriptor, occupancy: Parameter,
                 fract_x: Parameter, fract_y: Parameter, fract_z: Parameter,
                 interface=None, **kwargs):
        super(PeriodicSite, self).__init__(label, specie, occupancy,
                 fract_x, fract_y, fract_z, interface, **kwargs)
        self.lattice = lattice

    @classmethod
    def from_site(cls, lattice: PeriodicLattice, site: Site):
        args = [lattice, site.label, site.specie, site.occupancy,
            site.fract_x, site.fract_y, site.fract_z]
        kwargs = {
            'interface': site.interface
        }
        if hasattr(site, 'adp'):
            kwargs['adp'] = site.adp
        return cls(*args, **kwargs)

    def get_orbit(self) -> np.ndarray:
        """
        Generate all orbits for a given fractional position.

        """
        sym_op = self.lattice.spacegroup._sg_data.get_orbit
        return sym_op(self.fract_coords)

    @property
    def cart_coords(self) -> np.ndarray:
        """
        Get the atomic position in Cartesian form.
        :return:
        :rtype:
        """
        return self.lattice.get_cartesian_coords(self.fract_coords)


class Atoms(BaseCollection):
    def __init__(self, name: str, *args, interface=None, **kwargs):
        if not isinstance(name, str):
            raise TypeError('A `name` for this collection must be given in string form')
        super(Atoms, self).__init__(name, *args, **kwargs)
        self.interface = interface
        self._kwargs._stack_enabled = True

    def __repr__(self) -> str:
        return f'Collection of {len(self)} sites.'

    def __getitem__(self, idx: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, 'BaseCollection']:
        if isinstance(idx, str) and idx in self.atom_labels:
            idx = self.atom_labels.index(idx)
        return super(Atoms, self).__getitem__(idx)

    def __delitem__(self, key):
        if isinstance(key, str) and key in self.atom_labels:
            key = self.atom_labels.index(key)
        return super(Atoms, self).__delitem__(key)

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


class PeriodicAtoms(Atoms):
    def __init__(self, name: str, *args, lattice=None, interface=None, **kwargs):
        args = list(args)
        if lattice is None:
            for item in args:
                if hasattr(item, 'lattice'):
                    lattice = item.lattice
                    break
        if lattice is None:
            raise AttributeError
        for idx, item in enumerate(args):
            if isinstance(item, Site):
                args[idx] = PeriodicSite.from_site(lattice, item)
        super(PeriodicAtoms, self).__init__(name, *args, **kwargs, interface=interface)
        self.lattice = lattice

    @classmethod
    def from_atoms(cls, lattice: PeriodicLattice, atoms):
        return cls(atoms.name, *atoms, lattice=lattice, interface=atoms.interface)

    def __repr__(self) -> str:
        return f'Collection of {len(self)} periodic sites.'

    def append(self, item: Site):
        if not issubclass(item.__class__, Site):
            raise TypeError('Item must be a Site or periodic site')
        if item.label.raw_value in self.atom_labels:
            raise AttributeError(f'An atom of name {item.label.raw_value} already exists.')
        if isinstance(item, Site):
            item = PeriodicSite.from_site(self.lattice, item)
        super(PeriodicAtoms, self).append(item)

    def get_orbits(self, magnetic_only=False):
        orbit_dict = {}
        for item in self:
            if magnetic_only and not item.is_magnetic:
                continue
            orbit_dict[item.label.raw_value] = item.get_orbit()
        return orbit_dict
