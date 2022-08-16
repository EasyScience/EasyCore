#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

import sys

from typing import Callable, List, Any
from functools import wraps

from easyCore import borg

from easyCore.Utils.Hugger.Hugger import Store, PatcherFactory
import param


class LoggedProperty(property):
    """
    Pump up python properties. In this case we can see who has called this property and
    then do something if a criteria is met. In this case if the caller is not a member of
    the `BaseObj` class. Note that all high level `easyCore` objects should be built from
    `BaseObj`.
    """

    _borg = borg

    def __init__(self, *args, get_id=None, my_self=None, test_class=None, **kwargs):
        super(LoggedProperty, self).__init__(*args, **kwargs)
        self._get_id = get_id
        self._my_self = my_self
        self.test_class = test_class

    @staticmethod
    def _caller_class(test_class, skip: int = 1):
        def stack_(frame):
            frame_list = []
            while frame:
                frame_list.append(frame)
                frame = frame.f_back
            return frame_list

        stack: List[Any] = stack_(sys._getframe(1))
        start = 0 + skip
        if len(stack) < start + 1:
            return ""
        parent_frame = stack[start]
        test = False
        if "self" in parent_frame.f_locals:
            test = issubclass(parent_frame.f_locals["self"].__class__, test_class)
        return test

    def __get__(self, instance, owner=None):
        if not borg.script.enabled:
            return super(LoggedProperty, self).__get__(instance, owner)
        test = self._caller_class(self.test_class)
        res = super(LoggedProperty, self).__get__(instance, owner)

        def result_item(item_to_be_resulted):
            if item_to_be_resulted is None:
                return None
            if borg.map.is_known(item_to_be_resulted):
                borg.map.change_type(item_to_be_resulted, "returned")
            else:
                borg.map.add_vertex(item_to_be_resulted, obj_type="returned")

        if not test and self._get_id is not None and self._my_self is not None:
            if not isinstance(res, list):
                result_item(res)
            else:
                for item in res:
                    result_item(item)
            Store().append_log(self.makeEntry("get", res))
            if borg.debug:  # noqa: S1006
                print(
                    f"I'm {self._my_self} and {self._get_id} has been called from the outside!"
                )
        return res

    def __set__(self, instance, value):
        if not borg.script.enabled:
            return super().__set__(instance, value)
        test = self._caller_class(self.test_class)
        if not test and self._get_id is not None and self._my_self is not None:
            Store().append_log(self.makeEntry("set", value))
            if borg.debug:  # noqa: S1006
                print(
                    f"I'm {self._my_self} and {self._get_id} has been set to {value} from the outside!"
                )
        return super().__set__(instance, value)

    def makeEntry(self, log_type, returns, *args, **kwargs) -> str:
        temp = ""
        if returns is None:
            returns = []
        if not isinstance(returns, list):
            returns = [returns]
        if log_type == "get":
            for var in returns:
                if borg.map.convert_id_to_key(var) in borg.map.returned_objs:
                    index = borg.map.returned_objs.index(
                        borg.map.convert_id_to_key(var)
                    )
                    temp += f"{Store().var_ident}{index}, "
            if len(returns) > 0:
                temp = temp[:-2]
                temp += " = "
            if borg.map.convert_id_to_key(self._my_self) in borg.map.created_objs:
                # for edge in route[::-1]:
                index = borg.map.created_objs.index(
                    borg.map.convert_id_to_key(self._my_self)
                )
                temp += (
                    f"{self._my_self.__class__.__name__.lower()}_{index}.{self._get_id}"
                )
            if borg.map.convert_id(self._my_self) in borg.map.created_internal:
                # We now have to trace....
                route = borg.map.reverse_route(self._my_self)  # noqa: F841
                index = borg.map.created_objs.index(
                    borg.map.convert_id_to_key(self._my_self)
                )
                temp += (
                    f"{self._my_self.__class__.__name__.lower()}_{index}.{self._get_id}"
                )
        elif log_type == "set":
            if borg.map.convert_id_to_key(self._my_self) in borg.map.created_objs:
                index = borg.map.created_objs.index(
                    borg.map.convert_id_to_key(self._my_self)
                )
                temp += f"{self._my_self.__class__.__name__.lower()}_{index}.{self._get_id} = "
            args = args[1:]
            for var in args:
                if borg.map.convert_id_to_key(var) in borg.map.argument_objs:
                    index = borg.map.argument_objs.index(
                        borg.map.convert_id_to_key(var)
                    )
                    temp += f"{Store().var_ident}{index}"
                elif borg.map.convert_id_to_key(var) in borg.map.returned_objs:
                    index = borg.map.returned_objs.index(
                        borg.map.convert_id_to_key(var)
                    )
                    temp += f"{Store().var_ident}{index}"
                elif borg.map.convert_id_to_key(var) in borg.map.created_objs:
                    index = borg.map.created_objs.index(borg.map.convert_id_to_key(var))
                    temp += f"{self._my_self.__class__.__name__.lower()}_{index}"
                else:
                    if isinstance(var, str):
                        var = '"' + var + '"'
                    temp += f"{var}"
        else:
            print(f"{log_type} is not implemented yet. Sorry")
        temp += "\n"
        return temp


class LoggedParamProperty(param.Parameter):
    """
    Pump up python properties. In this case we can see who has called this property and
    then do something if a criteria is met. In this case if the caller is not a member of
    the `BaseObj` class. Note that all high level `easyCore` objects should be built from
    `BaseObj`.
    """

    _borg = borg

    # __slots__ = ["_my_self", "_get_id", "test_class", "_setter", "_getter"]

    def __init__(self, *args, get_id=None, my_self=None, test_class=None, **kwargs):
        super(LoggedParamProperty, self).__init__(my_self._kwargs[get_id])
        # self._getter = args[0]
        # self._setter = args[1]
        # self._get_id = get_id
        # self._my_self = my_self
        # self.test_class = test_class

    def __get__(self, instance, owner):
        return super().__get__(instance, owner)

    @param.parameterized.instance_descriptor
    def __set__(self, obj, val):
        """
        Set the value for this Parameter.

        If called for a Parameterized class, set that class's
        value (i.e. set this Parameter object's 'default' attribute).

        If called for a Parameterized instance, set the value of
        this Parameter on that instance (i.e. in the instance's
        __dict__, under the parameter's internal_name).

        If the Parameter's constant attribute is True, only allows
        the value to be set for a Parameterized class or on
        uninitialized Parameterized instances.

        If the Parameter's readonly attribute is True, only allows the
        value to be specified in the Parameter declaration inside the
        Parameterized source code. A read-only parameter also
        cannot be set on a Parameterized class.

        Note that until we support some form of read-only
        object, it is still possible to change the attributes of the
        object stored in a constant or read-only Parameter (e.g. one
        item in a list).
        """

        # PARAM2_DEPRECATION: For Python 2 compatibility only;
        # Deprecated Number set_hook called here to avoid duplicating setter
        if hasattr(self, 'set_hook'):
            val = self.set_hook(obj, val)

        self._validate(val)

        _old = NotImplemented
        # obj can be None if __set__ is called for a Parameterized class
        if self.constant or self.readonly:
            if self.readonly:
                raise TypeError("Read-only parameter '%s' cannot be modified" % self.name)
            elif obj is None:
                _old = self.default
                self.default = val
            elif not obj.initialized:
                _old = obj.__dict__.get(self._internal_name, self.default)
                obj.__dict__[self._internal_name] = val
            else:
                _old = obj.__dict__.get(self._internal_name, self.default)
                if val is not _old:
                    raise TypeError("Constant parameter '%s' cannot be modified"%self.name)
        else:
            if obj is None:
                _old = self.default
                self.default = val
            else:
                _old = obj.__dict__.get(self._internal_name, self.default)
                from easyCore.Objects.core import ComponentSerializer
                if issubclass(obj.__class__, ComponentSerializer) and not issubclass(val.__class__, ComponentSerializer):
                    if self._internal_name in obj.__dict__.keys():
                        _old = obj.__dict__[self._internal_name].raw_value
                        obj.__dict__[self._internal_name].value = val
                    else:
                        old_value = _old.raw_value
                        _old.value = val
                        obj.__dict__[self._internal_name] = _old
                        _old = old_value
                else:
                    obj.__dict__[self._internal_name] = val

        self._post_setter(obj, val)

        if obj is not None:
            if not getattr(obj, 'initialized', False):
                return
            obj.param._update_deps(self.name)

        if obj is None:
            watchers = self.watchers.get("value")
        elif hasattr(obj, '_param_watchers') and self.name in obj._param_watchers:
            watchers = obj._param_watchers[self.name].get('value')
            if watchers is None:
                watchers = self.watchers.get("value")
        else:
            watchers = None

        obj = self.owner if obj is None else obj

        if obj is None or not watchers:
            return

        event = param.parameterized.Event(what='value', name=self.name, obj=obj, cls=self.owner,
                      old=_old, new=val, type=None)

        # Copy watchers here since they may be modified inplace during iteration
        for watcher in sorted(watchers, key=lambda w: w.precedence):
            obj.param._call_watcher(watcher, event)
        if not obj.param._BATCH_WATCH:
            obj.param._batch_call_watchers()
    #
    # @staticmethod
    # def _caller_class(test_class, skip: int = 1):
    #     def stack_(frame):
    #         frame_list = []
    #         while frame:
    #             frame_list.append(frame)
    #             frame = frame.f_back
    #         return frame_list
    #
    #     stack: List[Any] = stack_(sys._getframe(1))
    #     start = 0 + skip
    #     if len(stack) < start + 1:
    #         return ""
    #     parent_frame = stack[start]
    #     test = False
    #     if "self" in parent_frame.f_locals:
    #         test = issubclass(parent_frame.f_locals["self"].__class__, test_class)
    # #     return test
    #
    # def __get__(self, instance, owner=None):
    #     res = super(LoggedParamProperty, self).__get__(instance, owner)
    #     if not borg.script.enabled:
    #         return res
    #     test = self._caller_class(self.test_class)
    #
    #     def result_item(item_to_be_resulted):
    #         if item_to_be_resulted is None:
    #             return None
    #         if borg.map.is_known(item_to_be_resulted):
    #             borg.map.change_type(item_to_be_resulted, "returned")
    #         else:
    #             borg.map.add_vertex(item_to_be_resulted, obj_type="returned")
    #
    #     if not test and self._get_id is not None and self._my_self is not None:
    #         if not isinstance(res, list):
    #             result_item(res)
    #         else:
    #             for item in res:
    #                 result_item(item)
    #         Store().append_log(self.makeEntry("get", res))
    #         if borg.debug:  # noqa: S1006
    #             print(
    #                 f"I'm {self._my_self} and {self._get_id} has been called from the outside!"
    #             )
    #     return res
    #
    #
    #
    # def __set__(self, instance, value):
    #     # param set
    #     self._setter(instance, value)
    #     super().__set__(instance, self._getter(instance))
    #     if not borg.script.enabled:
    #         return
    #     test = self._caller_class(self.test_class)
    #     if not test and self._get_id is not None and self._my_self is not None:
    #         Store().append_log(self.makeEntry("set", value))
    #         if borg.debug:  # noqa: S1006
    #             print(
    #                 f"I'm {self._my_self} and {self._get_id} has been set to {value} from the outside!"
    #             )
    #
    # def makeEntry(self, log_type, returns, *args, **kwargs) -> str:
    #     temp = ""
    #     if returns is None:
    #         returns = []
    #     if not isinstance(returns, list):
    #         returns = [returns]
    #     if log_type == "get":
    #         for var in returns:
    #             if borg.map.convert_id_to_key(var) in borg.map.returned_objs:
    #                 index = borg.map.returned_objs.index(
    #                     borg.map.convert_id_to_key(var)
    #                 )
    #                 temp += f"{Store().var_ident}{index}, "
    #         if len(returns) > 0:
    #             temp = temp[:-2]
    #             temp += " = "
    #         if borg.map.convert_id_to_key(self._my_self) in borg.map.created_objs:
    #             # for edge in route[::-1]:
    #             index = borg.map.created_objs.index(
    #                 borg.map.convert_id_to_key(self._my_self)
    #             )
    #             temp += (
    #                 f"{self._my_self.__class__.__name__.lower()}_{index}.{self._get_id}"
    #             )
    #         if borg.map.convert_id(self._my_self) in borg.map.created_internal:
    #             # We now have to trace....
    #             route = borg.map.reverse_route(self._my_self)  # noqa: F841
    #             index = borg.map.created_objs.index(
    #                 borg.map.convert_id_to_key(self._my_self)
    #             )
    #             temp += (
    #                 f"{self._my_self.__class__.__name__.lower()}_{index}.{self._get_id}"
    #             )
    #     elif log_type == "set":
    #         if borg.map.convert_id_to_key(self._my_self) in borg.map.created_objs:
    #             index = borg.map.created_objs.index(
    #                 borg.map.convert_id_to_key(self._my_self)
    #             )
    #             temp += f"{self._my_self.__class__.__name__.lower()}_{index}.{self._get_id} = "
    #         args = args[1:]
    #         for var in args:
    #             if borg.map.convert_id_to_key(var) in borg.map.argument_objs:
    #                 index = borg.map.argument_objs.index(
    #                     borg.map.convert_id_to_key(var)
    #                 )
    #                 temp += f"{Store().var_ident}{index}"
    #             elif borg.map.convert_id_to_key(var) in borg.map.returned_objs:
    #                 index = borg.map.returned_objs.index(
    #                     borg.map.convert_id_to_key(var)
    #                 )
    #                 temp += f"{Store().var_ident}{index}"
    #             elif borg.map.convert_id_to_key(var) in borg.map.created_objs:
    #                 index = borg.map.created_objs.index(borg.map.convert_id_to_key(var))
    #                 temp += f"{self._my_self.__class__.__name__.lower()}_{index}"
    #             else:
    #                 if isinstance(var, str):
    #                     var = '"' + var + '"'
    #                 temp += f"{var}"
    #     else:
    #         print(f"{log_type} is not implemented yet. Sorry")
    #     temp += "\n"
    #     return temp


class PropertyHugger(PatcherFactory):
    # Properties are immutable, so need to be set at the parent level. However unlike `FunctionHugger` we can't traverse
    # the stack to get the parent. So, it and it's name has to be set at initialization. Boo!

    _borg = borg

    def __init__(self, klass, prop_name):
        super().__init__()
        self.klass = klass
        if isinstance(prop_name, tuple):
            self.prop_name = prop_name[0]
            self.property = prop_name[1]
        else:
            self.prop_name = prop_name
            self.property = klass.__dict__.get(prop_name)
        self.__patch_ref = {
            "fget": {"old": self.property.fget, "patcher": self.patch_get},
            "fset": {"old": self.property.fset, "patcher": self.patch_set},
            "fdel": {"old": self.property.fdel, "patcher": self.patch_del},
        }

    def patch(self):
        option = {}
        for key, item in self.__patch_ref.items():
            func = getattr(self.property, key)
            if func is not None:
                if borg.debug:
                    print(f"Patching property {self.klass.__name__}.{self.prop_name}")
                patch_function: Callable = item.get("patcher")
                new_func = patch_function(func)
                option[key] = new_func
        setattr(self.klass, self.prop_name, property(**option))

    def restore(self):
        if borg.debug:
            print(f"Restoring property {self.klass.__name__}.{self.prop_name}")
        setattr(self.klass, self.prop_name, self.property)

    def patch_get(self, func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            if borg.debug:
                print(
                    f"{self.klass.__name__}.{self.prop_name} has been called with {args[1:]}, {kwargs}"
                )
            res = func(*args, **kwargs)
            self._append_args(*args, **kwargs)
            self._append_result(res)
            self._append_log(self.makeEntry("get", res, *args, **kwargs))
            return res

        return inner

    def patch_set(self, func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            if borg.debug:
                print(
                    f"{self.klass.__name__}.{self.prop_name} has been set with {args[1:]}, {kwargs}"
                )
            self._append_args(*args, **kwargs)
            self._append_log(self.makeEntry("set", None, *args, **kwargs))
            return func(*args, **kwargs)

        return inner

    def patch_del(self, func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            if borg.debug:
                print(f"{self.klass.__name__}.{self.prop_name} has been deleted.")
            self._append_log(self.makeEntry("del", None, *args, **kwargs))
            return func(*args, **kwargs)

        return inner

    def makeEntry(self, log_type, returns, *args, **kwargs) -> str:
        temp = ""
        if returns is None:
            returns = []
        if not isinstance(returns, list):
            returns = [returns]
        if log_type == "get":
            for var in returns:
                if self._in_list("return_list", var):
                    index = self._get_position("return_list", var)
                    temp += f"{self._store.var_ident}{index}, "
            if len(returns) > 0:
                temp = temp[:-2]
                temp += " = "
            if self._in_list("create_list", args[0]):
                index = self._get_position("create_list", args[0])
                temp += f"{self.klass.__name__.lower()}_{index}.{self.prop_name}"
        elif log_type == "set":
            if self._in_list("create_list", args[0]):
                index = self._get_position("create_list", args[0])
                temp += f"{self.klass.__name__.lower()}_{index}.{self.prop_name} = "
            args = args[1:]
            for var in args:
                if self._in_list("input_list", var):
                    index = self._get_position("input_list", var)
                    temp += f"{self._store.var_ident}{index}"
                elif self._in_list("return_list", var):
                    index = self._get_position("return_list", var)
                    temp += f"{self._store.var_ident}{index}"
                elif self._in_list("create_list", var):
                    index = self._get_position("create_list", var)
                    temp += f"{self.klass.__name__.lower()}_{index}"
                else:
                    if isinstance(var, str):
                        var = '"' + var + '"'
                    temp += f"{var}"
        else:
            print(f"{log_type} is not implemented yet. Sorry")
        temp += "\n"
        return temp
