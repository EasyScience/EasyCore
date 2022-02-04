#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from easyCore import np
from typing import Union, List, _SpecialForm, _type_check, _GenericAlias

noneType = type(None)
Vector3Like = Union[List[float], np.ndarray]


@_SpecialForm
def ClassVar(self, parameters):
    """Special type construct to mark class variables.

    An annotation wrapped in ClassVar indicates that a given
    attribute is intended to be used as a class variable and
    should not be set on instances of that class. Usage::

      class Starship:
          stats: ClassVar[Dict[str, int]] = {} # class variable
          damage: int = 10                     # instance variable

    ClassVar accepts only types and cannot be further subscribed.

    Note that ClassVar is not a class itself, and should not
    be used with isinstance() or issubclass().
    """
    if not isinstance(parameters, tuple):
        parameters = (parameters,)
    item = _type_check(parameters[0], f"{self} accepts only single type.")
    created = _GenericAlias(self, (item,))
    setattr(created, "__creation_vars__", ())
    if len(parameters) > 1:
        setattr(created, "__creation_vars__", parameters[1])
    return created
