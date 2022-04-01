#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from typing import List, Tuple, TYPE_CHECKING, TypeVar, Union

from easyCore import borg
from easyCore.Utils.Hugger.Property import LoggedProperty

if TYPE_CHECKING:
    from easyCore.Utils.typing import B, BV

def addLoggedProp(inst: BV, name: str, *args, **kwargs) -> None:
    cls = type(inst)
    annotations = getattr(cls, "__annotations__", False)
    if not hasattr(cls, "__perinstance"):
        cls = type(cls.__name__, (cls,), {"__module__": inst.__module__})
        cls.__perinstance = True
        if annotations:
            cls.__annotations__ = annotations
        inst.__old_class__ = inst.__class__
        inst.__class__ = cls
    setattr(cls, name, LoggedProperty(*args, **kwargs))


def addProp(inst: BV, name: str, *args, **kwargs) -> None:
    cls = type(inst)
    annotations = getattr(cls, "__annotations__", False)
    if not hasattr(cls, "__perinstance"):
        cls = type(cls.__name__, (cls,), {"__module__": __name__})
        cls.__perinstance = True
        if annotations:
            cls.__annotations__ = annotations
        inst.__old_class__ = inst.__class__
        inst.__class__ = cls

    setattr(cls, name, property(*args, **kwargs))


def removeProp(inst: BV, name: str) ->None:
    cls = type(inst)
    if not hasattr(cls, "__perinstance"):
        cls = type(cls.__name__, (cls,), {"__module__": __name__})
        cls.__perinstance = True
        inst.__old_class__ = inst.__class__
        inst.__class__ = cls
    delattr(cls, name)


def generatePath(model_obj: B, skip_first: bool = False) -> Tuple[List[int], List[str]]:
    pars = model_obj.get_parameters()
    start_idx = 0 + int(skip_first)
    ids = []
    names = []
    model_id = borg.map.convert_id(model_obj)
    for par in pars:
        elem = borg.map.convert_id(par)
        route = borg.map.reverse_route(elem, model_id)
        objs = [getattr(borg.map.get_item_by_key(r), "name") for r in route]
        objs.reverse()
        names.append(".".join(objs[start_idx:]))
        ids.append(elem.int)
    return ids, names
