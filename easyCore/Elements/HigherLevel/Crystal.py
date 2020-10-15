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

        self._extent = np.array([1, 1, 1])
        self._centre = np.array([0, 0, 0])

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
        offsets = np.array(np.meshgrid(range(0, self.extent[0] + 1),
                                       range(0, self.extent[1] + 1),
                                       range(0, self.extent[2] + 1))).T.reshape(-1, 3)
        for site in self.atoms:
            all_sites = np.array([op.operate(site.fract_coords) for op in sym_op])
            for offset in offsets[1:, :]:
                all_sites = np.concatenate((all_sites,
                                            np.array([op.operate(site.fract_coords + offset) for op in sym_op])),
                                           axis=0)
            site_positions = np.unique(all_sites, axis=0) - self.center
            sites[site.label.raw_value] = \
                site_positions[np.all(site_positions >= 0, axis=1) & np.all(site_positions <= self.extent, axis=1),
                :] + self.center
        return sites

    def to_cif_str(self) -> str:
        return str(self.cif)

    @property
    def extent(self):
        return self._extent

    @extent.setter
    def extent(self, new_extent: Union[list, np.ndarray]):
        if isinstance(new_extent, list):
            new_extent = np.array(new_extent)
        if np.prod(new_extent.shape) != 3:
            raise ValueError
        new_extent = new_extent.reshape((3,))
        self._extent = new_extent

    @property
    def center(self):
        return self._centre

    @center.setter
    def center(self, new_center):
        if isinstance(new_center, list):
            new_center = np.array(new_center)
        if np.prod(new_center.shape) != 3:
            raise ValueError
        new_center = new_center.reshape((3,))
        self._centre = new_center

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

    def __repr__(self) -> str:
        return f'Collection of {len(self)} phases.'

    def __getitem__(self, idx: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, BaseCollection]:
        if isinstance(idx, str) and idx in self.phase_names:
            idx = self.phase_names.index(idx)
        return super(Crystals, self).__getitem__(idx)

    def append(self, item: Crystal):
        if not isinstance(item, Crystal):
            raise TypeError('Item must be a Crystal')
        if item.name in self.phase_names:
            raise AttributeError(f'An atom of name {item.name} already exists.')
        super(Crystals, self).append(item)

    @property
    def phase_names(self) -> List[str]:
        return [phase.name for phase in self]
