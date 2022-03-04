#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import warnings


class AccessorRegistrationWarning(Warning):
    """Warning for conflicts in accessor registration."""


class _CachedAccessor(object):
    """Custom property-like object (descriptor) for caching accessors."""

    def __init__(self, name, accessor):
        self._name = name
        self._accessor = accessor

    def __get__(self, obj, cls):
        if obj is None:
            # we're accessing the attribute of the class, i.e., Dataset.geo
            return self._accessor
        try:
            accessor_obj = self._accessor(obj)
        except AttributeError:
            # __getattr__ on data object will swallow any AttributeErrors raised
            # when initializing the accessor, so we need to raise as something
            # else (GH933):
            msg = "error initializing %r accessor." % self._name
            raise RuntimeError(msg)
        # Replace the property with the accessor object. Inspired by:
        # http://www.pydanny.com/cached-property.html
        # We need to use object.__setattr__ because we overwrite __setattr__ on
        # AttrAccessMixin.
        # object.__setattr__(obj, self._name, accessor_obj)
        return accessor_obj


def _register_accessor(name, cls):
    def decorator(accessor):
        if hasattr(cls, name):
            warnings.warn(
                "registration of accessor %r under name %r for type %r is "
                "overriding a preexisting attribute with the same name."
                % (accessor, name, cls),
                AccessorRegistrationWarning,
                stacklevel=2,
            )
        setattr(cls, name, _CachedAccessor(name, accessor))
        return accessor

    return decorator


def register_accessor(name, cls):
    return _register_accessor(name, cls)
