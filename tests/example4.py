__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Callable

import numpy as np
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Fitting.Fitting import Fitter

from abc import ABCMeta, abstractmethod


# In this case we have inherited from `BaseObj` to create a class which has fitable attributes.
# This class does not know about the `Calculator`, only the interface.


class Calculator1:
    def __init__(self, m=1, c=0):
        self.m = m
        self.c = c

    def calculate(self, x):
        return self.m * x + self.c


class InterfaceTemplate(metaclass=ABCMeta):

    _interfaces = []

    def __init_subclass__(cls, is_abstract=False, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_abstract:
            cls._interfaces.append(cls)

    @abstractmethod
    def get_value(self, value_label: str):
        pass

    @abstractmethod
    def set_value(self, value_label: str, value):
        pass

    @abstractmethod
    def fit_func(self, x):
        pass


class Interface1(InterfaceTemplate):
    def __init__(self):
        self.calculator = Calculator1()

    def get_value(self, value_label: str):
        return getattr(self.calculator, value_label, None)

    def set_value(self, value_label: str, value):
        print(f'Interface1: Value of {value_label} set to {value}')
        setattr(self.calculator, value_label, value)

    def fit_func(self, x):
        return self.calculator.calculate(x)


class Interface2(InterfaceTemplate):
    def __init__(self):
        self.calculator = Calculator1()

    def get_value(self, value_label: str):
        return getattr(self.calculator, value_label, None)

    def set_value(self, value_label: str, value):
        print(f'Interface2: Value of {value_label} set to {value}')
        setattr(self.calculator, value_label, value)

    def fit_func(self, x):
        return self.calculator.calculate(x)


class Interface:
    def __init__(self):
        self._interfaces = InterfaceTemplate._interfaces
        self._current_interface = self._interfaces[0]

    @property
    def interfaces(self):
        return [interface.__name__ for interface in self._interfaces]

    @property
    def current_interface(self):
        return self._current_interface

    @current_interface.setter
    def current_interface(self, value:str):
        interfaces = self.interfaces
        if value in interfaces:
            self._current_interface = self._interfaces[interfaces.index(value)]


class Line(BaseObj):
    _defaults = [Parameter('m', 1),
                 Parameter('c', 0)]

    def __init__(self, interface=None):

        if interface:
            interface = interface.current_interface()

        self.interface = interface
        super().__init__(self.__class__.__name__,
                         *self._defaults)

        if self.interface:
            for parameter in self.get_fittables():
                name = parameter.name
                setattr(self.__dict__[name],
                        '_callback',
                        property(self.__gitem(name), self.__sitem(self, name)))

    @property
    def gradient(self):
        if self.interface:
            return self.interface.get_value('m')
        else:
            return self.m.raw_value

    @property
    def intercept(self):
        if self.interface:
            return self.interface.get_value('c')
        else:
            return self.c.raw_value

    def fit_func(self, x: np.ndarray) -> np.ndarray:
        if self.interface:
            return self.interface.fit_func(x)
        else:
            raise NotImplementedError

    def __repr__(self):
        return f'Line: m={self.m}, c={self.c}'

    @staticmethod
    def __gitem(key: str) -> Callable:
        def inner(obj):
            obj.interface.get_value(key)
        return lambda obj: inner(obj)

    @staticmethod
    def __sitem(obj, key):
        def inner(value):
            obj.interface.set_value(key, value)
        return inner


interface = Interface()
l = Line(interface=interface)
f = Fitter.fitting_engine(l, l.fit_func)

x = np.array([1, 2, 3])
y = np.array([2, 4, 6]) - 1

f_res = f.fit(x, y)

print(f_res.fit_report())
print(l)


interface.current_interface = interface.interfaces[1]
l2 = Line(interface=interface)
f = Fitter.fitting_engine(l2, l2.fit_func)

x = np.array([1, 2, 3])
y = np.array([2, 4, 6]) - 1

f_res = f.fit(x, y)

print(f_res.fit_report())
print(l2)