__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Utils.io.star import StarHeader, StarCollection, StarLoop, StarEntry, StarSection
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Atoms, Site
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup

_CRYSTAL = [SpaceGroup, Cell, Atoms]


class CrystalCif:
    def __init__(self, name: str, *args):
        self.name = name
        self._items: list = list(args)
        self.blocks = self._create_cif_obj()

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items
        self.blocks = self._create_cif_obj()

    def _create_cif_obj(self):
        blocks = [StarHeader(self.name)]
        for idx, entry_item in enumerate(self._items):
            in_there = [isinstance(entry_item, c) for c in _CRYSTAL]
            if not any(in_there):
                raise AttributeError
            blocks.append(self.items[idx].to_star())
        return StarCollection(*blocks)

    def __str__(self) -> str:
        out_str = str(self.blocks)
        out_str += '\n_eof'
        return out_str

    @classmethod
    def from_cif_str(cls, in_str: str):
        star_items = StarCollection.from_string(in_str)
        header = [item for item in star_items if isinstance(item, StarHeader)]
        header = header[0].name
        entry_dict = {item.name: item for item in star_items if isinstance(item, StarEntry)}
        entry_name_set = set(entry_dict.keys())
        if SpaceGroup._CIF_CONVERSIONS[0][1] in entry_name_set:
            space_group = entry_dict[SpaceGroup._CIF_CONVERSIONS[0][1]].to_class(SpaceGroup,
                                                                         name_conversion=SpaceGroup._CIF_CONVERSIONS[0][0])
        else:
            raise AttributeError
        cell_cif_names = set([item[1] for item in Cell._CIF_CONVERSIONS])
        if entry_name_set.issuperset(cell_cif_names):
            cell_star = StarSection.from_StarEntries([entry_dict[key] for key in cell_cif_names], [name[0] for name in Cell._CIF_CONVERSIONS])
            cell = cell_star.to_class(Cell, Cell._CIF_CONVERSIONS)
        else:
            raise AttributeError
        atom_cif_names = set([item[1] for item in Site._CIF_CONVERSIONS])
        loops = [item for item in star_items if isinstance(item, StarLoop)]
        found = False
        for loop in loops:
            if set(loop.labels).issuperset(atom_cif_names):
                found = True
                atoms = loop.to_class(Atoms, Site, Site._CIF_CONVERSIONS)
                break
        if not found:
            raise AttributeError
        return cls(header, space_group, cell, atoms)
