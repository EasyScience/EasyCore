__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numbers
import numpy as np
import weakref

from copy import deepcopy
from typing import List, Union, Any, Iterable
# from functools import cached_property

from easyCore import borg, ureg
from easyCore.Utils.classTools import addLoggedProp, addProp
from easyCore.Utils.typing import noneType
from easyCore.Utils.UndoRedo import stack_deco
from easyCore.Utils.json import MSONable

Q_ = ureg.Quantity
M_ = ureg.Measurement


class Descriptor(MSONable):
    """
    Class which is the base of all models. It contains all information to describe an objects unique property. This
    includes a value, unit, description and url (for reference material). All so implemented is a callback so that the
    value can be read from a linked library object.

    Undo/Redo functionality is implemented for value, unit, display name.
    """

    _constructor = Q_
    _borg = borg
    _args = {
        'value': None,
        'units': ''
    }

    def __init__(self, name: str,
                 value: Any,
                 units: Union[noneType, str, ureg.Unit] = None,
                 description: str = '',
                 url: str = '',
                 display_name: str = None,
                 callback: property = property(),
                 parent=None):  # noqa: S107
        """
        Class to describe a static-property. i.e Not a property which is fitable. The value and unit of this property
        can vary and the changes implement undo/redo functionality.

        Units are provided by pint: https://github.com/hgrecco/pint

        :param name: Name of this object
        :type name: str
        :param value: Value of this object
        :type value: Any
        :param units: This object can have a physical unit associated with it
        :type units: str, ureg.Unit
        :param description: A brief summary of what this object is
        :type description: str
        :param url: Lookup url for documentation/information
        :type url: str
        :param callback: The property which says how the object is linked to another one
        :type callback: parameter
        :param parent: The object which is the parent to this one
        :type parent:Any
        """
        # Let the collective know we've been assimilated
        self._borg.map.add_vertex(self, obj_type='created')
        # Make the connection between self and parent
        if parent is not None:
            self._borg.map.add_edge(parent, self)

        self.name: str = name
        # Attach units if necessary
        if isinstance(units, ureg.Unit):
            self._units = deepcopy(units)
        elif isinstance(units, (str, noneType)):
            self._units = ureg.parse_expression(units)
        else:
            raise AttributeError
        # Clunky method of keeping self.value up to date
        self._args['value'] = value
        self._args['units'] = str(self.unit)
        self._value = self.__class__._constructor(**self._args)

        self.description: str = description
        self._display_name: str = display_name
        self.url: str = url
        if callback is None:
            callback = property()
        self._callback: property = callback
        self.user_data: dict = {}
        self._type = type(value)

        finalizer = None
        if self._callback.fdel is not None:
            weakref.finalize(self, self._callback.fdel)
        self._finalizer = finalizer

    @property
    def display_name(self) -> str:
        """
        Get a pretty display name.

        :return: the pretty display name
        :rtype: str
        """
        # TODO This might be better implementing fancy f-strings where we can return html,latex, markdown etc
        display_name = self._display_name
        if display_name is None:
            display_name = self.name
        return display_name

    @display_name.setter
    @stack_deco
    def display_name(self, name_str: str):
        """
        Set the pretty display name.

        :param name_str: pretty display name
        :type name_str: str
        :return: None
        :rtype: noneType
        """
        self._display_name = name_str

    @property
    def unit(self) -> ureg.Unit:
        """
        Get the unit associated with the value.

        :return: Unit associated with self
        :rtype: ureg.Unit
        """
        return self._units.units

    @unit.setter
    @stack_deco
    def unit(self, unit_str: str):
        """
        Set the unit to a new one.

        :param unit_str:
        :type unit_str: str
        :return: None
        :rtype: noneType
        """
        if not isinstance(unit_str, str):
            unit_str = str(unit_str)
        new_unit = ureg.parse_expression(unit_str)
        self._units = new_unit
        self._args['units'] = str(new_unit)
        self._value = self.__class__._constructor(**self._args)

    @property
    def value(self):
        """
        Get the value of self as a pint. This is should be usable for most cases. If a pint
        is not acceptable then the raw value can be obtained through `obj.raw_value`.

        :return: Value of self
        :rtype: Any
        """
        # Cached property? Should reference callback.
        # Also should reference for undo/redo
        if self._callback.fget is not None:
            try:
                value = self._callback.fget()
                if value != self._value:
                    self.__deepValueSetter(value)
            except Exception as e:
                raise e
        return self._value

    def __deepValueSetter(self, value):
        """
        Set the value of self. This creates a pint with a unit.

        :param value: new value of self
        :type value: Any
        :return: None
        :rtype: noneType
        """
        # TODO there should be a callback to the collective, logging this as a return(if from a non `easyCore` class)
        if hasattr(value, 'magnitude'):
            value = value.magnitude
            if hasattr(value, 'nominal_value'):
                value = value.nominal_value
        self._args['value'] = value
        self._value = self.__class__._constructor(**self._args)

    @value.setter
    @stack_deco
    def value(self, value: Any):
        """
        Set the value of self. This creates a pint with a unit.

        :param value: new value of self
        :type value: Any
        :return: None
        :rtype: noneType
        """
        self.__deepValueSetter(value)
        if self._callback.fset is not None:
            try:
                self._callback.fset(value)
            except Exception as e:
                raise e

    @property
    def raw_value(self):
        """
        Return the raw value of self without a unit.

        :return: raw value of self
        :rtype: Any
        """
        value = self._value
        if hasattr(value, 'magnitude'):
            value = value.magnitude
            if hasattr(value, 'nominal_value'):
                value = value.nominal_value
        return value

    def _validator(self, value: Any):
        """
        Check that type is consistent. We don't want to assign a float to a string etc.

        :param value: Value to be checked
        :type value: Any
        :return: None
        :rtype: noneType
        """
        assert isinstance(value, self._type)

    def convert_unit(self, unit_str: str):
        new_unit = ureg.parse_expression(unit_str)
        self._value = self._value.to(new_unit)
        self._units = new_unit
        self._args['value'] = self.raw_value
        self._args['units'] = str(self.unit)

    # @cached_property
    @property
    def compatible_units(self) -> List[str]:
        """
        Returns all possible units for which the current unit can be converted.

        :return: Possible conversion units
        :rtype: List[str]
        """
        return [str(u) for u in self.unit.compatible_units()]

    def __repr__(self):
        """Return printable representation of a Parameter object."""
        sval = "= %s" % self._value.magnitude
        if not self.value.unitless:
            sval += ' %s' % self.unit
        return "<%s '%s' %s>" % (self.__class__.__name__, self.name, sval)

    def as_dict(self, skip: list = None) -> dict:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        :rtype: dict
        """
        if skip is None:
            skip = []
        super_dict = super().as_dict(skip=skip + ['parent', 'callback', '_finalizer'])
        super_dict['value'] = self.raw_value
        super_dict['units'] = self._args['units']
        # We'll have to serialize the callback option :face_palm:
        # keys = super_dict.keys()
        # if 'parent' in keys:
        #     del super_dict['parent']
        return super_dict

    def to_obj_type(self, data_type: Union['Descriptor', 'Parameter'], *kwargs):
        """
        Convert between a `Parameter` and a `Descriptor`.

        :param data_type: class constructor of what we want to be
        :type data_type: Callable
        :param kwargs: Additional keyword/value pairs for conversion
        :return: self as a new type
        :rtype: Callable
        """
        if issubclass(data_type, Descriptor):
            raise AttributeError
        pickled_obj = self.as_dict()
        pickled_obj.update(kwargs)
        return data_type.from_dict(pickled_obj)


class Parameter(Descriptor):
    """
    This class is an extension of a `Descriptor`. Where the descriptor was for static objects,
    a `Parameter` is for dynamic objects. A parameter has the ability to be used in fitting and
    has additional fields to facilitate this.
    """

    _constructor = M_
    _args = {
        'value': None,
        'units': '',
        'error': 0
    }

    def __init__(self,
                 name: str,
                 value: Union[numbers.Number, np.ndarray, noneType],
                 error: Union[numbers.Number, np.ndarray] = 0.,
                 min: numbers.Number = -np.Inf,
                 max: numbers.Number = np.Inf,
                 fixed: bool = False,
                 **kwargs):
        """
        Class to describe a dynamic-property which can be optimised. It inherits from `Descriptor`
        and can as such be serialised.

        :param name: Name of this object
        :type name: str
        :param value: Value of this object
        :type value: Any
        :param error: Error associated as sigma for this parameter
        :type error: float
        :param min: Minimum value for fitting
        :type min: float
        :param max: Maximum value for fitting
        :type max: float
        :param fixed: Should this parameter vary when fitting?
        :type fixed: bool
        :param kwargs: Key word arguments for the `Descriptor` class.
        """
        # Set the error
        self._args['error'] = error
        if not isinstance(value, numbers.Number):
            raise ValueError("In a parameter the `value` must be numeric")
        if value < min:
            raise ValueError("`value` can not be less than `min`")
        if value > max:
            raise ValueError("`value` can not be greater than `max`")
        if error < 0:
            raise ValueError("Standard deviation `error` must be positive")

        super().__init__(name, value, **kwargs)

        # Create additional fitting elements
        self._min: numbers.Number = min
        self._max: numbers.Number = max
        self._fixed: bool = fixed
        self.initial_value = self.value
        self.constraints: dict = {
            'user':     [],
            'physical': [],
            'builtin':  [Constraint(lambda x: x < self.min, self.min),
                         Constraint(lambda x: x > self.max, self.max)]
        }
        # This is for the serialization. Otherwise we wouldn't catch the values given to `super()`
        self._kwargs = kwargs
        # Monkey patch the unit and the value to take into account the new max/min situation
        self.__previous_set = self.__class__.value.fset
        # self.__previous_unit = self.__class__.unit

        # setattr(self.__class__, 'unit', property(fget=self.__class__.unit.fget,
        #                                          fset=lambda obj, val: obj.__unit_setter(val),
        #                                          fdel=self.__class__.unit.fdel))

        addProp(self, 'value',
                fget=self.__class__.value.fget,
                fset=lambda obj, val: self.__previous_set(obj, obj._validate(val)),
                fdel=self.__class__.value.fdel)

    def convert_unit(self, new_unit: str):  # noqa: S1144
        """
        Perform unit conversion. The value, max and min can change on unit change.

        :param value_str: new unit
        :type value_str: str
        :return: None
        :rtype: noneType
        """
        old_unit = str(self._args['units'])
        super().convert_unit(new_unit)
        # Deal with min/max. Error is auto corrected
        if not self.value.unitless and old_unit != 'dimensionless':
            self._min = Q_(self.min, old_unit).to(self._units).magnitude
            self._max = Q_(self.max, old_unit).to(self._units).magnitude
        # Log the new converted error
        self._args['error'] = self.value.error.magnitude

    @property
    def min(self) -> numbers.Number:
        """
        Get the minimum value for fitting.

        :return: minimum value
        :rtype: float
        """
        return self._min

    @min.setter
    @stack_deco
    def min(self, value: numbers.Number):
        """
        Set the minimum value for fitting.
        - implements undo/redo functionality.

        :param value: new minimum value
        :type value: float
        :return: None
        :rtype: noneType
        """
        if value <= self.raw_value:
            self._min = value
        else:
            raise ValueError

    @property
    def max(self) -> numbers.Number:
        """
        Get the maximum value for fitting.

        :return: maximum value
        :rtype: float
        """
        return self._max

    @max.setter
    @stack_deco
    def max(self, value: numbers.Number):
        """
        Get the maximum value for fitting.
        - implements undo/redo functionality.

        :param value: new maximum value
        :type value: float
        :return: None
        :rtype: noneType
        """
        if value >= self.raw_value:
            self._max = value
        else:
            raise ValueError

    @property
    def fixed(self) -> bool:
        """
        Can the parameter vary while fitting?

        :return: True = fixed, False = can vary
        :rtype: bool
        """
        return self._fixed

    @fixed.setter
    @stack_deco
    def fixed(self, value: bool):
        """
        Change the parameter vary while fitting state.
        - implements undo/redo functionality.

        :param value: True = fixed, False = can vary
        :type value: bool
        :return: None
        :rtype: noneType
        """
        # TODO Should we try and cast value to bool rather than throw ValueError?
        if not isinstance(value, bool):
            raise ValueError
        self._fixed = value

    @property
    def error(self) -> float:
        """
        The error associated with the parameter.

        :return: Error associated with parameter
        :rtype: float
        """
        return self._value.error.magnitude

    @error.setter
    @stack_deco
    def error(self, value: float):
        """
        Set the error associated with the parameter.
        - implements undo/redo functionality.

        :param value: New error value
        :type value: float
        :return: None
        :rtype: noneType
        """
        if value < 0:
            raise ValueError
        self._args['error'] = value
        self._value._magnitude.std_dev = value

    # def for_fit(self):
    #     """
    #     Coverts oneself into a type which can be used for fitting. Note that the type
    #     is dependent on the fitting engine selected.
    #
    #     :return: parameter for fitting
    #     """
    #     return self._borg.fitting_engine.convert_to_par_object(self)

    def _validate(self, value: Any):
        """
        Verify value against constraints. This hasn't really been implemented as fitting is tricky.

        :param value: value to be verified
        :type value: Any
        :return: new value from constraint
        :rtype: Any
        """
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
    """
    Toy constraint class. This need to be improved.
    """

    def __init__(self, validator, fail_value):
        self._validator = validator
        self._fail_value = fail_value

    def __call__(self, *args, **kwargs):
        return self._validator(*args, **kwargs)

    def value(self):
        return self._fail_value


class BaseObj(MSONable):
    """
    This is the base class for which all higher level classes are built off of.
    NOTE: This object is serializable only if parameters are supplied as:
    `BaseObj(a=value, b=value)`. For `Parameter` or `Descriptor` objects we can
    cheat with `BaseObj(*[Descriptor(...), Parameter(...), ...])`.
    """

    _borg = borg

    def __init__(self, name: str, *args, **kwargs):
        """
        Set up the base class.

        :param name: Name of this object
        :type name: str
        :param args: Any arguments?
        :type args: Union[Parameter, Descriptor]
        :param parent: Parent object which is used for linking
        :type parent: Any
        :param kwargs: Fields which this class should contain
        """

        self._borg.map.add_vertex(self, obj_type='created')
        self.interface = None
        self.__dict__['name'] = name
        # If Parameter or Descriptor is given as arguments...
        for arg in args:
            if issubclass(arg.__class__, (BaseObj, Descriptor)):
                kwargs[arg.name] = arg
        # Set kwargs, also useful for serialization
        known_keys = self.__dict__.keys()
        self._kwargs = kwargs
        for key in kwargs.keys():
            if key in known_keys:
                raise AttributeError
            if issubclass(kwargs[key].__class__, (BaseObj, Descriptor)):
                self._borg.map.add_edge(self, kwargs[key])
                self._borg.map.reset_type(kwargs[key], 'created_internal')
            addLoggedProp(self, key, self.__getter(key), self.__setter(key), get_id=key, my_self=self,
                          test_class=BaseObj)

    # def fit_objects(self):
    #     """
    #     Collect all objects which can be fitted, convert them to fitting engine objects and
    #     return them as a list.
    #
    #     :return: List of fitting engine objects
    #     """
    #     return_objects = []
    #     for par_obj in self.get_fit_parameters():
    #         return_objects.append(par_obj.for_fit())
    #     return return_objects

    def get_parameters(self) -> List[Parameter]:
        """
        Get all parameter objects as a list.

        :return: List of `Parameter` objects.
        :rtype: List[Parameter]
        """
        fit_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_fit_parameters'):
                fit_list = [*fit_list, *item.get_fit_parameters()]
            elif isinstance(item, Parameter):
                fit_list.append(item)
        return fit_list

    def get_fit_parameters(self) -> List[Parameter]:
        """
        Get all objects which can be fitted (and are not fixed) as a list.

        :return: List of `Parameter` objects which can be used in fitting.
        :rtype: List[Parameter]
        """
        fit_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_fit_parameters'):
                fit_list = [*fit_list, *item.get_fit_parameters()]
            elif isinstance(item, Parameter) and not item.fixed:
                fit_list.append(item)
        return fit_list

    def get_all_parameters(self) -> List[Parameter]:
        """
        Get all parameter objects as a list.

        :return: List of `Parameter` objects which can be used in fitting.
        :rtype: List[Parameter]
        """
        fit_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_parameters'):
                fit_list = [*fit_list, *item.get_parameters()]
            elif isinstance(item, Parameter):
                fit_list.append(item)
        return fit_list

    def __dir__(self) -> Iterable[str]:
        """
        This creates auto-completion and helps out in iPython notebooks.

        :return: list of function and parameter names for auto-completion
        :rtype: List[str]
        """
        # new_objs = list(k for k in self.__dict__ if not k.startswith('_'))
        # class_objs = list(k for k in self.__class__.__dict__ if not k.startswith('_'))
        new_class_objs = list(k for k in dir(self.__class__) if not k.startswith('_'))
        return sorted(new_class_objs)

    def as_dict(self, skip: list = None) -> dict:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        :rtype: dict
        """
        if skip is None:
            skip = []
        d = MSONable.as_dict(self, skip=skip)
        for key, item in d.items():
            if hasattr(item, 'as_dict'):
                d[key] = item.as_dict(skip=skip)
        return d

    def generate_bindings(self):
        """
        Generate or re-generate bindings to an interface (if exists)

        :raises: AttributeError
        """
        if self.interface is None:
            raise AttributeError
        self.interface.generate_bindings(self)

    def switch_interface(self, new_interface_name: str):
        """
        Switch or create a new interface.
        """
        if self.interface is None:
            raise AttributeError
        self.interface.switch(new_interface_name)
        self.interface.generate_bindings(self)

    @staticmethod
    def __getter(key: str):

        def getter(obj):
            return obj._kwargs[key]

        return getter

    @staticmethod
    def __setter(key):
        def setter(obj, value):
            if issubclass(obj._kwargs[key].__class__, Descriptor):
                obj._kwargs[key].value = value
            else:
                obj._kwargs[key] = value

        return setter
