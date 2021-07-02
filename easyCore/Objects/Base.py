#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from __future__ import annotations

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

import numbers
import weakref

from copy import deepcopy
from typing import List, Union, Any, Iterable, Dict, Optional, Type, TYPE_CHECKING, Callable

from easyCore import borg, ureg, np, pint
from easyCore.Utils.classTools import addLoggedProp, addProp
from easyCore.Utils.Exceptions import CoreSetException
from easyCore.Utils.typing import noneType
from easyCore.Utils.UndoRedo import property_stack_deco
from easyCore.Utils.json import MSONable
from easyCore.Fitting.Constraints import SelfConstraint

if TYPE_CHECKING:
    from easyCore.Fitting.Constraints import ConstraintBase as Constraint

Q_ = ureg.Quantity
M_ = ureg.Measurement


class Descriptor(MSONable):
    """
    This is the base of all variable descriptions for models. It contains all information to describe a single
    unique property of an object. This description includes a name and value as well as optionally a unit, description
    and url (for reference material). Also implemented is a callback so that the value can be read/set from a linked
    library object.

    A `Descriptor` is typically something which describes part of a model and is non-fittable and generally changes the
    state of an object.
    """

    _constructor = Q_
    _borg = borg

    def __init__(self, name: str,
                 value: Any,
                 units: Optional[Union[noneType, str, ureg.Unit]] = None,
                 description: Optional[str] = '',
                 url: Optional[str] = '',
                 display_name: Optional[str] = None,
                 callback: Optional[property] = property(),
                 enabled: Optional[bool] = True,
                 parent=None):  # noqa: S107
        """
        This is the base of all variable descriptions for models. It contains all information to describe a single
        unique property of an object. This description includes a name and value as well as optionally a unit,
        description and url (for reference material). Also implemented is a callback so that the value can be read/set
        from a linked library object.

        A `Descriptor` is typically something which describes part of a model and is non-fittable and generally changes
        the state of an object.

        Units are provided by pint: https://github.com/hgrecco/pint

        :param name: Name of this object
        :param value: Value of this object
        :param units: This object can have a physical unit associated with it
        :param description: A brief summary of what this object is
        :param url: Lookup url for documentation/information
        :param callback: The property which says how the object is linked to another one
        :param parent: The object which is the parent to this one

        .. code-block:: python

             from easyCore.Objects.Base import Descriptor
             # Describe a color by text
             color_text = Descriptor('fav_colour', 'red')
             # Describe a color by RGB
             color_num = Descriptor('fav_colour', [1, 0, 0])

        .. note:: Undo/Redo functionality is implemented for the attributes `value`, `unit` and `display name`.
        """
        if not hasattr(self, '_args'):
            self._args = {
                'value': None,
                'units': ''
            }

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

        self._enabled = enabled

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

        :return: The pretty display name.
        """
        # TODO This might be better implementing fancy f-strings where we can return html,latex, markdown etc
        display_name = self._display_name
        if display_name is None:
            display_name = self.name
        return display_name

    @display_name.setter
    @property_stack_deco
    def display_name(self, name_str: str):
        """
        Set the pretty display name.

        :param name_str: Pretty display name of the object.
        :return: None
        """
        self._display_name = name_str

    @property
    def unit(self) -> pint.UnitRegistry:
        """
        Get the unit associated with the object.

        :return: Unit associated with self in `pint` form.
        """
        return self._units.units

    @unit.setter
    @property_stack_deco
    def unit(self, unit_str: str):
        """
        Set the unit to a new one.

        :param unit_str: String representation of the unit required. i.e `m/s`
        :return: None
        """
        if not isinstance(unit_str, str):
            unit_str = str(unit_str)
        new_unit = ureg.parse_expression(unit_str)
        self._units = new_unit
        self._args['units'] = str(new_unit)
        self._value = self.__class__._constructor(**self._args)

    @property
    def value(self) -> Any:
        """
        Get the value of self as a pint. This is should be usable for most cases. If a pint
        is not acceptable then the raw value can be obtained through `obj.raw_value`.

        :return: Value of self with unit.
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

    def __deepValueSetter(self, value: Any):
        """
        Set the value of self. This creates a pint with a unit.

        :param value: New value of self
        :return: None
        """
        # TODO there should be a callback to the collective, logging this as a return(if from a non `easyCore` class)
        if hasattr(value, 'magnitude'):
            value = value.magnitude
            if hasattr(value, 'nominal_value'):
                value = value.nominal_value
        self._args['value'] = value
        self._value = self.__class__._constructor(**self._args)

    @value.setter
    @property_stack_deco
    def value(self, value: Any):
        """
        Set the value of self. This creates a pint with a unit.

        :param value: New value of self
        :return: None
        """
        if not self.enabled:
            if borg.debug:
                raise CoreSetException(f'{str(self)} is not enabled.')
            return
        self.__deepValueSetter(value)
        if self._callback.fset is not None:
            try:
                self._callback.fset(value)
            except Exception as e:
                raise CoreSetException(e)

    @property
    def raw_value(self) -> Any:
        """
        Return the raw value of self without a unit.

        :return: The raw value of self
        """
        value = self._value
        if hasattr(value, 'magnitude'):
            value = value.magnitude
            if hasattr(value, 'nominal_value'):
                value = value.nominal_value
        return value

    @property
    def enabled(self) -> bool:
        """
        Logical property to see if the objects value can be directly set.

        :return: Can the objects value be set
        """
        return self._enabled

    @enabled.setter
    @property_stack_deco
    def enabled(self, value: bool):
        """
        Enable and disable the direct setting of an objects value field.

        :param value: True - objects value can be set, False - the opposite
        """
        self._enabled = value

    def convert_unit(self, unit_str: str):
        """
        Convert the value from one unit system to another. You will should use
        `compatible_units` to see if your new unit is compatible.

        :param unit_str: New unit in string form
        """
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
        """
        return [str(u) for u in self.unit.compatible_units()]

    def __repr__(self):
        """Return printable representation of a Descriptor/Parameter object."""
        class_name = self.__class__.__name__
        obj_name = self.name
        obj_value = self._value.magnitude
        if isinstance(obj_value, float):
            obj_value = '{:0.04f}'.format(obj_value)
        obj_units = ''
        if not self.unit.dimensionless:
            obj_units = ' {:~P}'.format(self.unit)
        out_str = f"<{class_name} '{obj_name}': {obj_value}{obj_units}>"
        return out_str

    def as_dict(self, skip: List[str] = None) -> Dict[str, str]:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        """
        if skip is None:
            skip = []
        super_dict = super().as_dict(skip=skip + ['parent', 'callback', '_finalizer'])
        super_dict['value'] = self.raw_value
        super_dict['units'] = self._args['units']
        # Attach the id. This might be useful in connected applications.
        # Note that it is converted to int and then str because javascript....
        super_dict['@id'] = str(self._borg.map.convert_id(self).int)
        return super_dict

    def to_obj_type(self, data_type: Parameter, *kwargs):
        """
        Convert between a `Parameter` and a `Descriptor`.

        :param data_type: class constructor of what we want to be
        :param kwargs: Additional keyword/value pairs for conversion
        :return: self as a new type
        """
        pickled_obj = self.as_dict()
        pickled_obj.update(kwargs)
        return data_type.from_dict(pickled_obj)


class Parameter(Descriptor):
    """
    This class is an extension of a ``easyCore.Object.Base.Descriptor``. Where the descriptor was for static objects,
    a `Parameter` is for dynamic objects. A parameter has the ability to be used in fitting and
    has additional fields to facilitate this.
    """

    _constructor = M_

    def __init__(self,
                 name: str,
                 value: Union[numbers.Number, np.ndarray],
                 error: Optional[Union[numbers.Number, np.ndarray]] = 0.,
                 min: Optional[numbers.Number] = -np.Inf,
                 max: Optional[numbers.Number] = np.Inf,
                 fixed: Optional[bool] = False,
                 **kwargs):
        """
        This class is an extension of a ``easyCore.Object.Base.Descriptor``. Where the descriptor was for static
        objects, a `Parameter` is for dynamic objects. A parameter has the ability to be used in fitting and has
        additional fields to facilitate this.

        :param name: Name of this obj
        :param value: Value of this object
        :param error: Error associated as sigma for this parameter
        :param min: Minimum value for fitting
        :param max: Maximum value for fitting
        :param fixed: Should this parameter vary when fitting?
        :param kwargs: Key word arguments for the `Descriptor` class.

        .. code-block:: python

             from easyCore.Objects.Base import Parameter
             # Describe a phase
             phase_basic = Parameter('phase', 3)
             # Describe a phase with a unit
             phase_unit = Parameter('phase', 3, units,='rad/s')

        .. note::
            Undo/Redo functionality is implemented for the attributes `value`, `error`, `min`, `max`, `fixed`
        """
        # Set the error
        self._args = {
            'value': value,
            'units': '',
            'error': error
        }

        if not isinstance(value, numbers.Number):
            raise ValueError("In a parameter the `value` must be numeric")
        if value < min:
            raise ValueError("`value` can not be less than `min`")
        if value > max:
            raise ValueError("`value` can not be greater than `max`")
        if error < 0:
            raise ValueError("Standard deviation `error` must be positive")

        super().__init__(name, value, **kwargs)
        self._args['units'] = str(self.unit)

        # Create additional fitting elements
        self._min: numbers.Number = min
        self._max: numbers.Number = max
        self._fixed: bool = fixed
        self.initial_value = self.value
        self._constraints: dict = {
            'user':    {},
            'builtin': {'min': SelfConstraint(self, '>=', '_min'),
                        'max': SelfConstraint(self, '<=', '_max')}
        }
        # This is for the serialization. Otherwise we wouldn't catch the values given to `super()`
        self._kwargs = kwargs

        # We have initialized from the Descriptor class where value has it's own undo/redo decorator
        # This needs to be bypassed to use the Parameter undo/redo stack
        fun = self.__class__.value.fset
        if hasattr(fun, 'func'):
            fun = getattr(fun, 'func')
        self.__previous_set: Callable = fun

        # Monkey patch the unit and the value to take into account the new max/min situation
        addProp(self, 'value',
                fget=self.__class__.value.fget,
                fset=self.__class__._property_value.fset,
                fdel=self.__class__.value.fdel)

    @property
    def _property_value(self) -> Union[numbers.Number, np.ndarray]:
        return self.value

    @_property_value.setter
    @property_stack_deco
    def _property_value(self, set_value: Union[numbers.Number, np.ndarray]):
        """
        Verify value against constraints. This hasn't really been implemented as fitting is tricky.

        :param set_value: value to be verified
        :return: new value from constraint
        """
        if isinstance(set_value, M_):
            set_value = set_value.magnitude.nominal_value
        # Save the old state and create the new state
        old_value = self._value
        self._value = self.__class__._constructor(value=set_value, units=self._args['units'], error=self._args['error'])

        def constraint_runner(this_constraint_type: dict, newer_value: numbers.Number):
            for constraint in this_constraint_type.values():
                if constraint.external:
                    constraint()
                    continue
                this_new_value = constraint(no_set=True)
                if this_new_value != newer_value:
                    if borg.debug:
                        print(f'Constraint `{constraint}` has been applied')
                    self._value = self.__class__._constructor(value=this_new_value, units=self._args['units'],
                                                              error=self._args['error'])
                newer_value = this_new_value
            return newer_value

        # First run the built in constraints. i.e. min/max
        constraint_type: dict = self.builtin_constraints
        new_value = constraint_runner(constraint_type, set_value)
        # Then run any user constraints.
        constraint_type: dict = self.user_constraints

        state = self._borg.stack.enabled
        if state:
            self._borg.stack.force_state(False)
        try:
            new_value = constraint_runner(constraint_type, new_value)
        finally:
            self._borg.stack.force_state(state)

        # Restore to the old state
        self._value = old_value
        self.__previous_set(self, new_value)

    def convert_unit(self, new_unit: str):  # noqa: S1144
        """
        Perform unit conversion. The value, max and min can change on unit change.

        :param new_unit: new unit
        :return: None
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
        """
        return self._min

    @min.setter
    @property_stack_deco
    def min(self, value: numbers.Number):
        """
        Set the minimum value for fitting.
        - implements undo/redo functionality.

        :param value: new minimum value
        :return: None
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
        """
        return self._max

    @max.setter
    @property_stack_deco
    def max(self, value: numbers.Number):
        """
        Get the maximum value for fitting.
        - implements undo/redo functionality.

        :param value: new maximum value
        :return: None
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
    @property_stack_deco
    def fixed(self, value: bool):
        """
        Change the parameter vary while fitting state.
        - implements undo/redo functionality.

        :param value: True = fixed, False = can vary
        :return: None
        """
        if not self.enabled:
            if self._borg.stack.enabled:
                self._borg.stack.pop()
            if borg.debug:
                raise CoreSetException(f'{str(self)} is not enabled.')
            return
        # TODO Should we try and cast value to bool rather than throw ValueError?
        if not isinstance(value, bool):
            raise ValueError
        self._fixed = value

    @property
    def error(self) -> float:
        """
        The error associated with the parameter.

        :return: Error associated with parameter
        """
        return self._value.error.magnitude

    @error.setter
    @property_stack_deco
    def error(self, value: float):
        """
        Set the error associated with the parameter.
        - implements undo/redo functionality.

        :param value: New error value
        :return: None
        """
        if value < 0:
            raise ValueError
        self._args['error'] = value
        self._value = self.__class__._constructor(**self._args)

    def __repr__(self) -> str:
        """
        Return printable representation of a Parameter object.
        """
        super_str = super().__repr__()
        super_str = super_str[:-1]
        s = []
        if self.fixed:
            super_str += " (fixed)"
        s.append(super_str)
        s.append("bounds=[%s:%s]" % (repr(self.min), repr(self.max)))
        return "%s>" % ', '.join(s)

    def __float__(self) -> float:
        return float(self.raw_value)

    def as_dict(self, skip: List[str] = None) -> dict:
        """
        Include enabled in the dict output as it's unfortunately skipped

        :param skip: Which items to skip when serializing
        :return: Serialized dictionary
        """
        new_dict = super(Parameter, self).as_dict()
        new_dict['enabled'] = self.enabled
        return new_dict

    @property
    def builtin_constraints(self) -> Dict[str, Type[Constraint]]:
        """
        Get the built in constrains of the object. Typically these are the min/max

        :return: Dictionary of constraints which are built into the system
        """
        return self._constraints['builtin']

    @property
    def user_constraints(self) -> Dict[str, Type[Constraint]]:
        """
        Get the user specified constrains of the object.

        :return: Dictionary of constraints which are user supplied
        """
        return self._constraints['user']

    @user_constraints.setter
    def user_constraints(self, constraints_dict: Dict[str, Type[Constraint]]):
        self._constraints['user'] = constraints_dict


class BasedBase(MSONable):

    __slots__ = ['_name', '_borg', 'user_data', '_kwargs']

    def __init__(self, name: str, interface=None):
        self._borg = borg
        self._borg.map.add_vertex(self, obj_type='created')
        self.interface = interface
        self.user_data: dict = {}
        self._name: str = name

    def __getstate__(self) -> Dict[str, str]:
        return self.as_dict(skip=['interface'])

    def __setstate__(self, state: Dict[str, str]):
        obj = self.from_dict(state)
        self.__init__(**obj._kwargs)

    @property
    def name(self) -> str:
        """
        Get the common name of the object.
        
        :return: Common name of the object
        """
        return self._name

    @name.setter
    def name(self, new_name: str):
        """
        Set a new common name for the object.

        :param new_name: New name for the object
        :return: None
        """
        self._name = new_name

    @property
    def interface(self):
        """
        Get the current interface of the object
        """
        return self._interface

    @interface.setter
    def interface(self, value):
        """
        Set the current interface to the object and generate bindings if possible. I.e.
        ```
        def __init__(self, bar, interface=None, **kwargs):
            super().__init__(self, **kwargs)
            self.foo = bar
            self.interface = interface # As final step after initialization to set correct bindings.
        ```
        """
        self._interface = value
        if value is not None:
            self.generate_bindings()

    def generate_bindings(self):
        """
        Generate or re-generate bindings to an interface (if exists)

        :raises: AttributeError
        """
        if self.interface is None:
            raise AttributeError('Interface error for generating bindings. `interface` has to be set.')
        interfaceable_children = [key
                                  for key in self._borg.map.get_edges(self)
                                  if issubclass(type(self._borg.map.get_item_by_key(key)), BasedBase)]
        for child_key in interfaceable_children:
            child = self._borg.map.get_item_by_key(child_key)
            child.interface = self.interface
        self.interface.generate_bindings(self)

    def switch_interface(self, new_interface_name: str):
        """
        Switch or create a new interface.
        """
        if self.interface is None:
            raise AttributeError('Interface error for generating bindings. `interface` has to be set.')
        self.interface.switch(new_interface_name)
        self.generate_bindings()

    @property
    def constraints(self) -> List[Type[Constraint]]:
        pars = self.get_parameters()
        constraints = []
        for par in pars:
            con: Dict[str, Type[Constraint]] = par.user_constraints
            for key in con.keys():
                constraints.append(con[key])
        return constraints

    def as_dict(self, skip: List[str] = None) -> Dict[str, str]:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        """
        if skip is None:
            skip = []
        d = MSONable.as_dict(self, skip=skip)
        for key, item in d.items():
            if hasattr(item, 'as_dict'):
                d[key] = item.as_dict(skip=skip)
        # Attach the id. This might be useful in connected applications.
        # Note that it is converted to int and then str because javascript....
        d['@id'] = str(self._borg.map.convert_id(self).int)
        return d

    def get_parameters(self) -> List[Parameter]:
        """
        Get all parameter objects as a list.

        :return: List of `Parameter` objects.
        """
        par_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_parameters'):
                par_list = [*par_list, *item.get_parameters()]
            elif isinstance(item, Parameter):
                par_list.append(item)
        return par_list

    def _get_linkable_attributes(self) -> List[Union[Descriptor, Parameter]]:
        """
        Get all objects which can be linked against as a list.

        :return: List of `Descriptor`/`Parameter` objects.
        """
        item_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, '_get_linkable_attributes'):
                item_list = [*item_list, *item._get_linkable_attributes()]
            elif issubclass(type(item), Descriptor):
                item_list.append(item)
        return item_list

    def get_fit_parameters(self) -> List[Parameter]:
        """
        Get all objects which can be fitted (and are not fixed) as a list.

        :return: List of `Parameter` objects which can be used in fitting.
        """
        fit_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_fit_parameters'):
                fit_list = [*fit_list, *item.get_fit_parameters()]
            elif isinstance(item, Parameter) and item.enabled and not item.fixed:
                fit_list.append(item)
        return fit_list

    def __dir__(self) -> Iterable[str]:
        """
        This creates auto-completion and helps out in iPython notebooks.

        :return: list of function and parameter names for auto-completion
        """
        new_class_objs = list(k for k in dir(self.__class__) if not k.startswith('_'))
        return sorted(new_class_objs)


class BaseObj(BasedBase):
    """
    This is the base class for which all higher level classes are built off of.
    NOTE: This object is serializable only if parameters are supplied as:
    `BaseObj(a=value, b=value)`. For `Parameter` or `Descriptor` objects we can
    cheat with `BaseObj(*[Descriptor(...), Parameter(...), ...])`.
    """
    def __init__(self, name: str, *args: Optional[Union[Type[Descriptor], Type[BasedBase]]],
                 **kwargs: Optional[Union[Type[Descriptor], Type[BasedBase]]]):
        """
        Set up the base class.

        :param name: Name of this object
        :param args: Any arguments?
        :param kwargs: Fields which this class should contain
        """
        super(BaseObj, self).__init__(name)
        # If Parameter or Descriptor is given as arguments...
        for arg in args:
            if issubclass(type(arg), (BaseObj, Descriptor)):
                kwargs[getattr(arg, 'name')] = arg
        # Set kwargs, also useful for serialization
        known_keys = self.__dict__.keys()
        self._kwargs = kwargs
        for key in kwargs.keys():
            if key in known_keys:
                raise AttributeError
            if issubclass(type(kwargs[key]), (BasedBase, Descriptor)) or \
                    'BaseCollection' in [c.__name__ for c in type(kwargs[key]).__bases__]:
                self._borg.map.add_edge(self, kwargs[key])
                self._borg.map.reset_type(kwargs[key], 'created_internal')
            addLoggedProp(self, key, self.__getter(key), self.__setter(key),
                          get_id=key, my_self=self, test_class=BaseObj)

    def _add_component(self, key: str, component: Union[Type[Descriptor], Type[BasedBase]]):
        """
        Dynamically add a component to the class.

        :param key: Name of component to be added
        :param component: Component to be added
        :return: None
        """
        self._kwargs[key] = component
        self._borg.map.add_edge(self, component)
        self._borg.map.reset_type(component, 'created_internal')
        addLoggedProp(self, key, self.__getter(key), self.__setter(key), get_id=key, my_self=self,
                      test_class=BaseObj)
        
    def __setattr__(self, key, value):
        if hasattr(self, key) and issubclass(type(value), (BasedBase, Descriptor)):
            old_obj = self.__getattribute__(key)
            self._borg.map.prune_vertex_from_edge(self, old_obj)
            self._borg.map.add_edge(self, value)
        super(BaseObj, self).__setattr__(key, value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} `{getattr(self, 'name')}`"

    @staticmethod
    def __getter(key: str):
        def getter(obj: Union[Type[Descriptor], Type[BasedBase]]):
            return obj._kwargs[key]
        return getter

    @staticmethod
    def __setter(key: str):
        def setter(obj: Union[Type[Descriptor], Type[BasedBase]], value: float):
            if issubclass(obj._kwargs[key].__class__, Descriptor):
                obj._kwargs[key].value = value
            else:
                obj._kwargs[key] = value
        return setter
