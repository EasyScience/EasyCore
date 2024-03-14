#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from easyCore.Objects.Graph import Graph
from easyCore.Utils.classUtils import singleton
from easyCore.Utils.Hugger.Hugger import ScriptManager
from easyCore.Utils.Logging import Logger


@singleton
class Borg:
    """
    Borg is the assimilated knowledge of `easyCore`. Every class based on `easyCore` gets brought
    into the collective.
    """

    __log = Logger()
    __map = Graph()
    __stack = None
    __debug = False

    def __init__(self):
        # Logger. This is so there's a unified logging interface
        self.log: Logger = self.__log
        # Debug. Global debugging level
        self.debug: bool = self.__debug
        # Stack. This is where the undo/redo operations are stored.
        self.stack = self.__stack
        #
        self.script: ScriptManager = ScriptManager()
        # Map. This is the conduit database between all borg species
        self.map: Graph = self.__map

    def instantiate_stack(self):
        """
        The undo/redo stack references the collective. Hence it has to be imported
        after initialization.

        :return: None
        :rtype: noneType
        """
        from easyCore.Utils.UndoRedo import UndoStack

        self.stack = UndoStack()
