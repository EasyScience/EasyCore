#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import functools

from easyCore.Objects.ObjectClasses import BaseObj


class Model(BaseObj):
    def __init__(self, func, parameters, fn_kwargs):
        super().__init__()
        if not hasattr(func, "__call__"):
            f = functools.partial(value_wrapper, f)
        self._function = f
        self._parameters = parameters
