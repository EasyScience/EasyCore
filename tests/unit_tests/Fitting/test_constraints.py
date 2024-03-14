__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

from typing import List
from typing import Tuple

import pytest

from easyCore.Fitting.Constraints import NumericConstraint
from easyCore.Fitting.Constraints import ObjConstraint
from easyCore.Objects.Variable import Parameter


@pytest.fixture
def twoPars() -> Tuple[List[Parameter], List[int]]:
    return [Parameter("a", 1), Parameter("b", 2)], [1, 2]


@pytest.fixture
def threePars(twoPars) -> Tuple[List[Parameter], List[int]]:
    ps, vs = twoPars
    ps.append(Parameter("c", 3))
    vs.append(3)
    return ps, vs


def test_NumericConstraints_Equals(twoPars):

    value = 1
    c = NumericConstraint(twoPars[0][0], "==", value)
    c()
    assert twoPars[0][0].raw_value == twoPars[1][0]
    c = NumericConstraint(twoPars[0][1], "==", value)
    c()
    assert twoPars[0][1].raw_value == value


def test_NumericConstraints_Greater(twoPars):
    value = 1.5
    c = NumericConstraint(twoPars[0][0], ">", value)
    c()
    assert twoPars[0][0].raw_value == value
    c = NumericConstraint(twoPars[0][1], ">", value)
    c()
    assert twoPars[0][1].raw_value == twoPars[1][1]


def test_NumericConstraints_Less(twoPars):
    value = 1.5
    c = NumericConstraint(twoPars[0][0], "<", value)
    c()
    assert twoPars[0][0].raw_value == twoPars[1][0]
    c = NumericConstraint(twoPars[0][1], "<", value)
    c()
    assert twoPars[0][1].raw_value == value


@pytest.mark.parametrize("operator", [None, 1, 2, 3, 4.5])
def test_ObjConstraintMultiply(twoPars, operator):
    if operator is None:
        operator = 1
        operator_str = ""
    else:
        operator_str = f"{operator}*"
    c = ObjConstraint(twoPars[0][0], operator_str, twoPars[0][1])
    c()
    assert twoPars[0][0].raw_value == operator * twoPars[1][1]


@pytest.mark.parametrize("operator", [1, 2, 3, 4.5])
def test_ObjConstraintDivide(twoPars, operator):
    operator_str = f"{operator}/"
    c = ObjConstraint(twoPars[0][0], operator_str, twoPars[0][1])
    c()
    assert twoPars[0][0].raw_value == operator / twoPars[1][1]


def test_ObjConstraint_Multiple(threePars):

    p0 = threePars[0][0]
    p1 = threePars[0][1]
    p2 = threePars[0][2]

    value = 1.5

    p0.user_constraints["num_1"] = ObjConstraint(p1, "", p0)
    p0.user_constraints["num_2"] = ObjConstraint(p2, "", p0)

    p0.value = value
    assert p0.raw_value == value
    assert p1.raw_value == value
    assert p2.raw_value == value


def test_ConstraintEnable_Disable(twoPars):

    assert twoPars[0][0].enabled
    assert twoPars[0][1].enabled

    c = ObjConstraint(twoPars[0][0], "", twoPars[0][1])
    twoPars[0][0].user_constraints["num_1"] = c

    assert c.enabled
    assert twoPars[0][1].enabled
    assert not twoPars[0][0].enabled

    c.enabled = False
    assert not c.enabled
    assert twoPars[0][1].enabled
    assert twoPars[0][0].enabled

    c.enabled = True
    assert c.enabled
    assert twoPars[0][1].enabled
    assert not twoPars[0][0].enabled
