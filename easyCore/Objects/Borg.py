__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Union, List, Callable

from easyCore.Objects.Graph import Graph
from easyCore.Fitting import engines
from easyCore.Utils.classUtils import singleton

@singleton
class Borg:
    __log = []
    __map = Graph()
    __stack = None
    __debug = False

    def __init__(self):
        self.log = self.__log
        self.debug = self.__debug
        self.stack = self.__stack
        self.map = self.__map
        self._fitting = engines
        self._current_fitting_engine = self._fitting[0]

    @property
    def fitting_engines(self) -> List[str]:
        if self._fitting is None:
            print('Fitting not instantiated yet')
            raise ImportError
        return [engine.name for engine in self._fitting]

    @property
    def fitting_engine(self) -> Callable:
        return self._current_fitting_engine

    @fitting_engine.setter
    def fitting_engine(self, value: Union[str, int]):
        if isinstance(value, int):
            if value < len(self._fitting):
                value = self._fitting[value]
            else:
                raise ValueError
        engine_list = self.fitting_engines
        if value in engine_list:
            self._current_fitting_engine = self._fitting[engine_list.index(value)]
        else:
            raise ValueError

    def instantiate_stack(self):
        from easyCore.Utils.UndoRedo import UndoStack
        self.stack = UndoStack()