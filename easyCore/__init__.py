__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Objects.Borg import Borg
from pint import UnitRegistry

ureg = UnitRegistry()
borg = Borg()
borg.instantiate_stack()