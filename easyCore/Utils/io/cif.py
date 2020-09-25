__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Utils.io.star import StarLoop, StarSection, StarEntry, StarBase
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Atoms
# from easyCore.Elements.Basic.SpaceGroup import

_CRYSTAL = [Cell.__class__, Atoms.__class__]

class CrystalCif:
    def __init__(self, name: str, *args):
        self.name = name
        self._items: list = args
        self.obj = self._create_cif_obj()

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items
        self.obj = self._create_cif_obj()

    def _create_cif_obj(self):
        given_classes =[item.__class__ for item in self.items]
        blocks = [StarBase(self.name)]
        for idx, entry_item in enumerate(given_classes):
            if entry_item not in _CRYSTAL:
                raise AttributeError
            blocks.append(self.items[idx].to_star())
        return blocks

    def __str__(self) -> str:
        if len(self.obj) > 0
            out_str = str(self.obj[0]) + '\n\n'
        else:
            raise IndexError
        for item in self.obj[1:]:
            out_str += str(item) + '\n'

        out_str += '_eof'
        return out_str