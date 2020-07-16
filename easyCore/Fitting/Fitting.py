__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from typing import Union, Callable, List
from functools import wraps
from easyCore import borg


class Fitter:
    _borg = borg

    def __init__(self):
        pass

    @property
    def fitting_engines(self) -> List[str]:
        return self._borg.fitting_engines

    @staticmethod
    def fitting_engine(*args, **kwargs):
        engine = borg.fitting_engine
        # TODO wrap `engine.fit` with the undo/redo bulk operations flag
        # fit_fun = engine.fit
        # def new_fit_fun(*args, **kwargs):
        #     return fu
        # engine.
        return engine(*args, **kwargs)

    def set_fitting_engine(self, value: Union[str, int]):
        self._borg.fitting_engine = value
