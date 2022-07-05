#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from numbers import Number
from typing import Union, TypeVar, Optional, TYPE_CHECKING, Callable, List, Dict, Any, Tuple

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

        for item in [*kwargs.values(), *args]:
            if not issubclass(type(item), (Descriptor, BasedBase)):
                raise AttributeError(
                    "A collection can only be formed from easyCore objects."
                )

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

    def as_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        :rtype: dict
        """
        d = super(BaseCollection, self).as_dict(skip=skip)
        data = []
        dd = {}
        for key in d.keys():
            if key == "@id":
                continue
            if isinstance(d[key], dict):
                data.append(d[key])
            else:
                dd[key] = d[key]
        dd["data"] = data
        # Attach the id. This might be useful in connected applications.
        # Note that it is converted to int and then str because javascript....
        dd["@id"] = d["@id"]
        return dd

    @property
    def data(self) -> Tuple:
        return tuple(self._kwargs.values())

    @classmethod
    def from_dict(cls, input_dict: Dict[str, Any]) -> "BaseCollection":
        """
        De-serialise the data and try to recreate the object.

        :param input_dict: serialised dictionary of an object. Usually generated from `obj.as_dict()`
        :type input_dict: dict
        :return: Class constructed from the input_dict
        """

        d = input_dict.copy()
        if len(d["data"]) > 0:
            for idx, item in enumerate(d["data"]):
                d[item["@id"]] = item
        del d["data"]
        return super(BaseCollection, cls).from_dict(d)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__} `{getattr(self, 'name')}` of length {len(self)}"
        )

    def sort(self, mapping: Callable[[Union[B, V]], Any], reverse: bool = False) -> None:
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
