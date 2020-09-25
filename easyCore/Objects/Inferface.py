__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'


from abc import ABCMeta, abstractmethod
from typing import TypeVar, List

from easyCore import np


_C = TypeVar("_C", bound=ABCMeta)
_M = TypeVar("_M")


class InterfaceFactoryTemplate:
    """
    This class allows for the creation and transference of interfaces.
    """

    def __init__(self, interface_list: List[_C]):
        self._interfaces: List[_C] = interface_list
        self._current_interface: _C
        self.__interface_obj: _M = None
        self.create()

    def create(self, interface_name: str = None):
        """
        Create an interface to a calculator from those initialized. Interfaces can be selected
        by `interface_name` where `interface_name` is one of `obj.available_interfaces`. This
        interface can now be accessed by obj().

        :param interface_name: name of interface to be created
        :type interface_name: str
        :return: None
        :rtype: noneType
        """
        if interface_name is None:
            if len(self._interfaces) > 0:
                # Fallback name
                interface_name = self.return_name(self._interfaces[0])
            else:
                raise NotImplementedError

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
        return [self.return_name(this_interface) for this_interface in self._interfaces]

    @property
    def current_interface(self) -> _C:
        """
        Returns the constructor for the currently selected interface.

        :return: Interface constructor
        :rtype: InterfaceTemplate
        """
        return self._current_interface

    @property
    def current_interface_name(self) -> str:
        """
        Returns the constructor name for the currently selected interface.

        :return: Interface constructor name
        :rtype: str
        """
        return self.return_name(self._current_interface)

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
        def outer_fit_func(obj):
            def inner_fit_func(x_array, *args, **kwargs):
                return obj.__interface_obj.fit_func(x_array, *args, **kwargs)
            return inner_fit_func
        return outer_fit_func(self)(x_array, *args, **kwargs)

    def generate_bindings(self, model):
        """
        Automatically bind a `Parameter` to the corresponding interface.
        :param name: parameter name
        :type name: str
        :return: binding property
        :rtype: property
        """
        props = model.get_parameters()
        for prop in props:
            prop._callback = self.generate_binding(prop.name)
            prop._callback.fset(prop.raw_value)

    @abstractmethod
    def generate_binding(self, name, *args, **kwargs) -> property:
        """
        Automatically bind a `Parameter` to the corresponding interface.

        :param name: parameter name
        :type name: str
        :return: binding property
        :rtype: property
        """
        pass

    def __call__(self, *args, **kwargs) -> _M:
        return self.__interface_obj

    @staticmethod
    def return_name(this_interface) -> str:
        """
        Return an interfaces name
        """
        interface_name = this_interface.__name__
        if hasattr(this_interface, 'name'):
            interface_name = getattr(this_interface, 'name')
        return interface_name
