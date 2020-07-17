__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Union, List, Callable

from easyCore.Objects.Graph import Graph
from easyCore.Fitting import engines
from easyCore.Utils.classUtils import singleton


@singleton
class Borg:
    """
    Borg is the assimilated knowledge of `easyCore`. Every class based on `easyCore` gets brought
    into the collective.
    """
    __log = []
    __map = Graph()
    __stack = None
    __debug = False

    def __init__(self):
        # Logger. This is so there's a unified logging interface
        self.log = self.__log
        # Debug. Global debugging level
        self.debug = self.__debug
        # Stack. This is where the undo/redo operations are stored.
        self.stack = self.__stack
        # Map. This is the conduit database between all borg species
        self.map = self.__map
        # Fitting. These are the available fitting engines
        self._fitting = engines
        self._current_fitting_engine = self._fitting[0]

    @property
    def fitting_engines(self) -> List[str]:
        """
        Get a list of the names of available fitting engines
        :return: List of available fitting engines
        :rtype: List[str]
        """
        if self._fitting is None:
            print('Fitting not instantiated yet')
            raise ImportError
        return [engine.name for engine in self._fitting]

    @property
    def fitting_engine(self) -> Callable:
        """
        Get the constructor to the current fitting engine
        :return: class constructor for a fitting engine
        :rtype: Callable
        """
        return self._current_fitting_engine

    @fitting_engine.setter
    def fitting_engine(self, engine_name: Union[str, int]):
        """
        Set the current fitting engine
        :param engine_name: Name of the fitting engine to be initialised
        :type engine_name: str
        :return: None
        :rtype: noneType
        """
        if isinstance(engine_name, int):
            if engine_name < len(self._fitting):
                engine_name = self._fitting[engine_name]
            else:
                raise ValueError
        engine_list = self.fitting_engines
        if engine_name in engine_list:
            self._current_fitting_engine = self._fitting[engine_list.index(engine_name)]
        else:
            raise ValueError

    def instantiate_stack(self):
        """
        The undo/redo stack references the collective. Hence it has to be imported
        after initialization.
        :return: None
        :rtype: noneType
        """
        from easyCore.Utils.UndoRedo import UndoStack
        self.stack = UndoStack()
