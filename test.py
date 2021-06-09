__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from easyCore.Elements.HigherLevel.Phase import Phase
from easyCore.Symmetry.Bonding import generate_bonds

p = Phase('test')
p.cell.length_c = 4
p.spacegroup.space_group_HM_name = 'P 6'
p.add_atom('Al', 'Al', 1, 0.5, 0, 0)
p.add_atom('Cl', 'Cl', 1, 0, 0, 0)

b = generate_bonds(p, max_distance=4)
