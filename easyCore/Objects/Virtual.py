#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import inspect
import weakref
from copy import deepcopy
from typing import Iterable, MutableSequence

from easyCore import borg
from easyCore.Fitting.Constraints import ObjConstraint


def raise_(ex):
    raise ex


def _remover(a_objID: str, v_objID: str):
    a_obj = borg.map.get_item_by_key(int(a_objID))
    if a_obj._constraints["virtual"].get(v_objID, False):
        del a_obj._constraints["virtual"][v_objID]


def realizer(obj):
    if getattr(obj, "_is_virtual", False):
        klass = getattr(obj, "__non_virtual_class__")
        import easyCore.Objects.Variable as ec_var
        args = []
        is_var = False
        if klass in ec_var.__dict__.values():
            is_var = True
        if is_var:
            kwargs = obj.to_data_dict()
            return klass(**kwargs)
        else:
            kwargs = {name: realizer(item) for name, item in obj._kwargs.items()}
            if isinstance(klass, Iterable) or issubclass(klass, MutableSequence):
                for key, value in inspect.signature(klass).parameters.items():
                    if value.kind in [inspect.Parameter.POSITIONAL_ONLY,
                                      inspect.Parameter.POSITIONAL_OR_KEYWORD]:
                        args.append(getattr(obj, key))
            return klass(*args, **kwargs)
    else:
        return obj


def component_realizer(obj, component, recursive=True):

    import easyCore.Objects.Variable as ec_var
    done_mapping = False
    if not isinstance(obj, Iterable) or not issubclass(obj.__class__, MutableSequence):
        old_component = obj._kwargs[component]
        new_components = realizer(obj._kwargs[component])
    else:
        old_component = obj[component]
        new_components = realizer(obj[component])
        idx = obj.index(old_component)
        del obj[component]
        obj.insert(idx, new_components)
        done_mapping = True
    if not recursive:
        for key in iter(component):
            if isinstance(key, 'str'):
                value = component._kwargs[key]
            else:
                value = key
                key = value._borg.map.convert_id_to_key(value)
            if getattr(value, '__old_class__', value.__class__) in ec_var.__dict__.values():
                continue
            component._borg.map.prune_vertex_from_edge(component, component._kwargs[key])
            component._borg.map.add_edge(component, old_component._kwargs[key])
            component._kwargs[key] = old_component._kwargs[key]
    if done_mapping:
        obj._borg.map.prune_vertex_from_edge(obj, old_component)
        obj._borg.map.add_edge(obj, new_components)
        obj._kwargs[component] = new_components
    return obj


def virtualizer(obj):
    """
    Convert a real `easyCore` object to a virtual object.
    This means that the object returned is an exact copy which is unsettable, unchangeable
    and linked to the parent object.
    The object can be realized and returned as a copy via the `realizer` function. If you need a
    component realized in place then `relalize_component` should be called.

    :param obj:
    :type obj:
    :return:
    :rtype:
    """
    # First  check if we're already a virtual object
    if getattr(obj, "_is_virtual", False):
        new_obj = deepcopy(obj)
        old_obj = obj._borg.map.get_item_by_key(obj._derived_from)
        constraint = ObjConstraint(new_obj, "", old_obj)
        constraint.external = True
        old_obj._constraints["virtual"][str(obj._borg.map.convert_id(new_obj).int)] = constraint
        new_obj._constraints["builtin"] = dict()
        # setattr(new_obj, "__previous_set", getattr(olobj, "__previous_set", None))
        weakref.finalize(
            new_obj,
            _remover,
            str(borg.map.convert_id(old_obj).int),
            str(borg.map.convert_id(new_obj).int),
        )
        return new_obj

    # The supplied class
    klass = getattr(obj, "__old_class__", obj.__class__)
    virtual_options = {
        "_is_virtual": True,
        "is_virtual": property(fget=lambda self: self._is_virtual),
        "_derived_from": property(fget=lambda self: self._borg.map.convert_id(obj).int),
        "__non_virtual_class__": klass,
        "realize": realizer,
        "relalize_component": component_realizer,
    }

    import easyCore.Objects.Variable as ec_var

    is_var = False
    if klass in ec_var.__dict__.values():
        is_var = True
    if is_var:
        virtual_options["fixed"] = property(
            fget=lambda self: self._fixed,
            fset=lambda self, value: raise_(
                AttributeError("Virtual parameters cannot be fixed")
            ),
        )
    # Generate a new class
    cls = type("Virtual" + klass.__name__, (klass,), virtual_options)
    # Determine what to do next.
    args = []
    # If `obj` is a parameter or descriptor etc, then simple mods.
    if hasattr(obj, "_constructor"):
        # All Variables are based on the Descriptor.
        d = obj.as_dict()
        if hasattr(d, "fixed"):
            d["fixed"] = True
        v_P = cls.from_dict(d)
        v_P._enabled = False
        constraint = ObjConstraint(v_P, "", obj)
        constraint.external = True
        obj._constraints["virtual"][str(cls._borg.map.convert_id(v_P).int)] = constraint
        v_P._constraints["builtin"] = dict()
        setattr(v_P, "__previous_set", getattr(obj, "__previous_set", None))
        weakref.finalize(
            v_P,
            _remover,
            str(borg.map.convert_id(obj).int),
            str(borg.map.convert_id(v_P).int),
        )
    else:
        # In this case, we need to be recursive.
        kwargs = {name: virtualizer(item) for name, item in obj._kwargs.items()}
        if isinstance(klass, Iterable) or issubclass(klass, MutableSequence):
            for key, value in inspect.signature(cls).parameters.items():
                if value.kind in [inspect.Parameter.POSITIONAL_ONLY,
                                  inspect.Parameter.POSITIONAL_OR_KEYWORD]:
                    args.append(getattr(obj, key))
        v_P = cls(*args, **kwargs)
    return v_P
