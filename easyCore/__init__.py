__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Objects.Borg import Borg
from pint import UnitRegistry

default_fitting_engine = 'lmfit'


ureg = UnitRegistry()
borg = Borg()
borg.instantiate_stack()
borg.stack.enabled = True

