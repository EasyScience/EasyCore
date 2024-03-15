#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import numpy as np
import pytest

from easyCore.models.polynomial import Line
from easyCore.models.polynomial import Polynomial
from easyCore.Objects.Variable import Parameter

line_test_cases = ((1, 2), (-1, -2), (0.72, 6.48))
poly_test_cases = (
    (1.,),
    (
        1.,
        2.,
    ),
    (1., 2., 3.),
    (-1., -2., -3.),
    (0.72, 6.48, -0.48),
)


@pytest.mark.parametrize("m, c", line_test_cases)
def test_Line_pars(m, c):
    line = Line(m, c)

    assert line.m.raw_value == m
    assert line.c.raw_value == c

    x = np.linspace(0, 10, 100)
    y = line.m.raw_value * x + line.c.raw_value
    assert np.allclose(line(x), y)


@pytest.mark.parametrize("m, c", line_test_cases)
def test_Line_constructor(m, c):
    m_ = Parameter("m", m)
    c_ = Parameter("c", c)
    line = Line(m_, c_)

    assert line.m.raw_value == m
    assert line.c.raw_value == c

    x = np.linspace(0, 10, 100)
    y = line.m.raw_value * x + line.c.raw_value
    assert np.allclose(line(x), y)


@pytest.mark.parametrize("coo", poly_test_cases)
def test_Polynomial_pars(coo):
    poly = Polynomial(coefficients=coo)

    vals = {coo.raw_value for coo in poly.coefficients}
    assert len(vals.difference(set(coo))) == 0

    x = np.linspace(0, 10, 100)
    y = np.polyval(coo, x)
    assert np.allclose(poly(x), y)
