__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Site, Atoms
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup

from easyCore.Utils.io.cif import CrystalCif


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
        self.atoms.append(Site.from_pars(*args, **kwargs))

    def all_sites(self):
        sym_op = self.spacegroup.symmetry_opts
        sites = {}
        for site in self.atoms:
            pos = np.unique(np.array([op.operate(site.coords) for op in sym_op]), axis=0) - self.centre
            sites[site.label.raw_value] = pos[np.all(pos >= 0, axis=1) & np.all(pos <= self.extent, axis=1), :] + self.centre
        return sites


    def to_cif_str(self) -> str:
        return str(CrystalCif(self.name, self.spacegroup, self.cell, self.atoms))

    @classmethod
    def from_cif_str(cls, in_string: str):
        star = CrystalCif.from_cif_str(in_string)
        items = star.items
        return cls(star.name,
                   *[item for item in items if isinstance(item, SpaceGroup)],
                   *[item for item in items if isinstance(item, Cell)],
                   *[item for item in items if isinstance(item, Atoms)]
                   )
