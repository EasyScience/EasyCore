__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Objects.Graph import Graph
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

    def instantiate_stack(self):
        from easyCore.Utils.UndoRedo import UndoStack
        self.stack = UndoStack()
