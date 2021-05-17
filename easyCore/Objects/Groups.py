__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from numbers import Number
from typing import Union, List, Iterable

from easyCore import borg
from easyCore.Objects.Base import BasedBase, Descriptor
from collections.abc import Sequence
from easyCore.Utils.UndoRedo import NotarizedDict


class BaseCollection(BasedBase, Sequence):
    """
    This is the base class for which all higher level classes are built off of.
    NOTE: This object is serializable only if parameters are supplied as:
    `BaseObj(a=value, b=value)`. For `Parameter` or `Descriptor` objects we can
    cheat with `BaseObj(*[Descriptor(...), Parameter(...), ...])`.
    """
    def __init__(self, name: str, *args, interface=None, **kwargs):
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
                raise AttributeError('A collection can only be formed from easyCore objects.')

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
                raise AttributeError(f'Given kwarg: `{key}`, is an internal attribute. Please rename.')
            self._borg.map.add_edge(self, kwargs[key])
            self._borg.map.reset_type(kwargs[key], 'created_internal')
            kwargs[key].interface = interface
            # TODO wrap getter and setter in Logger
        self.interface = interface

    def append(self, item: Union[Descriptor, BasedBase]):
        """
        Add an idem to the end of the collection

        :param item: New item to be added
        :type item: Union[Parameter, Descriptor, BaseObj, 'BaseCollection']
        """
        if issubclass(item.__class__, (BasedBase, Descriptor)):
            self._kwargs[str(borg.map.convert_id_to_key(item))] = item
            self._borg.map.add_edge(self, self._kwargs[str(borg.map.convert_id_to_key(item))])
            item.interface = self.interface
        else:
            raise AttributeError('A collection can only be formed from easyCore objects.')

    def __getitem__(self, idx: Union[int, slice]) -> Union[Descriptor, BasedBase]:
        """
        Get an item in the collection based on it's index.

        :param idx: index or slice of the collection.
        :type idx: Union[int, slice]
        :return: Object at index `idx`
        :rtype: Union[Parameter, Descriptor, BaseObj, 'BaseCollection']
        """
        if isinstance(idx, slice):
            start, stop, step = idx.indices(len(self))
            return self.__class__(getattr(self, 'name'), *[self[i] for i in range(start, stop, step)])
        if str(idx) in self._kwargs.keys():
            return self._kwargs[str(idx)]
        if isinstance(idx, str):
            names = [item.name for item in self]
            if idx in names:
                idx = names.index(idx)
        elif not isinstance(idx, int) or isinstance(idx, bool):
            if isinstance(idx, bool):
                raise TypeError('Boolean indexing is not supported at the moment')
            try:
                if idx > len(self):
                    raise IndexError(f'Given index {idx} is out of bounds')
            except TypeError:
                raise IndexError('Index must be of type `int`/`slice` or an item name (`str`)')
        keys = list(self._kwargs.keys())
        return self._kwargs[keys[idx]]

    def __setitem__(self, key: int, value: Number):
        """
        Set an item via it's index.

        :param key: Index in self. 
        :type key: int
        :param value: Value which index key should be set to.
        :type value: Any
        """
        item = self.__getitem__(key)
        if isinstance(value, Number):  # noqa: S3827
            item.value = value
        else:
            raise NotImplementedError('At the moment only numerical values can be set.')

    def __delitem__(self, key: int):
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

    def as_dict(self, skip: list = None) -> dict:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        :rtype: dict
        """
        d = super(BaseCollection, self).as_dict(skip=skip)
        data = []
        dd = {}
        for key in d.keys():
            if key == '@id':
                continue
            if isinstance(d[key], dict):
                data.append(d[key])
            else:
                dd[key] = d[key]
        dd['data'] = data
        # Attach the id. This might be useful in connected applications.
        # Note that it is converted to int and then str because javascript....
        dd['@id'] = d['@id']
        return dd

    @classmethod
    def from_dict(cls, input_dict: dict):
        """
        De-serialise the data and try to recreate the object.

        :param input_dict: serialised dictionary of an object. Usually generated from `obj.as_dict()`
        :type input_dict: dict
        :return: Class constructed from the input_dict
        """

        d = input_dict.copy()
        if len(d['data']) > 0:
            for idx, item in enumerate(d['data'][1:]):
                d[str(idx)] = item
            d['data'] = d['data'][0]
        else:
            del d['data']
        return super(BaseCollection, cls).from_dict(d)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} `{getattr(self, 'name')}` of length {len(self)}"
