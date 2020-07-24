__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import TypeVar, List, Callable
import numpy as np

_T = TypeVar("_T")
_M = TypeVar("_M")


class InterfaceFactoryTemplate:
    """
    This class allows for the creation and transference of interfaces.
    """

    def __init__(self, interface_list: List[_T]):
        self._interfaces: List[_T] = interface_list
        self._current_interface: _T = None
        self.__interface_obj: _M = None
        self.create()

    def create(self, interface_name: str = None):
        """
        Create an interface to a calculator from those initialized. Interfaces can be selected
        by `interface_name` where `interface_name` is one of `obj.available_interfaces`. This
        interface can now be accessed by obj()

        :param interface_name: name of interface to be created
        :type interface_name: str
        :return: None
        :rtype: noneType
        """
        if interface_name is None:
            interface_name = self._interfaces[0].__name__

        interfaces = self.available_interfaces
        if interface_name in interfaces:
            self._current_interface = self._interfaces[interfaces.index(interface_name)]
        self.__interface_obj = self._current_interface()

    def switch(self, new_interface: str):
        """
        Changes the current interface to a new interface. The current interface is destroyed and
        all MSONable parameters carried over to the new interface. i.e. pick up where you left off.

        :param new_interface: name of new interface to be created
        :type new_interface: str
        :return: None
        :rtype: noneType
        """
        serialized = self.__interface_obj.as_dict()
        interfaces = self.available_interfaces
        if new_interface in interfaces:
            self._current_interface = self._interfaces[interfaces.index(new_interface)]
            self.__interface_obj = self._current_interface.from_dict(serialized)
        else:
            raise AttributeError

    @property
    def available_interfaces(self) -> List[str]:
        """
        Return all available interfaces.

        :return: List of available interface names
        :rtype: List[str]
        """
        return [this_interface.__name__ for this_interface in self._interfaces]

    @property
    def current_interface(self) -> _T:
        """
        Returns the constructor for the currently selected interface

        :return: Interface constructor
        :rtype: InterfaceTemplate
        """
        return self._current_interface

    def fit_func(self, x_array: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        Pass through to the underlying interfaces fitting function.

        :param x_array: points to be calculated at
        :type x_array: np.ndarray
        :param args: positional arguments for the fitting function
        :type args: Any
        :param kwargs: key/value pair arguments for the fitting function.
        :type kwargs: Any
        :return: points calculated at positional values `x`
        :rtype: np.ndarray
        """
        return self.__interface_obj.fit_func(x_array, *args, **kwargs)

    def generate_bindings(self, name) -> property:
        """
        Automatically bind a `Parameter` to the corresponding interface.

        :param name: parameter name
        :type name: str
        :return: binding property
        :rtype: property
        """
        return property(self.__get_item(name), self.__set_item(self, name))

    def __call__(self, *args, **kwargs) -> _M:
        return self.__interface_obj

    @staticmethod
    def __get_item(key: str) -> Callable:
        """
        Access the value of a key by a callable object

        :param key: name of parameter to be retrieved
        :type key: str
        :return: function to get key
        :rtype: Callable
        """
        def inner(obj):
            obj().get_value(key)
        return lambda obj: inner(obj)

    @staticmethod
    def __set_item(obj, key):
        """
        Set the value of a key by a callable object

        :param obj: object to be created from
        :type obj: InterfaceFactory
        :param key: name of parameter to be set
        :type key: str
        :return: function to set key
        :rtype: Callable
        """
        def inner(value):
            obj().set_value(key, value)
        return inner