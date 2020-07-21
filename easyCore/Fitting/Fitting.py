__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from typing import Union, List
from easyCore import borg


class Fitter:
    """
    Wrapper to the fitting engines
    """
    _borg = borg

    @property
    def fitting_engines(self) -> List[str]:
        """
        Get a list of the names of available fitting engines
        :return: List of available fitting engines
        :rtype: List[str]
        """
        return self._borg.fitting_engines

    @staticmethod
    def fitting_engine(*args, **kwargs):
        """
        Initialize the current fitting engine.
        :param args: positional arguments for initializing the engine
        :param kwargs: keyword/value pairs for initializing the engine
        :return: Initialized fitting engine
        """
        engine = borg.fitting_engine
        # TODO wrap `engine.fit` with the undo/redo bulk operations flag
        # fit_fun = engine.fit
        # def new_fit_fun(*args, **kwargs):
        #     return fu
        # engine.
        return engine(*args, **kwargs)

    @staticmethod
    def set_fitting_engine(engine_name: Union[str, int]):
        """
        Set the current fitting engine
        :param engine_name: Name of the fitting engine to be initialised
        :type engine_name: str
        :return: None
        :rtype: noneType
        """
        borg.fitting_engine = engine_name
