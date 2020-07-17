__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Callable, List
from monty.json import MSONable

import numpy as np
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import Fitter

from abc import ABCMeta, abstractmethod


# This is a much more complex case where we have calculators, interfaces, interface factory and an
# inherited object (from `BaseObj`). In this case the Line class is available with/without an interface
# With an interface it connects to one of the calculator interfaces. This calculator interface then translates
# interface commands to calculator specific commands


class Calculator1:
    """
    Generic calculator
    """
    def __init__(self, m: float = 1, c: float = 0):
        """
        Create a calculator object with m and c
        :param m: gradient
        :type m: float
        :param c: intercept
        :type c: float
        """
        self.m = m
        self.c = c

    def calculate(self, x: np.ndarray) -> np.ndarray:
        """
        For a given x calculate the corresponding y
        :param x: array of data points to be calculated
        :type x: np.ndarray
        :return: points calculated at `x`
        :rtype: np.ndarray
        """
        return self.m * x + self.c


class InterfaceTemplate(MSONable, metaclass=ABCMeta):
    """
    This class is a template and defines all properties that an interface should have.
    """
    _interfaces = []

    def __init_subclass__(cls, is_abstract: bool = False, **kwargs):
        """
        Initialise all subclasses so that they can be created in the factory
        :param is_abstract: Is this a subclass which shouldn't be dded
        :type is_abstract: bool
        :param kwargs: key word arguments
        :type kwargs: dict
        :return: None
        :rtype: noneType
        """
        super().__init_subclass__(**kwargs)
        if not is_abstract:
            cls._interfaces.append(cls)

    @abstractmethod
    def get_value(self, value_label: str) -> float:
        """
        Method to get a value from the calculator
        :param value_label: parameter name to get
        :type value_label: str
        :return: associated value
        :rtype: float
        """
        pass

    @abstractmethod
    def set_value(self, value_label: str, value: float):
        """
        Method to set a value from the calculator
        :param value_label: parameter name to get
        :type value_label: str
        :param value: new numeric value
        :type value: float
        :return: None
        :rtype: noneType
        """
        pass

    @abstractmethod
    def fit_func(self, x: np.ndarray) -> np.ndarray:
        """
        Function to perform a fit
        :param x: points to be calculated at
        :type x: np.ndarray
        :return: calculated points
        :rtype: np.ndarray
        """
        pass


class Interface1(InterfaceTemplate):
    """
    A simple example interface using Calculator1
    """
    def __init__(self):
        # This interface will use calculator1
        self.calculator = Calculator1()

    def get_value(self, value_label: str) -> float:
        """
        Method to get a value from the calculator
        :param value_label: parameter name to get
        :type value_label: str
        :return: associated value
        :rtype: float
        """
        return getattr(self.calculator, value_label, None)

    def set_value(self, value_label: str, value: float):
        """
        Method to set a value from the calculator
        :param value_label: parameter name to get
        :type value_label: str
        :param value: new numeric value
        :type value: float
        :return: None
        :rtype: noneType
        """
        print(f'Interface1: Value of {value_label} set to {value}')
        setattr(self.calculator, value_label, value)

    def fit_func(self, x: np.ndarray) -> np.ndarray:
        """
        Function to perform a fit
        :param x: points to be calculated at
        :type x: np.ndarray
        :return: calculated points
        :rtype: np.ndarray
        """
        return self.calculator.calculate(x)


class Interface2(InterfaceTemplate):
    def __init__(self):
        self.calculator = Calculator1()

    def get_value(self, value_label: str) -> float:
        """
        Method to get a value from the calculator
        :param value_label: parameter name to get
        :type value_label: str
        :return: associated value
        :rtype: float
        """
        return getattr(self.calculator, value_label, None)

    def set_value(self, value_label: str, value: float):
        """
        Method to set a value from the calculator
        :param value_label: parameter name to get
        :type value_label: str
        :param value: new numeric value
        :type value: float
        :return: None
        :rtype: noneType
        """
        print(f'Interface2: Value of {value_label} set to {value}')
        setattr(self.calculator, value_label, value)

    def fit_func(self, x: np.ndarray) -> np.ndarray:
        """
        Function to perform a fit
        :param x: points to be calculated at
        :type x: np.ndarray
        :return: calculated points
        :rtype: np.ndarray
        """
        return self.calculator.calculate(x)


class InterfaceFactory:
    """
    This class allows for the creation and transference of interfaces.
    """
    def __init__(self):
        self._interfaces: List[InterfaceTemplate] = InterfaceTemplate._interfaces
        self._current_interface = None
        self.__interface_obj = None
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
        self.__interface_obj = self.current_interface()

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
            new_interface_class: InterfaceTemplate = self._interfaces[interfaces.index(new_interface)]
            self.__interface_obj = new_interface_class.from_dict(serialized)
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
    def current_interface(self):
        """
        Returns the constructor for the currently selected interface
        :return: Interface constructor
        :rtype: InterfaceTemplate
        """
        return self._current_interface

    def fit_func(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        """
        Pass through to the underlying interfaces fitting function.
        :param x: points to be calculated at
        :type x: np.ndarray
        :param args: positional arguments for the fitting function
        :type args: Any
        :param kwargs: key/value pair arguments for the fitting function.
        :type kwargs: Any
        :return: points calculated at positional values `x`
        :rtype: np.ndarray
        """
        return self.__interface_obj.fit_func(x, *args, **kwargs)

    def generate_bindings(self, name):
        """
        Automatically bind a `Parameter` to the corresponding interface.
        :param name: parameter name
        :type name: str
        :return: binding property
        :rtype: property
        """
        return property(self.__get_item(name), self.__set_item(self, name))

    def __call__(self, *args, **kwargs) -> InterfaceTemplate:
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

        :param obj: object to be created from
        :type obj: InterfaceTemplate
        :param key: name of parameter to be set
        :type key: str
        :return: function to set key
        :rtype: Callable
        """
        def inner(value):
            obj().set_value(key, value)
        return inner


class Line(BaseObj):
    """
    Simple descriptor of a line.
    """
    _defaults = [Parameter('m', 1),
                 Parameter('c', 0)]

    def __init__(self, interface_factory: InterfaceFactory = None):
        """
        Create a line and add an interface if requested
        :param interface_factory: interface controller object
        :type interface_factory: InterfaceFactory
        """
        self.interface = interface_factory
        super().__init__(self.__class__.__name__,
                         *self._defaults)

        if self.interface:
            # If an interface is given, generate bindings
            for parameter in self.get_fittables():
                name = parameter.name
                self.set_binding(name, self.interface.generate_bindings)

    @property
    def gradient(self):
        if self.interface:
            return self.interface().get_value('m')
        else:
            return self.m.raw_value

    @property
    def intercept(self):
        if self.interface:
            return self.interface().get_value('c')
        else:
            return self.c.raw_value

    def __repr__(self):
        return f'Line: m={self.m}, c={self.c}'


interface = InterfaceFactory()
line = Line(interface_factory=interface)
f = Fitter.fitting_engine(line, interface.fit_func)

x = np.array([1, 2, 3])
y = np.array([2, 4, 6]) - 1

f_res = f.fit(x, y)

print(f_res.fit_report())
print(line)

# This gets the interface name `'Interface2'`
other_interface = interface.available_interfaces[1]
# Switch over the interfaces
line.interface.switch(other_interface)
f_res = f.fit(x, y)

print(f_res.fit_report())
print(line)