__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'


#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from abc import ABCMeta, abstractmethod
from typing import TypeVar, List, NamedTuple, Callable

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

    @property
    def fit_func(self) -> Callable: # , x_array: np.ndarray, *args, **kwargs) -> np.ndarray:
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
        # """
        return self.__interface_obj.fit_func

    def generate_bindings(self, model, *args, ifun=None, **kwargs):
        """
        Automatically bind a `Parameter` to the corresponding interface.
        :param name: parameter name
        :type name: str
        :return: binding property
        :rtype: property
        """
        class_links = self.__interface_obj.create(model)
        props = model._get_linkable_attributes()
        props_names = [prop.name for prop in props]
        for item in class_links:
            for item_key in item.name_conversion.keys():
                if item_key not in props_names:
                    continue
                idx = props_names.index(item_key)
                prop = props[idx]
                prop._callback = item.make_prop(item_key)
                prop._callback.fset(prop.raw_value)

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


class ItemContainer(NamedTuple):
    link_name: str
    name_conversion: dict
    getter_fn: Callable
    setter_fn: Callable

    def make_prop(self, parameter_name) -> property:
        return property(fget=self.__make_getter(parameter_name),
                        fset=self.__make_setter(parameter_name))

    def convert_key(self, lookup_key: str) -> str:
        key = self.name_conversion.get(lookup_key, None)
        return key

    def __make_getter(self, get_name: str) -> Callable:
        def get_value():
            inner_key = self.name_conversion.get(get_name, None)
            return self.getter_fn(self.link_name, inner_key)
        return get_value

    def __make_setter(self, get_name: str) -> Callable:
        def set_value(value):
            inner_key = self.name_conversion.get(get_name, None)
            self.setter_fn(self.link_name, **{inner_key: value})
        return set_value
