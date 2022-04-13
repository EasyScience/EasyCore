from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

import numbers

from typing import (
    List,
    Union,
    Iterable,
    Dict,
    Optional,
    TypeVar,
    TYPE_CHECKING,
    Callable,
)

from easyCore import borg
from easyCore.Utils.json import MSONable
from easyCore.Utils.classTools import addLoggedProp
from .Variable import Parameter, Descriptor

if TYPE_CHECKING:
    from easyCore.Utils.typing import C, V, iF


class BasedBase(MSONable):
    __slots__ = ["_name", "_borg", "user_data", "_kwargs"]

    def __init__(self, name: str, interface: Optional[iF] = None):
        self._borg = borg
        self._borg.map.add_vertex(self, obj_type="created")
        self.interface = interface
        self.user_data: dict = {}
        self._name: str = name

    def __reduce__(self):
        """
        Make the class picklable.
        Due to the nature of the dynamic class definitions special measures need to be taken.

        :return: Tuple consisting of how to make the object
        :rtype: tuple
        """
        state = self.as_dict()
        cls = getattr(self, "__old_class__", self.__class__)
        return cls.from_dict, (state,)

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
    def interface(self) -> iF:
        """
        Get the current interface of the object
        """
        return self._interface

    @interface.setter
    def interface(self, new_interface: iF):
        """
        Set the current interface to the object and generate bindings if possible. iF.e.
        ```
        def __init__(self, bar, interface=None, **kwargs):
            super().__init__(self, **kwargs)
            self.foo = bar
            self.interface = interface # As final step after initialization to set correct bindings.
        ```
        """
        self._interface = new_interface
        if new_interface is not None:
            self.generate_bindings()

    def generate_bindings(self):
        """
        Generate or re-generate bindings to an interface (if exists)

        :raises: AttributeError
        """
        if self.interface is None:
            raise AttributeError(
                "Interface error for generating bindings. `interface` has to be set."
            )
        interfaceable_children = [
            key
            for key in self._borg.map.get_edges(self)
            if issubclass(type(self._borg.map.get_item_by_key(key)), BasedBase)
        ]
        for child_key in interfaceable_children:
            child = self._borg.map.get_item_by_key(child_key)
            child.interface = self.interface
        self.interface.generate_bindings(self)

    def switch_interface(self, new_interface_name: str):
        """
        Switch or create a new interface.
        """
        if self.interface is None:
            raise AttributeError(
                "Interface error for generating bindings. `interface` has to be set."
            )
        self.interface.switch(new_interface_name)
        self.generate_bindings()

    @property
    def constraints(self) -> List[C]:
        pars = self.get_parameters()
        constraints = []
        for par in pars:
            con: Dict[str, C] = par.user_constraints
            for key in con.keys():
                constraints.append(con[key])
        return constraints

    def as_dict(
        self, skip: Optional[List[str]] = None
    ) -> Dict[str, Union[str, bool, numbers.Number]]:
        """
        Convert ones self into a serialized form.

        :return: dictionary of ones self
        """
        if skip is None:
            skip = []
        d = MSONable.as_dict(self, skip=skip)
        for key, item in d.items():
            if hasattr(item, "as_dict"):
                d[key] = item.as_dict(skip=skip)
        # Attach the id. This might be useful in connected applications.
        # Note that it is converted to int and then str because javascript....
        d["@id"] = str(self._borg.map.convert_id(self).int)
        return d

    def get_parameters(self) -> List[Parameter]:
        """
        Get all parameter objects as a list.

        :return: List of `Parameter` objects.
        """
        par_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, "get_parameters"):
                par_list = [*par_list, *item.get_parameters()]
            elif isinstance(item, Parameter):
                par_list.append(item)
        return par_list

    def _get_linkable_attributes(self) -> List[V]:
        """
        Get all objects which can be linked against as a list.

        :return: List of `Descriptor`/`Parameter` objects.
        """
        item_list = []
        for key, item in self._kwargs.items():
            if hasattr(item, "_get_linkable_attributes"):
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
            if hasattr(item, "get_fit_parameters"):
                fit_list = [*fit_list, *item.get_fit_parameters()]
            elif isinstance(item, Parameter) and item.enabled and not item.fixed:
                fit_list.append(item)
        return fit_list

    def __dir__(self) -> Iterable[str]:
        """
        This creates auto-completion and helps out in iPython notebooks.

        :return: list of function and parameter names for auto-completion
        """
        new_class_objs = list(k for k in dir(self.__class__) if not k.startswith("_"))
        return sorted(new_class_objs)


if TYPE_CHECKING:
    B = TypeVar("B", bound=BasedBase)
    BV = TypeVar("BV", bound=Union[BasedBase, Descriptor])


class BaseObj(BasedBase):
    """
    This is the base class for which all higher level classes are built off of.
    NOTE: This object is serializable only if parameters are supplied as:
    `BaseObj(a=value, b=value)`. For `Parameter` or `Descriptor` objects we can
    cheat with `BaseObj(*[Descriptor(...), Parameter(...), ...])`.
    """

    def __init__(
        self,
        name: str,
        *args: Optional[BV],
        **kwargs: Optional[BV],
    ):
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
                kwargs[getattr(arg, "name")] = arg
        # Set kwargs, also useful for serialization
        known_keys = self.__dict__.keys()
        self._kwargs = kwargs
        for key in kwargs.keys():
            if key in known_keys:
                raise AttributeError
            if issubclass(
                type(kwargs[key]), (BasedBase, Descriptor)
            ) or "BaseCollection" in [c.__name__ for c in type(kwargs[key]).__bases__]:
                self._borg.map.add_edge(self, kwargs[key])
                self._borg.map.reset_type(kwargs[key], "created_internal")
            addLoggedProp(
                self,
                key,
                self.__getter(key),
                self.__setter(key),
                get_id=key,
                my_self=self,
                test_class=BaseObj,
            )

    def _add_component(self, key: str, component: BV) -> None:
        """
        Dynamically add a component to the class. This is an internal method, though can be called remotely.
        The recommended alternative is to use typing, i.e.

        class Foo(Bar):
            def __init__(self, foo: Parameter, bar: Parameter):
                super(Foo, self).__init__(bar=bar)
                self._add_component("foo", foo)

        Goes to:
         class Foo(Bar):
            foo: ClassVar[Parameter]
            def __init__(self, foo: Parameter, bar: Parameter):
                super(Foo, self).__init__(bar=bar)
                self.foo = foo

        :param key: Name of component to be added
        :param component: Component to be added
        :return: None
        """
        self._kwargs[key] = component
        self._borg.map.add_edge(self, component)
        self._borg.map.reset_type(component, "created_internal")
        addLoggedProp(
            self,
            key,
            self.__getter(key),
            self.__setter(key),
            get_id=key,
            my_self=self,
            test_class=BaseObj,
        )

    def __setattr__(self, key: str, value: BV) -> None:
        # Assume that the annotation is a ClassVar
        old_obj = None
        if (
            hasattr(self.__class__, "__annotations__")
            and key in self.__class__.__annotations__
            and hasattr(self.__class__.__annotations__[key], "__args__")
            and issubclass(
                getattr(value, "__old_class__", value.__class__),
                self.__class__.__annotations__[key].__args__,
            )
        ):
            if issubclass(type(getattr(self, key, None)), (BasedBase, Descriptor)):
                old_obj = self.__getattribute__(key)
                self._borg.map.prune_vertex_from_edge(self, old_obj)
            self._add_component(key, value)
        else:
            if hasattr(self, key) and issubclass(type(value), (BasedBase, Descriptor)):
                old_obj = self.__getattribute__(key)
                self._borg.map.prune_vertex_from_edge(self, old_obj)
                self._borg.map.add_edge(self, value)
        super(BaseObj, self).__setattr__(key, value)
        # Update the interface bindings if something changed (BasedBase and Descriptor)
        if old_obj is not None:
            old_interface = getattr(self, "interface", None)
            if old_interface is not None:
                self.generate_bindings()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} `{getattr(self, 'name')}`"

    @staticmethod
    def __getter(key: str) -> Callable[[BV], BV]:
        def getter(obj: BV) -> BV:
            return obj._kwargs[key]

        return getter

    @staticmethod
    def __setter(key: str) -> Callable[[BV], None]:
        def setter(obj: BV, value: float) -> None:
            if issubclass(obj._kwargs[key].__class__, Descriptor) and not issubclass(
                value.__class__, Descriptor
            ):
                obj._kwargs[key].value = value
            else:
                obj._kwargs[key] = value

        return setter

    # @staticmethod
    # def __setter(key: str) -> Callable[[Union[B, V]], None]:
    #     def setter(obj: Union[V, B], value: float) -> None:
    #         if issubclass(obj._kwargs[key].__class__, Descriptor):
    #             if issubclass(obj._kwargs[key].__class__, Descriptor):
    #                 obj._kwargs[key] = value
    #             else:
    #                 obj._kwargs[key].value = value
    #         else:
    #             obj._kwargs[key] = value
    #
    #     return setter
