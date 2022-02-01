#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import weakref
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

        is_var = False
        if klass in ec_var.__dict__.values():
            is_var = True
        if is_var:
            kwargs = obj.to_data_dict()
            return klass(**kwargs)
        else:
            kwargs = {name: realizer(item) for name, item in obj._kwargs.items()}
            return klass(**kwargs)
    else:
        return obj


def component_realizer(obj, component=None, recursive=True):
    if component is None:
        new_components = realizer(obj)
    else:
        old_component = obj._kwargs[component]
        new_components = realizer(obj._kwargs[component])
        if recursive:
            # Borg mapping should also take place here
            obj._borg.map.prune_vertex_from_edge(obj, old_component)
            obj._borg.map.add_edge(obj, new_components)
            obj._kwargs[component] = new_components
        else:
            pass
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
        v_P = cls(**kwargs)
    return v_P
