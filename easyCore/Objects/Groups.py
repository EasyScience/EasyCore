#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from numbers import Number
from typing import (
    Union,
    TypeVar,
    Optional,
    TYPE_CHECKING,
    Callable,
    List,
    Dict,
    Any,
    Tuple,
)

from easyCore import borg
from easyCore.Objects.ObjectClasses import BasedBase, Descriptor
from collections.abc import MutableSequence
from easyCore.Utils.UndoRedo import NotarizedDict

if TYPE_CHECKING:
    from easyCore.Utils.typing import B, iF, V


class BaseCollection(BasedBase, MutableSequence):
    """
    This is the base class for which all higher level classes are built off of.
    NOTE: This object is serializable only if parameters are supplied as:
    `BaseObj(a=value, b=value)`. For `Parameter` or `Descriptor` objects we can
    cheat with `BaseObj(*[Descriptor(...), Parameter(...), ...])`.
    """

    def __init__(
        self,
        name: str,
        *args: Union[B, V],
        interface: Optional[iF] = None,
        **kwargs,
    ):
        """
        Set up the base collection class.

        :param name: Name of this object
        :type name: str
        :param args: selection of
        :param _kwargs: Fields which this class should contain
        :type _kwargs: dict
        """
        BasedBase.__init__(self, name)
        kwargs = {key: kwargs[key] for key in kwargs.keys() if kwargs[key] is not None}
        _args = []
        for item in args:
            if not isinstance(item, list):
                _args.append(item)
            else:
                _args += item
        _kwargs = {}
        for key, item in kwargs.items():
            if isinstance(item, list) and len(item) > 0:
                _args += item
            else:
                _kwargs[key] = item
        kwargs = _kwargs
        for item in list(kwargs.values()) + _args:
            if not issubclass(type(item), (Descriptor, BasedBase)):
                raise AttributeError(
                    "A collection can only be formed from easyCore objects."
                )
        args = _args
        _kwargs = {}
        for key, item in kwargs.items():
            _kwargs[key] = item
        for arg in args:
            kwargs[str(borg.map.convert_id_to_key(arg))] = arg
            _kwargs[str(borg.map.convert_id_to_key(arg))] = arg

        # Set kwargs, also useful for serialization
        self._kwargs = NotarizedDict(**_kwargs)

        for key in kwargs.keys():
            if key in self.__dict__.keys() or key in self.__slots__:
                raise AttributeError(
                    f"Given kwarg: `{key}`, is an internal attribute. Please rename."
                )
            self._borg.map.add_edge(self, kwargs[key])
            self._borg.map.reset_type(kwargs[key], "created_internal")
            if interface is not None:
                kwargs[key].interface = interface
            # TODO wrap getter and setter in Logger
        if interface is not None:
            self.interface = interface
        self._kwargs._stack_enabled = True

    def insert(self, index: int, value: Union[V, B]) -> None:
        """
        Insert an object into the collection at an index.

        :param index: Index for easyCore object to be inserted.
        :type index: int
        :param value: Object to be inserted.
        :type value: Union[BasedBase, Descriptor]
        :return: None
        :rtype: None
        """
        t_ = type(value)
        if issubclass(t_, (BasedBase, Descriptor)):
            update_key = list(self._kwargs.keys())
            values = list(self._kwargs.values())
            # Update the internal dict
            new_key = str(borg.map.convert_id_to_key(value))
            update_key.insert(index, new_key)
            values.insert(index, value)
            self._kwargs.reorder(**{k: v for k, v in zip(update_key, values)})
            # ADD EDGE
            self._borg.map.add_edge(self, value)
            self._borg.map.reset_type(value, "created_internal")
            value.interface = self.interface
        else:
            raise AttributeError(
                "Only easyCore objects can be put into an easyCore group"
            )

    def __getitem__(self, idx: Union[int, slice]) -> Union[V, B]:
        """
        Get an item in the collection based on it's index.

        :param idx: index or slice of the collection.
        :type idx: Union[int, slice]
        :return: Object at index `idx`
        :rtype: Union[Parameter, Descriptor, BaseObj, 'BaseCollection']
        """
        if isinstance(idx, slice):
            start, stop, step = idx.indices(len(self))
            return self.__class__(
                getattr(self, "name"), *[self[i] for i in range(start, stop, step)]
            )
        if str(idx) in self._kwargs.keys():
            return self._kwargs[str(idx)]
        if isinstance(idx, str):
            idx = [index for index, item in enumerate(self) if item.name == idx]
            l = len(idx)
            if l == 0:
                raise IndexError(f"Given index does not exist")
            elif l == 1:
                idx = idx[0]
            else:
                return self.__class__(getattr(self, "name"), *[self[i] for i in idx])
        elif not isinstance(idx, int) or isinstance(idx, bool):
            if isinstance(idx, bool):
                raise TypeError("Boolean indexing is not supported at the moment")
            try:
                if idx > len(self):
                    raise IndexError(f"Given index {idx} is out of bounds")
            except TypeError:
                raise IndexError(
                    "Index must be of type `int`/`slice` or an item name (`str`)"
                )
        keys = list(self._kwargs.keys())
        return self._kwargs[keys[idx]]

    def __setitem__(self, key: int, value: Union[B, V]) -> None:
        """
        Set an item via it's index.

        :param key: Index in self.
        :type key: int
        :param value: Value which index key should be set to.
        :type value: Any
        """
        if isinstance(value, Number):  # noqa: S3827
            item = self.__getitem__(key)
            item.value = value
        elif issubclass(type(value), BasedBase) or issubclass(type(value), Descriptor):
            update_key = list(self._kwargs.keys())
            values = list(self._kwargs.values())
            old_item = values[key]
            # Update the internal dict
            update_dict = {update_key[key]: value}
            self._kwargs.update(update_dict)
            # ADD EDGE
            self._borg.map.add_edge(self, value)
            self._borg.map.reset_type(value, "created_internal")
            value.interface = self.interface
            # REMOVE EDGE
            self._borg.map.prune_vertex_from_edge(self, old_item)
        else:
            raise NotImplementedError(
                "At the moment only numerical values or easyCore objects can be set."
            )

    def __delitem__(self, key: int) -> None:
        """
        Try to delete  an idem by key.

        :param key:
        :type key:
        :return:
        :rtype:
        """
        keys = list(self._kwargs.keys())
        item = self._kwargs[keys[key]]
        self._borg.map.prune_vertex_from_edge(self, item)
        del self._kwargs[keys[key]]

    def __len__(self) -> int:
        """
        Get the number of items in this collection

        :return: Number of items in this collection.
        :rtype: int
        """
        return len(self._kwargs.keys())

    def _convert_to_dict(
        self, in_dict, encoder, skip: List[str] = [], **kwargs
    ) -> dict:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        :rtype: dict
        """
        d = {}
        if hasattr(self, "_modify_dict"):
            # any extra keys defined on the inheriting class
            d = self._modify_dict(skip=skip, **kwargs)
        in_dict["data"] = [
            encoder._convert_to_dict(item, skip=skip, **kwargs) for item in self
        ]
        out_dict = {**in_dict, **d}
        return out_dict

    @property
    def data(self) -> Tuple:
        """
        The data function returns a tuple of the keyword arguments passed to the
        constructor. This is useful for when you need to pass in a dictionary of data
        to other functions, such as with matplotlib's plot function.

        :param self: Access attributes of the class within the method
        :return: The values of the attributes in a tuple
        :doc-author: Trelent
        """
        return tuple(self._kwargs.values())

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__} `{getattr(self, 'name')}` of length {len(self)}"
        )

    def sort(
        self, mapping: Callable[[Union[B, V]], Any], reverse: bool = False
    ) -> None:
        """
        Sort the collection according to the given mapping.

        :param mapping: mapping function to sort the collection. i.e. lambda parameter: parameter.raw_value
        :type mapping: Callable
        :param reverse: Reverse the sorting.
        :type reverse: bool
        """
        i = list(self._kwargs.items())
        i.sort(key=lambda x: mapping(x[1]), reverse=reverse)
        self._kwargs.reorder(**{k[0]: k[1] for k in i})
