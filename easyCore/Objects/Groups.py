__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from numbers import Number
from typing import Union, List, Iterable

from easyCore import borg
from easyCore.Objects.Base import BaseObj, Descriptor, Parameter
from easyCore.Utils.json import MSONable
from collections.abc import Sequence


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

        for key, item in kwargs.items():
            if not issubclass(item.__class__, (Descriptor, BaseObj, BaseCollection)):
                raise AttributeError

        self._borg.map.add_vertex(self, obj_type='created')
        self.interface = None
        self.name = name

        for arg in args:
            if issubclass(arg.__class__, (BaseObj, Descriptor, BaseCollection, BaseCollection)):
                kwargs[str(borg.map.convert_id_to_key(arg))] = arg

        # Set kwargs, also useful for serialization
        self._kwargs = kwargs

        for key in kwargs.keys():
            if key in self.__dict__.keys():
                raise AttributeError
            self._borg.map.add_edge(self, kwargs[key])
            self._borg.map.reset_type(kwargs[key], 'created_internal')
            # TODO wrap getter and setter in Logger

    def append(self, item: Union[Parameter, Descriptor, BaseObj, 'BaseCollection']):
        if issubclass(item.__class__, (BaseObj, Descriptor, BaseCollection)):
            self._kwargs[str(borg.map.convert_id_to_key(item))] = item
            self._borg.map.add_edge(self, self._kwargs[str(borg.map.convert_id_to_key(item))])

    def __getitem__(self, i: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, 'BaseCollection']:
        if isinstance(i, slice):
            start, stop, step = i.indices(len(self))
            return self.__class__(getattr(self, 'name'), *[self[i] for i in range(start, stop, step)])
        if str(i) in self._kwargs.keys():
            return self._kwargs[str(i)]
        else:
            if i > len(self):
                raise IndexError
            else:
                keys = list(self._kwargs.keys())
                return self._kwargs[keys[i]]

    def __setitem__(self, key: int, value: Number):
        item = self.__getitem__(key)
        if isinstance(value, Number):  # noqa: S3827
            item.value = value
        else:
            raise NotImplementedError

    def __len__(self) -> int:
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
        for key, item in d.items():
            if hasattr(item, 'as_dict'):
                d[key] = item.as_dict(skip=skip)
        return d

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
