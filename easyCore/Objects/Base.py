__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from copy import deepcopy
from typing import List, Union
from functools import cached_property

from easyCore import borg, ureg
from easyCore.Utils.typing import noneType
from easyCore.Utils.UndoRedo import stack_deco

import numpy as np
from monty.json import MSONable
from lmfit import Parameter as lmfitPar

Q_ = ureg.Quantity
M_ = ureg.Measurement


class Descriptor:
    _storer = Q_

    def __init__(self, name: str, value, *args, unit=None, description: str = '',
                 url: str = '', callback: property = None, parent=None):
        self.__borg = borg
        self.__borg.map.add_vertex(id(self))
        self._parent = parent
        if self._parent is not None:
            self.__borg.map.add_edge({id(self._parent), id(self)})
        self.name: str = name
        self._unit = ureg.parse_expression(unit)

        self._val = self.__class__._storer(value, *args, self._unit)
        self.description: str = description
        self._display_name: str = ''
        self.url: str = url
        self._callback: property = callback
        self.user_data: dict = {}
        self._type = type(value)
        self._args = args

    # This should not
    @property
    def display_name(self) -> str:
        display_name = self._display_name
        if display_name is None:
            display_name = self.name
        return display_name

    @display_name.setter
    @stack_deco
    def display_name(self, name_str):
        self._display_name = name_str

    @property
    def unit(self):
        # Should implement the undo/redo functionality
        return self._unit.units

    @unit.setter
    @stack_deco
    def unit(self, unit_str: str):
        new_unit = ureg.parse_expression(unit_str)
        self._unit = new_unit
        self._val = self.__class__._storer(self.raw_value, *self._args, self._unit)

    @property
    def value(self):
        # Cached property? Should reference callback.
        # Also should reference for undo/redo
        return self._val

    @value.setter
    @stack_deco
    def value(self, value):
        # There should be a callback to the base module which has a Borg, with
        # if self._parent is not None and hasattr(self._parent, '_history'):
        #     self._parent._history[self._parent.__hash__()].append(self, 'value_change', value)
        # Cached property?
        if hasattr(value, 'magnitude'):
            value = value.magnitude.nominal_value
        self._val = self.__class__._storer(value, *self._args, self._unit)

    @property
    def raw_value(self):
        return self._val.magnitude.nominal_value

    def _validator(self, value):
        assert isinstance(value, self._type)

    def convert_unit(self, unit_str: str):
        new_unit = ureg.parse_expression(unit_str)
        self._val = self._val.to(new_unit)

    @cached_property
    def compatible_units(self) -> List[str]:
        return [str(u) for u in self.unit.compatible_units()]

    def __del__(self):
        # Remove oneself from the map
        # self.__borg.map.remove_vertice(id(self))
        pass

    def __repr__(self):
        """Return printable representation of a Parameter object."""
        sval = "value=%s" % self._val.magnitude
        if self.value.unitless:
            sval += ' %s' % self._val.units
        return "<%s '%s', %s>" % (self.__class__.__name__, self.name, sval)


class Parameter(Descriptor):
    _storer = M_

    def __init__(self, name:str, value: Union[float, np.ndarray, noneType], error: Union[float, np.ndarray, noneType]=None, **kwargs):
        super().__init__(name, value, error, **kwargs)
        self._min: float = -np.Inf
        self._max: float = np.Inf
        self._fixed: bool = False
        self.initial_value = self.value
        self.constraints: dict = {
            'user': [],
            'physical': [],
            'builtin': [Constraint(lambda x: x < self.min, self.min),
                        Constraint(lambda x: x > self.max, self.max)]
        }
        self.__previous_set = self.__class__.value.fset
        self.__previous_unit = self.__class__.unit

        setattr(self.__class__, 'unit', property(fget=self.__class__.unit.fget,
                                                 fset=lambda obj, value: obj.__unit_setter(value),
                                                 fdel=self.__class__.unit.fdel))

        setattr(self.__class__, 'value', property(fget=self.__class__.value.fget,
                                                  fset=lambda obj, val: self.__previous_set(obj, obj._validate(val)),
                                                  fdel=self.__class__.value.fdel))

    def __unit_setter(self, value_str: str):
        old_unit = deepcopy(self._unit)
        # Deal with min/max
        if self.value.unitless:
            self._min = Q_(self.min, old_unit).to(self._unit).magnitude
            self._max = Q_(self.max, old_unit).to(self._unit).magnitude
        self.__previous_unit.fset(self, value_str)

    @property
    def min(self) -> float:
        # Should implement the undo/redo functionality
        return self._min

    @min.setter
    @stack_deco
    def min(self, value: float):
        # Should implement the undo/redo functionality
        self._min = value

    @property
    def max(self) -> float:
        # Should implement the undo/redo functionality
        return self._max

    @max.setter
    @stack_deco
    def max(self, value: float):
        # Should implement the undo/redo functionality
        self._max = value

    @property
    def fixed(self) -> bool:
        # Should implement the undo/redo functionality
        return self._fixed

    @fixed.setter
    @stack_deco
    def fixed(self, value: bool):
        # Should implement the undo/redo functionality
        self._fixed = value

    @property
    def stderr(self) -> float:
        return self._val.error.magnitude

    def set_error(self, value: float):
        self._args[0] = value
        self._val.error.magnitude = value

    def for_fit(self) -> lmfitPar:
        return lmfitPar(self.name, value=self.value, vary=~self.fixed, min=self.min, max=self.max,
                        expr=None, brute_step=None, user_data=self.user_data)

    def _validate(self, value):
        new_value = value
        for constraint in self.constraints.values():
            for test in constraint:
                if test(value):
                    new_value = test.value()
        return new_value

    def __repr__(self):
        """Return printable representation of a Parameter object."""
        super_str = super().__repr__()
        super_str = super_str[:-1]
        s = []
        if self.fixed:
            super_str += " (fixed)"
        s.append(super_str)
        s.append("bounds=[%s:%s]" % (repr(self.min), repr(self.max)))
        return "%s>" % ', '.join(s)


class Constraint:
    def __init__(self, validator, fail_value):
        self._validator = validator
        self._fail_value = fail_value

    def __call__(self, *args, **kwargs):
        return self._validator(*args, **kwargs)

    def value(self):
        return self._fail_value


class BaseObj(MSONable):
    def __init__(self, **kwargs):
        self._borg = borg

    def _instantiate(self, json: str):
        pass

    def sub_fittables(self) -> List[Parameter]:
        vals = []
        for key, item in self.__dict__.items():
            if hasattr(item, 'sub_fittables'):
                vals = [vals, *item.sub_fittables()]
            elif isinstance(item, Parameter) and not item.fixed:
                vals.append(item.for_fit())
        return vals
