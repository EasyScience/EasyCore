#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import numbers
from typing import Any, Optional, List

import numpy as np
import param
import pint

from easyCore.Objects.core import ComponentSerializer
from easyCore import ureg, borg


class CoreNumerics:
    @staticmethod
    def __pre__(object1, object2=None):
        """
        This function is used to prepare the object for the operation. It returns a dictionary of the to cast type.
        In this schema `object1` is the object that is being operated on.
        :param object1:
        :type object1:
        :param object2:
        :type object2:
        :return:
        :rtype:
        """
        obj1 = object1.value_obj
        obj1_dict = object1.as_dict()
        if hasattr(object2, "value_obj"):
            obj2 = object2.value_obj
        else:
            if isinstance(object2, numbers.Number):
                obj2 = ureg.Quantity(object2)
            elif isinstance(object2, (ureg.Quantity, ureg.Measurement)):
                obj2 = object2
            elif object2 is None:
                obj2 = None
            else:
                raise TypeError(f"Cannot operate on {object2} and {object1}")
        return obj1_dict, obj1, obj2

    @staticmethod
    def __post__(object_dict, value):
        magnitude = value.magnitude
        std = None
        if not isinstance(magnitude, numbers.Number):
            std = float(value.std_dev)
            magnitude = magnitude.nominal_value
        object_dict["value"] = magnitude
        object_dict["units"] = str(value.units)
        if std is not None:
            object_dict["error"] = std
        return ComponentSerializer.from_dict(object_dict)

    def __abs__(self):
        obj_dict, obj1, obj2 = self.__pre__(self)
        return self.__post__(obj_dict, abs(obj1))

    def __add__(self, other):
        obj_dict, obj1, obj2 = self.__pre__(self, other)
        return self.__post__(obj_dict, obj1 + obj2)

    def __sub__(self, other):
        obj_dict, obj1, obj2 = self.__pre__(self, other)
        return self.__post__(obj_dict, obj1 - obj2)

    def __mul__(self, other):
        obj_dict, obj1, obj2 = self.__pre__(self, other)
        return self.__post__(obj_dict, obj1 * obj2)

    def __div__(self, other):
        obj_dict, obj1, obj2 = self.__pre__(self, other)
        return self.__post__(obj_dict, obj1 / obj2)

    # def __radd__(self, other):
    #     obj_dict, obj1, obj2 = self.__pre__(self)
    #     return self.__post__(obj_dict, obj2 + obj1)
    #
    # def __rsub__(self, other):
    #     obj_dict = self.__pre__(other)
    #     return self.__post__(obj_dict, other.value_obj - self.value_obj)
    #
    # def __rmul__(self, other):
    #     obj_dict = self.__pre__(other)
    #     return self.__post__(obj_dict, other.value_obj * self.value_obj)
    #
    # def __rdiv__(self, other):
    #     obj_dict = self.__pre__(other)
    #     return self.__post__(obj_dict, other.value_obj / self.value_obj)

    def __pow__(self, other):
        obj_dict, obj1, obj2 = self.__pre__(self, other)
        return self.__post__(obj_dict, obj1**obj2)

    def __lt__(self, other):
        return

    def __le__(self, other):
        pass

    def __gt__(self, other):
        pass

    def __ge__(self, other):
        pass


class FloatNumber(param.Parameter):
    """FLoat Parameter that must be a bool"""

    def _validate_value(self, val, allow_None):
        super(FloatNumber, self)._validate_value(val, allow_None)
        if not isinstance(val, numbers.Number) or isinstance(val, bool):
            raise ValueError(
                "FloatNumber parameter %r must be a number, "
                "not %r." % (self.name, val)
            )


class Descriptor(ComponentSerializer, param.Parameterized, CoreNumerics):

    value_modified = param.Event()

    label = param.String(default=None, doc="Label of the descriptor")
    value = param.Parameter(default=None, doc="Value of the descriptor")
    value_obj = param.Parameter(default=None, doc="Raw value of the descriptor")
    unit = param.Parameter(default="", doc="Units of the descriptor")
    description = param.String(default="", doc="Description of the descriptor")
    url = param.String(default="", doc="URL of the descriptor")
    enabled = param.Boolean(default=True, doc="Whether the descriptor is enabled")
    parent = param.Parameter(default=None, doc="Parent of the descriptor")
    watchers = param.Dict(
        default={
            "user": {},
            "builtin": {},
            "virtual": {},
        },
        doc="Watchers for the object",
        readonly=True,
    )

    _constructor = ureg.Quantity
    _borg = borg
    args = {
        "value": lambda obj: getattr(obj, "value"),
        "units": lambda obj: str(getattr(obj, "unit")),
    }
    _watch_attributes = ["value", "unit"]

    def __init__(self, label: str, value: Any, **kwargs):
        super().__init__(label=label, value=value, **kwargs)

        self._update_full_value(None)
        self._update_from_full_value(None)
        self.param.watch(self._update_full_value, self.__class__._watch_attributes)

        # Let the collective know we've been assimilated
        self._borg.map.add_vertex(self, obj_type="created")
        # Make the connection between self and parent
        if self.parent is not None:
            self._borg.map.add_edge(self.parent, self)

        self.user_data: dict = {}

    def _update_full_value(self, event):
        self.param.value_obj.readonly = False
        self.value_obj = self._constructor(
            **{name: value(self) for name, value in self.args.items()}
        )
        self.param.value_obj.readonly = True
        self._update_from_full_value(event)

    def _update_from_full_value(self, event):
        if event is not None and event.name == "unit":
            self.value = self.value_obj.magnitude
        if event is None:
            self.unit = str(self.value_obj.units)

    def __repr__(self):
        """Return printable representation of a Descriptor/Parameter object."""
        class_name = self.__class__.__name__
        obj_name = self.label
        obj_value = self.value
        if isinstance(obj_value, float):
            obj_value = "{:0.04f}".format(obj_value)
        obj_units = ""
        if not self.value_obj.dimensionless:
            obj_units = " {:~P}".format(self.value_obj.units)
        out_str = f"<{class_name} '{obj_name}': {obj_value}{obj_units}>"
        return out_str

    @property
    def compatible_units(self) -> List[str]:
        """
        Returns all possible units for which the current unit can be converted.

        :return: Possible conversion units
        """
        return [str(u) for u in self.value_obj.units.compatible_units()]

    def convert_unit(self, unit_str: str):
        """
        Convert the value from one unit system to another. You should use
        `compatible_units` to see if your new unit is compatible.

        :param unit_str: New unit in string form
        """
        new_unit = ureg.parse_expression(unit_str)
        new_value_obj = self.value_obj.to(new_unit)
        self.param.value_obj.readonly = False
        self.value_obj = new_value_obj
        self.param.value_obj.readonly = True
        with param.discard_events(self):
            self.value = self.value_obj.magnitude
            self.unit = str(self.value_obj.units)
        self.param.trigger("value_modified")

    def add_watcher(self, name, attributes, callback, priority=1):
        watcher = self.param.watch(callback, attributes, precedence=priority)
        self.watchers["user"][name] = watcher


class Parameter(Descriptor):
    """
    This class is an extension of a ``easyCore.Object.Base.Descriptor``. Where the descriptor was for static objects,
    a `Parameter` is for dynamic objects. A parameter has the ability to be used in fitting and
    has additional fields to facilitate this.
    """

    _constructor = ureg.Measurement
    value = FloatNumber(default=0.0, doc="Value of the descriptor")
    error = param.Parameter(default=0.0, doc="Error of the parameter")
    min = FloatNumber(default=-np.Inf, doc="Minimum value of the parameter")
    max = FloatNumber(default=np.Inf, doc="Maximum value of the parameter")
    fixed = param.Boolean(default=False, doc="Whether the parameter is fixed or not")
    initial_value = param.Number(
        default=None, readonly=False, doc="Initial value of the parameter"
    )
    args = {
        "value": lambda obj: getattr(obj, "value"),
        "units": lambda obj: str(getattr(obj, "unit")),
        "error": lambda obj: getattr(obj, "error"),
    }
    _watch_attributes = ["value", "unit", "error"]

    def __init__(self, label: str, value: Any, **kwargs):
        super().__init__(label=label, value=value, initial_value=value, **kwargs)
        self.param.initial_value.readonly = True
        self.param.watch(self._validate_min_max, ["min", "max"])

    def _validate_min_max(self, event: param.Event) -> None:
        """
        Set the minimum value for fitting.
        - implements undo/redo functionality.

        :param value: new minimum value
        :return: None
        """
        value = event.new
        if event.name == "min" and value >= self.value:
            raise ValueError(
                f"The current set value ({self.value}) is less than the desired min value ({value})."
            )
        elif event.name == "max" and value <= self.value:
            raise ValueError(
                f"The current set value ({self.value}) is greater than the desired max value ({value})."
            )

    def _update_from_full_value(self, event):
        if event is not None and event.name == "unit":
            self.value = self.value_obj.magnitude.nominal_value
            self.error = self.value_obj.magnitude.std_dev
        if event is None:
            self.unit = str(self.value_obj.units)

    def convert_unit(self, new_unit: str):  # noqa: S1144
        """
        Perform unit conversion. The value, max and min can change on unit change.

        :param new_unit: new unit
        :return: None
        """
        old_unit = self.unit
        super().convert_unit(new_unit)
        # Deal with min/max. Error is auto corrected
        if not self.value.unitless and old_unit != "dimensionless":
            self.min = ureg.Quantity(self.min, old_unit).to(self._units).magnitude
            self.max = ureg.Quantity(self.max, old_unit).to(self._units).magnitude
        # Log the new converted error
        self.error = self.value_obj.magnitude.std_dev
