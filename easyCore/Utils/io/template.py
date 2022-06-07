from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import datetime
import json

from abc import abstractmethod
from importlib import import_module
from inspect import getfullargspec
from typing import (
    List,
    TYPE_CHECKING,
    Callable,
    Tuple,
    Any,
    Optional,
    Dict,
    MutableSequence,
)

from easyCore import np

if TYPE_CHECKING:
    from easyCore.Utils.typing import BV


class BaseEncoderDecoder:
    @abstractmethod
    def encode(self, obj: BV, skip: List[str] = []):
        pass

    @classmethod
    @abstractmethod
    def decode(cls, data) -> BV:
        pass

    @staticmethod
    def get_arg_spec(func: Callable) -> Tuple[Any, List[str]]:
        spec = getfullargspec(func)
        args = spec.args[1:]
        return spec, args

    @staticmethod
    def _encode_objs(obj, skip: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        A JSON serializable dict representation of an object.
        """
        if skip is None:
            skip = []
        elif isinstance(skip, str):
            skip = [skip]
        if not isinstance(skip, list):
            raise ValueError("Skip must be a list of strings.")

        d = {"@module": get_class_module(obj), "@class": obj.__class__.__name__}
        if kwargs.get("include_id", False):
            d["@id"] = obj._borg.map.convert_id_to_key(obj)
        try:
            parent_module = get_class_module(obj).split(".")[0]
            module_version = import_module(parent_module).__version__  # type: ignore
            d["@version"] = "{}".format(module_version)
        except (AttributeError, ImportError):
            d["@version"] = None  # type: ignore

        spec, args = BaseEncoderDecoder.get_arg_spec(obj.__class__.__init__)
        redirect = getattr(obj, "_REDIRECT", {})

        if hasattr(obj, "_convert_to_dict"):
            d = obj._convert_to_dict(d, BaseEncoderDecoder, skip=skip, **kwargs)

        for c in args:
            if c not in skip:
                try:
                    if c in redirect.keys():
                        a = redirect[c](obj)
                    else:
                        a = obj.__getattribute__(c)
                except AttributeError:
                    try:
                        a = obj.__getattribute__("_" + c)
                    except AttributeError:
                        err = True
                        if hasattr(obj, "kwargs"):
                            # type: ignore
                            option = getattr(obj, "kwargs")
                            if hasattr(option, c):
                                v = getattr(option, c)
                                delattr(option, c)
                                d.update(v)  # pylint: disable=E1101
                                err = False
                        if hasattr(obj, "_kwargs"):
                            # type: ignore
                            option = getattr(obj, "_kwargs")
                            if hasattr(option, c):
                                v = getattr(option, c)
                                delattr(option, c)
                                d.update(v)  # pylint: disable=E1101
                                err = False
                        if err:
                            raise NotImplementedError(
                                "Unable to automatically determine as_dict "
                                "format from class. MSONAble requires all "
                                "args to be present as either self.argname or "
                                "self._argname, and kwargs to be present under"
                                "a self.kwargs variable to automatically "
                                "determine the dict format. Alternatively, "
                                "you can implement both as_dict and from_dict."
                            )
                if a.__class__.__module__ != "builtins":  # strings have encode
                    d[c] = recursive_encoder(a, skip=skip, **kwargs)
                else:
                    d[c] = a
        return d

    @staticmethod
    def _convert_to_dict(obj: BV, skip: List[str] = [], **kwargs) -> dict:
        if isinstance(obj, datetime.datetime):
            return {
                "@module": "datetime",
                "@class": "datetime",
                "string": obj.__str__(),
            }
        if np is not None:
            if isinstance(obj, np.ndarray):
                if str(obj.dtype).startswith("complex"):
                    return {
                        "@module": "numpy",
                        "@class": "array",
                        "dtype": obj.dtype.__str__(),
                        "data": [obj.real.tolist(), obj.imag.tolist()],
                    }
                return {
                    "@module": "numpy",
                    "@class": "array",
                    "dtype": obj.dtype.__str__(),
                    "data": obj.tolist(),
                }
            if isinstance(obj, np.generic):
                return obj.item()
        try:
            json.JSONEncoder().default(obj)
        except TypeError:
            try:
                d = BaseEncoderDecoder._encode_objs(obj, skip, **kwargs)
                if "@module" not in d:
                    d["@module"] = "{}".format(obj.__class__.__module__)
                if "@class" not in d:
                    d["@class"] = "{}".format(obj.__class__.__name__)
                if "@version" not in d:
                    try:
                        parent_module = obj.__class__.__module__.split(".")[0]
                        module_version = import_module(parent_module).__version__  # type: ignore
                        d["@version"] = "{}".format(module_version)
                    except (AttributeError, ImportError):
                        d["@version"] = None
                return d
            except AttributeError:
                return obj

    @staticmethod
    def _convert_from_dict(d):
        """
        Recursive method to support decoding dicts and lists containing
        pymatgen objects.
        """
        T_ = type(d)
        if isinstance(d, dict):
            if "@module" in d and "@class" in d:
                modname = d["@module"]
                classname = d["@class"]
                # if classname in DictSerializer.REDIRECT.get(modname, {}):
                #     modname = DictSerializer.REDIRECT[modname][classname]["@module"]
                #     classname = DictSerializer.REDIRECT[modname][classname]["@class"]
            else:
                modname = None
                classname = None
            if modname and modname not in ["bson.objectid", "numpy"]:
                if modname == "datetime" and classname == "datetime":
                    try:
                        dt = datetime.datetime.strptime(
                            d["string"], "%Y-%m-%d %H:%M:%S.%f"
                        )
                    except ValueError:
                        dt = datetime.datetime.strptime(
                            d["string"], "%Y-%m-%d %H:%M:%S"
                        )
                    return dt

                mod = __import__(modname, globals(), locals(), [classname], 0)
                if hasattr(mod, classname):
                    cls_ = getattr(mod, classname)
                    data = {
                        k: BaseEncoderDecoder._convert_from_dict(v)
                        for k, v in d.items()
                        if not k.startswith("@")
                    }
                    return cls_(**data)
            elif np is not None and modname == "numpy" and classname == "array":
                if d["dtype"].startswith("complex"):
                    return np.array(
                        [r + i * 1j for r, i in zip(*d["data"])], dtype=d["dtype"]
                    )
                return np.array(d["data"], dtype=d["dtype"])

        if issubclass(T_, (list, MutableSequence)):
            return [BaseEncoderDecoder._convert_from_dict(x) for x in d]
        return d


def recursive_encoder(obj, skip: List[str] = [], **kwargs):
    T_ = type(obj)
    if issubclass(T_, (list, tuple, MutableSequence)):
        return [recursive_encoder(it, skip, **kwargs) for it in obj]
    if isinstance(obj, dict):
        return {kk: recursive_encoder(vv, skip, **kwargs) for kk, vv in obj.items()}
    if (
        hasattr(obj, "encode") and obj.__class__.__module__ != "builtins"
    ):  # strings have encode
        return BaseEncoderDecoder._convert_to_dict(obj, skip, **kwargs)
    return obj


def get_class_module(obj):
    """
    Returns the REAL module of the class of the object.
    """
    c = getattr(obj, "__old_class__", obj.__class__)
    return c.__module__
