__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from copy import deepcopy
from typing import List, Union, Any, Iterable
from functools import cached_property

from easyCore import borg, ureg
from easyCore.Utils.typing import noneType
from easyCore.Utils.UndoRedo import stack_deco
from easyCore.Utils.json import MSONable

import numpy as np

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
        # Where did we come from
        self._parent = parent
        # Let the collective know we've been assimilated
        self._borg.map.add_vertex(id(self))
        # Make the connection between self and parent
        if self._parent is not None:
            self._borg.map.add_edge({id(self._parent), id(self)})

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
        self._callback: property = callback
        self.user_data: dict = {}
        self._type = type(value)

    @property
    def _parent(self) -> int:
        """
        Return the id of parent
        :return: python id of parent
        :rtype: int
        """
        return id(self._parent_store)

    @_parent.setter
    def _parent(self, parent: Any):
        """
        Set the parent of this self
        :param parent: Parent object
        :type parent: Any
        :return: None
        :rtype: noneType
        """
        # TODO This should also update the graph.....
        self._parent_store = parent

    @property
    def display_name(self) -> str:
        """
        Get a pretty display name
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
        Set the pretty display name
        :param name_str: pretty display name
        :type name_str: str
        :return: None
        :rtype: noneType
        """
        self._display_name = name_str

    @property
    def unit(self):
        """
        Get the unit associated with the value
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
        is not acceptable then the raw value can be obtained through `obj.raw_value`
        :return: Value of self
        :rtype: Any
        """
        # Cached property? Should reference callback.
        # Also should reference for undo/redo
        return self._value

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
        # TODO there should be a callback to the collective, logging this as a return(if from a non `easyCore` class)
        if hasattr(value, 'magnitude'):
            value = value.magnitude
            if hasattr(value, 'nominal_value'):
                value = value.nominal_value
        self._args['value'] = value
        self._value = self.__class__._constructor(**self._args)

    @property
    def raw_value(self):
        """
        Return the raw value of self without a unit
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

    @cached_property
    def compatible_units(self) -> List[str]:
        """
        Returns all possible units for which the current unit can be converted.
        :return: Possible conversion units
        :rtype: List[str]
        """
        return [str(u) for u in self.unit.compatible_units()]

    def __del__(self):
        """
        This would remove ones self from the collective
        :return: None
        :rtype: noneType
        """
        # TODO Remove oneself from the collective on deletion
        # self.__borg.map.remove_vertices(id(self))
        pass

    def __repr__(self):
        """Return printable representation of a Parameter object."""
        sval = "= %s" % self._value.magnitude
        if not self.value.unitless:
            sval += ' %s' % self.unit
        return "<%s '%s' %s>" % (self.__class__.__name__, self.name, sval)

    def as_dict(self) -> dict:
        """
        Convert ones self into a serialized form
        :return: dictionary of ones self
        :rtype: dict
        """
        super_dict = super().as_dict()
        super_dict['value'] = self.raw_value
        super_dict['units'] = self._args['units']
        # We'll have to serialize the callback option :face_palm:
        keys = super_dict.keys()
        if 'parent' in keys:
            del super_dict['parent']
        return super_dict

    def to_obj_type(self, data_type: Union['Descriptor', 'Parameter'], *kwargs):
        """
        Convert between a `Parameter` and a `Descriptor`
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
                 value: Union[float, np.ndarray, noneType],
                 error: Union[float, np.ndarray] = 0.,
                 min: float = -np.Inf,
                 max: float = np.Inf,
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
        super().__init__(name, value, **kwargs)

        # Create additional fitting elements
        self._min: float = min
        self._max: float = max
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
        self.__previous_unit = self.__class__.unit

        setattr(self.__class__, 'unit', property(fget=self.__class__.unit.fget,
                                                 fset=lambda obj, new_value: obj.__unit_setter(new_value),
                                                 fdel=self.__class__.unit.fdel))

        setattr(self.__class__, 'value', property(fget=self.__class__.value.fget,
                                                  fset=lambda obj, val: self.__previous_set(obj, obj._validate(val)),
                                                  fdel=self.__class__.value.fdel))

    def __unit_setter(self, value_str: str):  # noqa: S1144
        """
        Perform unit conversion. The value, max and min can change on unit change.
        :param value_str: new unit
        :type value_str: str
        :return: None
        :rtype: noneType
        """
        old_unit = str(self._args['units'])
        self.__previous_unit.fset(self, value_str)
        # Deal with min/max
        if not self.value.unitless:
            self._min = Q_(self.min, old_unit).to(self._units).magnitude
            self._max = Q_(self.max, old_unit).to(self._units).magnitude
        # Log the converted error
        self._args['error'] = self.value.error.magnitude

    @property
    def min(self) -> float:
        """
        Get the minimum value for fitting
        :return: minimum value
        :rtype: float
        """
        return self._min

    @min.setter
    @stack_deco
    def min(self, value: float):
        """
        Set the minimum value for fitting.
        - implements undo/redo functionality
        :param value: new minimum value
        :type value: float
        :return: None
        :rtype: noneType
        """
        self._min = value

    @property
    def max(self) -> float:
        """
        Get the maximum value for fitting
        :return: maximum value
        :rtype: float
        """
        return self._max

    @max.setter
    @stack_deco
    def max(self, value: float):
        """
        Get the maximum value for fitting.
        - implements undo/redo functionality
        :param value: new maximum value
        :type value: float
        :return: None
        :rtype: noneType
        """
        self._max = value

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
        Change the parameter vary while fitting state
        - implements undo/redo functionality
        :param value: True = fixed, False = can vary
        :type value: bool
        :return: None
        :rtype: noneType
        """
        self._fixed = value

    @property
    def error(self) -> float:
        """
        The error associated with the parameter
        :return: Error associated with parameter
        :rtype: float
        """
        return self._value.error.magnitude

    @error.setter
    @stack_deco
    def error(self, value: float):
        """
        Set the error associated with the parameter
        - implements undo/redo functionality
        :param value: New error value
        :type value: float
        :return: None
        :rtype: noneType
        """
        self._args['error'] = value
        self._value.error.magnitude = value

    def for_fit(self):
        """
        Coverts oneself into a type which can be used for fitting. Note that the type
        is dependent on the fitting engine selected
        :return: parameter for fitting
        """
        return self._borg.fitting_engine.convert_to_par_object(self)

    def _validate(self, value: Any):
        """
        Verify value against constraints. This hasn't really been implemented as fitting is tricky
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
    cheat with `BaseObj(*[Descriptor(...), Parameter(...), ...])`
    """

    _parent_store = None
    _borg = borg

    def __init__(self, name: str, *args, parent=None, **kwargs):
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

        self._parent = parent
        self.__dict__['name'] = name
        # If Parameter or Descriptor is given as arguments...
        for arg in args:
            if issubclass(arg.__class__, Descriptor):
                arg._parent = self
                kwargs[arg.name] = arg
        # Set kwargs, also useful for serialization
        known_keys = self.__dict__.keys()
        for key in kwargs.keys():
            if key in known_keys:
                raise AttributeError
            # Should we do it like this or assign property to class?
            # This way is easy, but can be overwritten i.e obj.foo = 1
            # Assigning property is more complex but protects obj.foo
            self.__dict__[key] = kwargs[key]
        self._kwargs = kwargs

    def fit_objects(self):
        """
        Collect all objects which can be fitted, convert them to fitting engine objects and
        return them as a list
        :return: List of fitting engine objects
        """
        return_objects = []
        for par_obj in self.get_parameters():
            return_objects.append(par_obj.for_fit())
        return return_objects

    def get_parameters(self) -> List[Parameter]:
        """
        Get all objects which can be fitted (and are not fixed) as a list
        :return: List of `Parameter` objects which can be used in fitting.
        :rtype: List[Parameter]
        """
        fit_list = []
        for key, item in self.__dict__.items():
            if hasattr(item, 'get_parameters'):
                fit_list = [fit_list, *item.get_parameters()]
            elif isinstance(item, Parameter) and not item.fixed:
                fit_list.append(item)
        return fit_list

    @property
    def _parent(self) -> int:
        """
        Return the id of parent
        :return: python id of parent
        :rtype: int
        """
        return id(self._parent_store)

    @_parent.setter
    def _parent(self, parent: Any):
        """
        Set the parent of this self
        :param parent: Parent object
        :type parent: Any
        :return: None
        :rtype: noneType
        """
        self._parent_store = parent

    def __dir__(self) -> Iterable[str]:
        """
        This creates auto-completion and helps out in iPython notebooks
        :return: list of function and parameter names for auto-completion
        :rtype: List[str]
        """
        new_objs = list(k for k in self.__dict__ if not k.startswith('_'))
        class_objs = list(k for k in self.__class__.__dict__ if not k.startswith('_'))
        return sorted(new_objs + class_objs)

    def as_dict(self) -> dict:
        """
        Convert ones self into a serialized form
        :return: dictionary of ones self
        :rtype: dict
        """
        d = MSONable.as_dict(self)
        for key, item in d.items():
            if hasattr(item, 'as_dict'):
                d[key] = item.as_dict()
        return d

    def set_binding(self, binding_name, binding_fun, *args, **kwargs):
        """
        Set the binding of parameters of self to interface counterparts
        :param binding_name: name of parameter to be bound
        :type binding_name: str
        :param binding_fun: function to do the binding
        :type binding_fun: Callable
        :param args: positional arguments for the binding function
        :param kwargs: keyword/value pair arguments for the binding function
        :return: None
        :rtype: noneType
        """
        parameters = [par.name for par in self.get_parameters()]
        if binding_name in parameters:
            setattr(self.__dict__[binding_name], '_callback', binding_fun(binding_name, *args, **kwargs))
