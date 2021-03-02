__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from collections import deque
from typing import Union, Any, NoReturn, Tuple, List
import abc

from easyCore import borg


class UndoStack:
    """
    Implement a version of QUndoStack without the QT
    """

    def __init__(self, max_history: Union[int, type(None)] = None):
        self._history = deque(maxlen=max_history)
        self._future = deque(maxlen=max_history)
        self._macro_running = False
        self._macro = dict(text="", commands=[])
        self._max_history = max_history

    @property
    def history(self) -> deque:
        return self._history

    def push(self, command) -> NoReturn:
        """
        Add a command to the history stack
        """
        if self._macro_running:
            self._macro['commands'].append(command)
        else:
            self._history.appendleft(command)
        command.redo()
        self._future = deque(maxlen=self._max_history)

    def pop(self):
        """
        Sometimes you really don't want the last command. Remove it from the stack
        !! WARNING: TO BE USED WITH UTTER CAUTION !!

        :return: None
        :rtype: None
        """
        if self._macro_running:
            self._macro['commands'].pop(-1)
        else:
            self._history.popleft()

    def clear(self) -> NoReturn:
        """
        Remove any commands on the stack and reset the state
        """
        self._history = deque(maxlen=self._max_history)
        self._future = deque(maxlen=self._max_history)
        self._macro_running = False
        self._macro = dict(text="", commands=[])

    def undo(self) -> NoReturn:
        """
        Undo the last change to the stack
        """
        if self.canUndo():
            command = self._history[0]
            self._future.appendleft(command)
            self._history.popleft()
            if isinstance(command, dict):
                for item in command['commands'][::-1]:
                    item.undo()
            else:
                command.undo()

    def redo(self) -> NoReturn:
        """
        Redo the last `undo` command on the stack
        """
        if len(self._future) > 0:
            command = self._future[0]
            if not self._macro_running:
                self._history.appendleft(command)
            self._future.popleft()
            if isinstance(command, dict):
                for item in command['commands']:
                    item.redo()
            else:
                command.redo()

    def beginMacro(self, text: str) -> NoReturn:
        """
        Start a bulk update i.e. multiple commands under one undo/redo command
        """
        if self._macro_running:
            raise AssertionError
        self._macro_running = True
        self._macro = dict(text=text, commands=[])

    def endMacro(self) -> NoReturn:
        """
        End a bulk update i.e. multiple commands under one undo/redo command
        """
        if not self._macro_running:
            raise AssertionError
        self._macro_running = False
        self._history.appendleft(self._macro)

    def canUndo(self) -> bool:
        """
        Can the last command be undone?
        """
        return len(self._history) > 0 and not self._macro_running

    def canRedo(self) -> bool:
        """
        Can we redo a command?
        """
        return len(self._future) > 0 and not self._macro_running

    def redoText(self) -> str:
        """
        Text associated with a redo item.
        """
        text = ''
        if self.canRedo():
            if isinstance(self._future[0], dict):
                text = self._future[0]['text']
            else:
                text = self._future[0]._text
        return text

    def undoText(self) -> str:
        """
        Text associated with a undo item.
        """
        text = ''
        if self.canUndo():
            if isinstance(self._history[0], dict):
                text = self._history[0]['text']
            else:
                text = self._history[0]._text
        return text


class UndoCommand(metaclass=abc.ABCMeta):
    """
    The Command interface pattern
    """

    def __init__(self, obj) -> None:
        self._obj = obj
        self._text = None

    @abc.abstractmethod
    def undo(self) -> NoReturn:
        """
        Undo implementation which should be overwritten
        """

    @abc.abstractmethod
    def redo(self) -> NoReturn:
        """
        Redo implementation which should be overwritten
        """

    def setText(self, text: str) -> NoReturn:
        self._text = text


# class _EmptyCommand(UndoCommand):
#     """
#     The _EmptyCommand class is the custom base class of all undoable commands
#     stored on a UndoStack.
#     """
#
#     def __init__(self, dictionary: 'UndoableDict', key: Union[str, list], value: Any):
#         super().__init__(self)
#         self._dictionary = dictionary
#         self._key = key
#         self._new_value = value
#         self._old_value = dictionary.getItem(key)
#
#
# class _AddItemCommand(_EmptyCommand):
#     """
#     The _AddItemCommand class implements a command to add a key-value pair to
#     the UndoableDict-base_dict dictionary.
#     """
#
#     def __init__(self, dictionary: 'UndoableDict', key: Union[str, list], value: Any):
#         super().__init__(dictionary, key, value)
#         self.setText("Adding: {} = {}".format(self._key, self._new_value))
#
#     def undo(self) -> NoReturn:
#         self._dictionary._realDelItem(self._key)
#
#     def redo(self) -> NoReturn:
#         self._dictionary._realAddItem(self._key, self._new_value)
#
#
# class _SetItemCommand(_EmptyCommand):
#     """
#     The _SetItemCommand class implements a command to modify the value of
#     the existing key in the UndoableDict-base_dict dictionary.
#     """
#
#     def __init__(self, dictionary: 'UndoableDict', key: Union[str, list], value: Any):
#         super().__init__(dictionary, key, value)
#         self.setText("Setting: {} = {}".format(self._key, self._new_value))
#
#     def undo(self) -> NoReturn:
#         if self._new_value is not self._old_value:
#             if self._old_value is None:
#                 self._dictionary._realDelItem(self._key)
#             else:
#                 self._dictionary._realSetItem(self._key, self._old_value)
#
#     def redo(self) -> NoReturn:
#         if self._new_value is not self._old_value:
#             self._dictionary._realSetItem(self._key, self._new_value)
#
#
# class _RemoveItemCommand(_EmptyCommand):
#     """
#     The _SetItemCommand class implements a command to modify the value of
#     the existing key in the UndoableDict-base_dict dictionary.
#     """
#
#     def __init__(self, dictionary: 'UndoableDict', key: Union[str, list]):
#         super().__init__(dictionary, key, None)
#         self.setText("Removing: {}".format(self._key))
#
#     def undo(self) -> NoReturn:
#         self._dictionary._realAddItemByPath(self._key, self._old_value)
#
#     def redo(self) -> NoReturn:
#         self._dictionary._realDelItem(self._key)


class PropertyStack(UndoCommand):
    """
    Stack operator for when a property setter is wrapped.
    """
    def __init__(self, parent, func, old_value, new_value):
        self.setText("Setting {} to {}".format(func.__name__, new_value))
        super().__init__(self)
        self._parent = parent
        self._old_value = old_value
        self._new_value = new_value
        self._set_func = func
        self.setText(f'{parent} value changed from {old_value} to {new_value}')

    def undo(self) -> NoReturn:
        self._set_func(self._parent, self._old_value)

    def redo(self) -> NoReturn:
        self._set_func(self._parent, self._new_value)


def stack_deco(func):
    """
    Decorate a `property` setter with undo/redo functionality
    :param func: function to be wrapped
    :type func: Callable
    :return: wrapped function
    :rtype: Callable
    """
    name = func.__name__

    def inner(obj, *args, **kwargs):
        old_value = getattr(obj, name)
        new_value = args[0]
        if borg.debug:
            print(f"I'm {obj} and have been set from {old_value} to {new_value}!")
        borg.stack.push(PropertyStack(obj, func, old_value, new_value))

    return inner

# def stack_macro(func):
#     def inner(obj, *args, **kwargs):
#         old_value = getattr(obj, name)
#         new_value = args[0]
#         borg.stack.push(PropertyStack(obj, func, old_value, new_value))
#     return inner
