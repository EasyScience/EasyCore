#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

__author__ = 'github.com/wardsimon'

import numpy as np  # noqa: F401  This is used in the other codebases that uses easyCore
import pint

from easyCore.Objects.Borg import Borg

default_fitting_engine = 'lmfit'

ureg = pint.UnitRegistry()
borg = Borg()
borg.instantiate_stack()
borg.stack.enabled = False
