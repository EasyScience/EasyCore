__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

try:
    from easyCore.Fitting.lmfit import lmfit  # noqa: F401
except ImportError:
    # TODO make this a proper message (use logging?)
    print('lm fit is not installed')
try:
    from easyCore.Fitting.bumps import bumps  # noqa: F401
except ImportError:
    # TODO make this a proper message (use logging?)
    print('bumps is not installed')

from easyCore.Fitting.fitting_template import FittingTemplate

engines = FittingTemplate._engines

