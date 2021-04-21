__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from numbers import Number
from typing import Union, List, Iterable

from easyCore import borg
from easyCore.Objects.Base import BaseObj, Descriptor, Parameter
from easyCore.Utils.json import MSONable
from collections.abc import Sequence
from easyCore.Utils.UndoRedo import NotarizedDict


class BaseCollection(MSONable, Sequence):
    """
    This is the base class for which all higher level classes are built off of.
    NOTE: This object is serializable only if parameters are supplied as:
    `BaseObj(a=value, b=value)`. For `Parameter` or `Descriptor` objects we can
    cheat with `BaseObj(*[Descriptor(...), Parameter(...), ...])`.
    """

    _borg = borg

    def __init__(self, name: str, *args, **kwargs):
        """
        Set up the base collection class.

        :param name: Name of this object
        :type name: str
        :param args: selection of
        :param _kwargs: Fields which this class should contain
        :type _kwargs: dict
        """

        kwargs = {key: kwargs[key] for key in kwargs.keys() if kwargs[key] is not None}

        for key, item in kwargs.items():
            if not issubclass(item.__class__, (Descriptor, BaseObj, BaseCollection)):
                raise AttributeError

        self._borg.map.add_vertex(self, obj_type='created')
        self.interface = None
        self.name = name
        self.user_data = {}

        _kwargs = {}
        for item in kwargs.values():
            _kwargs[str(borg.map.convert_id_to_key(item))] = item

        for arg in args:
            if issubclass(arg.__class__, (BaseObj, Descriptor, Parameter, BaseCollection)):
                _kwargs[str(borg.map.convert_id_to_key(arg))] = arg

        # Set kwargs, also useful for serialization
        self._kwargs = NotarizedDict(**_kwargs)

        for key in _kwargs.keys():
            if key in self.__dict__.keys():
                raise AttributeError
            self._borg.map.add_edge(self, _kwargs[key])
            self._borg.map.reset_type(_kwargs[key], 'created_internal')
            # TODO wrap getter and setter in Logger

    def append(self, item: Union[Parameter, Descriptor, BaseObj, 'BaseCollection']):
        """
        Add an idem to the end of the collection

        :param item: New item to be added
        :type item: Union[Parameter, Descriptor, BaseObj, 'BaseCollection']
        """
        if issubclass(item.__class__, (BaseObj, Descriptor, BaseCollection)):
            self._kwargs[str(borg.map.convert_id_to_key(item))] = item
            self._borg.map.add_edge(self, self._kwargs[str(borg.map.convert_id_to_key(item))])

    def __getitem__(self, idx: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, 'BaseCollection']:
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
        if idx > len(self):
            raise IndexError
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
            raise NotImplementedError

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
        
        :return: Number of items in this collection 
        :rtype: int
        """
        return len(self._kwargs.keys())

    def get_parameters(self) -> List[Parameter]:
        """
        Get all parameter objects as a list.

        :return: List of `Parameter` objects.
        :rtype: List[Parameter]
        """
        fit_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, 'get_parameters'):
                fit_list = [*fit_list, *item.get_parameters()]
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

    def __dir__(self) -> Iterable[str]:
        """
        This creates auto-completion and helps out in iPython notebooks.

        :return: list of function and parameter names for auto-completion
        :rtype: List[str]
        """
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
        for key in d.keys():
            if hasattr(d[key], 'as_dict'):
                d[key] = d[key].as_dict(skip=skip)
        data = []
        dd = {}
        for key in d.keys():
            if isinstance(d[key], dict):
                data.append(d[key])
            else:
                dd[key] = d[key]
        dd['data'] = data
        # Attach the id. This might be useful in connected applications.
        # Note that it is converted to int and then str because javascript....
        dd['@id'] = str(self._borg.map.convert_id(self).int)
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

    @property
    def constraints(self) -> list:
        pars = self.get_parameters()
        constraints = []
        for par in pars:
            con = par.constraints['user']
            for key in con.keys():
                constraints.append(con[key])
        return constraints

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} `{getattr(self, 'name')}` of length {len(self)}"