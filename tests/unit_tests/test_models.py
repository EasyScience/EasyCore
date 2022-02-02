#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import functools
import pickle
from typing import ClassVar

from easyCore import np
from easyCore.Objects.ObjectClasses import BaseObj, Parameter
from easyCore.optimization.model import Model, EasyModel, CompositeModel


def line_func(x, m=1, c=0):
    return m * x + c


def fn_wrapper(func):
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        for name in list(obj.__annotations__.keys()):
            func.__globals__["_" + name] = getattr(obj, name).raw_value
        return func(obj, *args, **kwargs)
    return wrapper


class Line(BaseObj):

    m: ClassVar[Parameter]
    c: ClassVar[Parameter]

    def __init__(self, m: Parameter, c: Parameter):
        super(Line, self).__init__('line', m=m, c=c)

    @classmethod
    def from_pars(cls, m, c):
        m = Parameter('m', m)
        c = Parameter('c', c)
        return cls(m=m, c=c)

    @fn_wrapper
    def func(self, x, *args, **kwargs):
        return _m * x + _c


def test_model_fn():
    model = Model(line_func)
    x = np.linspace(0, 10, 100)

    m = 2
    c = 1.5

    assert np.allclose(model(x, m, c), m * x + c)
    assert np.allclose(model(x, m=m, c=c), m * x + c)
    assert model.count == 2
    assert model.runtime > 0
    assert model.function == line_func

    dump = pickle.dumps(model)
    model2 = pickle.loads(dump)


def test_model_numeric():
    num = 5

    model = Model(num)
    x = np.linspace(0, 10, 100)

    assert model(x) == num
    assert model.count == 1
    assert model.runtime > 0

    dump = pickle.dumps(model)
    model2 = pickle.loads(dump)


def test_easyModel():
    line = Line.from_pars(m=1, c=0)

    model = EasyModel(line, 'func')
    x = np.linspace(0, 10, 100)
    m = 2
    c = 1.5

    def runner(_model):
        assert np.allclose(_model(x, m, c), m * x + c)
        assert np.allclose(_model(x, m=m, c=c), m * x + c)
        # assert _model.count == 2
        assert _model.runtime > 0

    runner(model)
    dump = pickle.dumps(model)
    runner(pickle.loads(dump))


def test_compositeModel_numeric_1():

    model0 = Model(line_func)
    x = np.linspace(0, 10, 100)

    m = 2
    c = 1.5
    offset = 1

    model = model0 + offset

    assert np.allclose(model(x, m, c), m * x + c + offset)
    assert np.allclose(model(x, m=m, c=c), m * x + c + offset)
    assert model.count == 2
    assert model.runtime > 0

    dump = pickle.dumps(model)
    model2 = pickle.loads(dump)


def test_compositeModel_numeric_2():
    model0 = Model(line_func)
    x = np.linspace(0, 10, 100)

    m = 2
    c = 1.5
    offset = 1

    model = model0 + Model(offset)

    assert np.allclose(model(x, m, c), m * x + c + offset)
    assert np.allclose(model(x, m=m, c=c), m * x + c + offset)
    assert model.count == 2
    assert model.runtime > 0

    dump = pickle.dumps(model)
    model2 = pickle.loads(dump)

def test_compositeModel_model():

    line0 = Line.from_pars(m=1, c=0)
    line1 = Line.from_pars(m=1.5, c=3)

    model0 = EasyModel(line0, 'func')
    model1 = EasyModel(line1, 'func')

    x = np.linspace(0, 10, 100)
    m1 = 2
    c1 = 1.5
    m2 = 2.3
    c2 = 1.6

    x = np.linspace(0, 10, 100)

    model = model0 + model1
    expected = m1 * x + c1 + m2 * x + c2

    assert np.allclose(model(x, m1, c1, m2, c2), expected)
    assert model.count == 2
    assert model.runtime > 0

    dump = pickle.dumps(model)
    model2 = pickle.loads(dump)