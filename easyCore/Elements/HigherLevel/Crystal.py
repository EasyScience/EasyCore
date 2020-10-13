__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from pathlib import Path
from typing import Dict, Union, List

from easyCore import np
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Site, Atoms
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup
from easyCore.Objects.Base import BaseObj, Parameter, Descriptor
from easyCore.Objects.Groups import BaseCollection

from easyCore.Utils.io.cif import CifIO


class Crystal(BaseObj):

    def __init__(self, name, spacegroup=None, cell=None, atoms=None, interface=None):
        self.name = name
        if spacegroup is None:
            spacegroup = SpaceGroup.default()
        if cell is None:
            cell = Cell.default()
        if atoms is None:
            atoms = Atoms('atom_list')

        super(Crystal, self).__init__(name,
                                      cell=cell,
                                      spacegroup=spacegroup,
                                      atoms=atoms)
        self.interface = interface
        if self.interface is not None:
            self.interface.generate_bindings(self)

        self.extent = np.array([1, 1, 1])
        self.centre = np.array([0, 0, 0])

    def add_atom(self, *args, **kwargs):
        supplied_atom = False
        for arg in args:
            if isinstance(arg, Site):
                self.atoms.append(arg)
                supplied_atom = True
        if not supplied_atom:
            self.atoms.append(Site.from_pars(*args, **kwargs))

    def all_sites(self) -> Dict[str, np.ndarray]:
        sym_op = self.spacegroup.symmetry_opts
        sites = {}
        for site in self.atoms:
            site_positions = np.unique(np.array([op.operate(site.fract_coords) for op in sym_op]), axis=0) - self.centre
            sites[site.label.raw_value] = \
                site_positions[np.all(site_positions >= 0, axis=1) & np.all(site_positions <= self.extent, axis=1),
                :] + self.centre
        return sites

    def to_cif_str(self) -> str:
        return str(self.cif)

    @property
    def cif(self):
        return CifIO.from_objects(self.name, self.cell, self.spacegroup, self.atoms)

    @classmethod
    def from_cif_str(cls, in_string: str):
        cif = CifIO.from_cif_str(in_string)
        name, kwargs = cif.to_crystal_form()
        return cls(name, **kwargs)

    @classmethod
    def from_cif_file(cls, file_path: Path):
        cif = CifIO.from_file(file_path)
        name, kwargs = cif.to_crystal_form()
        return cls(name, **kwargs)


class Crystals(BaseCollection):

    def __init__(self, name: str = 'phases', *args, interface=None, **kwargs):
        super(Crystals, self).__init__(name, *args, **kwargs)
        self.interface = interface
        if self.interface is not None:
            self.interface.generate_bindings(self)

    def __repr__(self) -> str:
        return f'Collection of {len(self)} phases.'

    def __getitem__(self, i: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, BaseCollection]:
        if isinstance(i, str) and i in self.phase_names:
            i = self.phase_names.index(i)
        return super(Crystals, self).__getitem__(i)

    def append(self, item: Crystal):
        if not isinstance(item, Crystal):
            raise TypeError('Item must be a Crystal')
        if item.name in self.phase_names:
            raise AttributeError(f'An atom of name {item.name} already exists.')
        super(Crystals, self).append(item)

    @property
    def phase_names(self) -> List[str]:
        return [phase.name for phase in self]