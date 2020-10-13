__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Dict

from easyCore import np
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Site, Atoms
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup

from easyCore.Utils.io.cif import CifIO


class Crystal:

    def __init__(self, name, spacegroup=None, cell=None, atoms=None):
        self.name = name
        if spacegroup is None:
            self.spacegroup = SpaceGroup.default()
        else:
            self.spacegroup = spacegroup
        if cell is None:
            self.cell = Cell.default()
        else:
            self.cell = cell
        if atoms is None:
            self.atoms = Atoms('atom_list')
        else:
            self.atoms = atoms

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
                site_positions[np.all(site_positions >= 0, axis=1) & np.all(site_positions <= self.extent, axis=1), :] + self.centre
        return sites

    def to_cif_str(self) -> str:
        return str(CifIO.from_objects(self.name, self.cell, self.spacegroup, self.atoms))

    @classmethod
    def from_cif_str(cls, in_string: str):
        cif = CifIO.from_cif_str(in_string)
        name, kwargs = cif.to_crystal_form()
        return cls(name, **kwargs)
