__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import warnings
imported = -1
try:
    from easyCore.Fitting.lmfit import lmfit  # noqa: F401
    imported += 1
except ImportError:
    # TODO make this a proper message (use logging?)
    warnings.warn('lmfit has not been installed.', ImportWarning, stacklevel=2)
try:
    from easyCore.Fitting.bumps import bumps  # noqa: F401
    imported += 1
except ImportError:
    # TODO make this a proper message (use logging?)
    warnings.warn('bumps has not been installed.', ImportWarning, stacklevel=2)

from easyCore.Fitting.fitting_template import FittingTemplate

engines: list = FittingTemplate._engines

