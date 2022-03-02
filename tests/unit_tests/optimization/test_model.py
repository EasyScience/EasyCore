#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"


import numpy as np
from easyCore.optimization._model import Model, EasyModel, CompositeModel

x = np.linspace(0, 1, 100)


def test_Model():

    f = np.cos

    m = Model(f)
    assert np.allclose(m(x), np.cos(x))
    assert len(m.parameters) == 0
    assert m.parameters == {}
    assert m.function == f
    assert m.count == 1
    assert m.runtime > 0

    m.reset_count()
    assert m.count == 0
    assert m.runtime == 0


def test_model_functions():
    a = Model(np.sin)
    b = Model(np.cos)

    C = a + b
    assert np.allclose(C(x), np.sin(x) + np.cos(x))
    C = a - b
    assert np.allclose(C(x), np.sin(x) - np.cos(x))
    C = a * b
    assert np.allclose(C(x), np.sin(x) * np.cos(x))
    C = a / b
    assert np.allclose(C(x), np.sin(x) / np.cos(x))


def test_easyModel():
    from easyCore.models.polynomial import Line

    l = Line.from_pars(0.2, 0.6)

    m = EasyModel(l)
    assert np.allclose(m(x), l(x))
    assert len(m.parameters) == 2
    assert "m" in m.parameters.keys()
    assert "c" in m.parameters.keys()
    assert m.count == 1
    assert m.runtime > 0

    m.reset_count()
    assert m.count == 0
    assert m.runtime == 0


def test_easyModel_model_functions():
    from easyCore.models.polynomial import Line

    l = Line.from_pars(0.2, 0.6)
    m = EasyModel(l)
    a = Model(np.sin)

    C = m + a
    assert np.allclose(C(x), np.sin(x) + l(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0
    C = m - a
    assert np.allclose(C(x), np.sin(x) - l(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0
    C = m * a
    assert np.allclose(C(x), np.sin(x) * l(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0
    C = m / a
    assert np.allclose(C(x), np.sin(x) / l(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0

    C = a + m
    assert np.allclose(C(x), l(x) + np.sin(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0
    C = a - m
    assert np.allclose(C(x), l(x) - np.sin(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0
    C = a * m
    assert np.allclose(C(x), l(x) * np.sin(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0
    C = a / m
    assert np.allclose(C(x), l(x) / np.sin(x))
    assert len(C.parameters) == 2
    assert "m" in C.parameters.keys()
    assert "c" in C.parameters.keys()
    assert C.count == 1
    assert C.runtime > 0


def test_easyModel_model_functions():
    from easyCore.models.polynomial import Line, Polynomial

    l = Line.from_pars(0.2, 0.6)
    m = EasyModel(l)
    p = Polynomial.from_pars([1, 2, 3])
    a = EasyModel(p)

    def do_test(C_, op_res):
        assert np.allclose(C_(x), op_res)
        assert len(C_.parameters) == 5
        assert "m" in C_.parameters.keys()
        assert "c" in C_.parameters.keys()
        assert "c0" in C_.parameters.keys()
        assert "c1" in C_.parameters.keys()
        assert "c2" in C_.parameters.keys()
        assert C_.count == 1
        assert C_.runtime > 0

    C = m + a
    do_test(C, l(x) + p(x))

    C = m - a
    do_test(C, l(x) - p(x))

    C = m * a
    do_test(C, l(x) * p(x))

    C = m / a
    do_test(C, l(x) / p(x))

    C = a + m
    do_test(C, p(x) + l(x))

    C = a - m
    do_test(C, p(x) - l(x))

    C = a * m
    do_test(C, p(x) * l(x))

    C = a / m
    do_test(C, p(x) / l(x))


def test_model_kwargs():

    m = Model(np.sum, parameters={}, fn_kwargs={"axis": 1})

    xx = np.arange(10).reshape(2, 5)

    assert np.allclose(m(xx), np.sum(xx, axis=1))
    m.fn_kwargs = {"axis": 0}
    assert np.allclose(m(xx), np.sum(xx, axis=0))
    assert len(m.parameters) == 0
    assert m.count == 2
    assert m.runtime > 0
