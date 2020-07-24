__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import json
from typing import Callable, List, TypeVar
from easyCore.Utils.json import MSONable

import numpy as np

from easyCore import borg
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Objects.Inferface import InterfaceFactoryTemplate
from easyCore.Fitting.Fitting import Fitter

from abc import ABCMeta, abstractmethod


# This is a much more complex case where we have calculators, interfaces, interface factory and an
# inherited object (from `BaseObj`). In this case the Line class is available with/without an interface
# With an interface it connects to one of the calculator interfaces. This calculator interface then translates
# interface commands to calculator specific commands


class Calculator1:
    """
    Generic calculator in the style of crysPy
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

    def calculate(self, x_array: np.ndarray) -> np.ndarray:
        """
        For a given x calculate the corresponding y

        :param x_array: array of data points to be calculated
        :type x_array: np.ndarray
        :return: points calculated at `x`
        :rtype: np.ndarray
        """
        return self.m * x_array + self.c


class Calculator2:
    """
    Isolated calculator. This calculator can't have values set, it can
    only load/save data and calculate from it. i.e in the style of crysfml
    """
    def __init__(self):
        """
        """
        self._data = {'m': 0,
                      'c': 0}

    def calculate(self, x_array: np.ndarray) -> np.ndarray:
        """
        For a given x calculate the corresponding y

        :param x_array: array of data points to be calculated
        :type x_array: np.ndarray
        :return: points calculated at `x`
        :rtype: np.ndarray
        """
        return self._data['m'] * x_array + self._data['c']

    def export_data(self) -> str:
        return json.dumps(self._data)

    def import_data(self, input_str: str):
        self._data = json.loads(input_str)


class InterfaceTemplate(MSONable, metaclass=ABCMeta):
    """
    This class is a template and defines all properties that an interface should have.
    """
    _interfaces = []
    _borg = borg

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
    def fit_func(self, x_array: np.ndarray) -> np.ndarray:
        """
        Function to perform a fit

        :param x_array: points to be calculated at
        :type x_array: np.ndarray
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
        if self._borg.debug:
            print(f'Interface1: Value of {value_label} set to {value}')
        setattr(self.calculator, value_label, value)

    def fit_func(self, x_array: np.ndarray) -> np.ndarray:
        """
        Function to perform a fit

        :param x_array: points to be calculated at
        :type x_array: np.ndarray
        :return: calculated points
        :rtype: np.ndarray
        """
        return self.calculator.calculate(x_array)


class Interface2(InterfaceTemplate):
    """
    This is a more complex template. Here we need to export_data data,
    transfer it to the calculator (get and calculate) and import data
    from the calculator (set)
    """
    def __init__(self):
        """
        Set up a calculator and a local dict
        """
        self.calculator = Calculator2()
        self._data: dict = {}

    def get_value(self, value_label: str) -> float:
        """
        Method to get a value from the calculator

        :param value_label: parameter name to get
        :type value_label: str
        :return: associated value
        :rtype: float
        """
        self._data = json.loads(self.calculator.export_data())
        return getattr(self._data, value_label, None)

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
        if self._borg.debug:
            print(f'Interface2: Value of {value_label} set to {value}')
        self._data = json.loads(self.calculator.export_data())
        if value_label in self._data.keys():
            self._data[value_label] = value
        self.calculator.import_data(json.dumps(self._data))

    def fit_func(self, x_array: np.ndarray) -> np.ndarray:
        """
        Function to perform a fit

        :param x_array: points to be calculated at
        :type x_array: np.ndarray
        :return: calculated points
        :rtype: np.ndarray
        """
        return self.calculator.calculate(x_array)


class InterfaceFactory(InterfaceFactoryTemplate):
    def __init__(self):
        super(InterfaceFactory, self).__init__(InterfaceTemplate._interfaces)


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
        self._set_interface()

    def _set_interface(self):
        if self.interface:
            # If an interface is given, generate bindings
            for parameter in self.get_parameters():
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
f = Fitter(line, interface.fit_func)

# y = 2x -1
x = np.array([1, 2, 3])
y = 2*x - 1

f_res = f.fit(x, y)

print('\n######### Interface 1 #########\n')
print(f_res)
print(line)

# Now lets change fitting engine
f.switch_engine('bumps')
# Reset the values so we don't cheat
line.m = 1
line.c = 0
f_res = f.fit(x, y, weights=0.1*np.ones_like(x))
print('\n######### bumps fitting #########\n')
print(f_res)
print(line)


