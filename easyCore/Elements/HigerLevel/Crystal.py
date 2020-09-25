__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Site, Atoms
class crystal:

    def __init__(self, name):
        self.name = name
        self.cell = Cell.default()
        self.atoms = Atoms('atom_list')

    def add_atom(self, *args, **kwargs):
        self.atoms.append(Site.from_pars(*args, **kwargs))


