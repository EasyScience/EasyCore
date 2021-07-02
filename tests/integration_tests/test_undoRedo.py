#  SPDX-FileCopyrightText: 2021 European Spallation Source <info@ess.eu>
#  SPDX-License-Identifier: BSD-3-Clause

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numpy as np
import pytest
from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
from easyCore.Objects.Groups import BaseCollection
import math

def createSingleObjs(idx):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    reps = math.floor(idx/len(alphabet)) + 1
    name = alphabet[idx % len(alphabet)] * reps
    if idx % 2:
        return Parameter(name, idx)
    else:
        return Descriptor(name, idx)


def createParam(option):
    return pytest.param(option, id=option[0])


def doUndoRedo(obj, attr, future, additional=''):
    from easyCore import borg

    borg.stack.enabled = True
    e = False

    def getter(_obj, _attr):
        value = getattr(_obj, _attr)
        if additional:
            value = getattr(value, additional)
        return value

    try:
        previous = getter(obj, attr)
        setattr(obj, attr, future)
        assert getter(obj, attr) == future
        assert borg.stack.canUndo()
        borg.stack.undo()
        assert getter(obj, attr) == previous
        assert borg.stack.canRedo()
        borg.stack.redo()
        assert getter(obj, attr) == future
    except Exception as err:
        e = err
    finally:
        borg.stack.enabled = False
    return e

@pytest.mark.parametrize('test', [createParam(option) for option in [('value', 500), ('error', 5), ('enabled', False),
                                                                     ('unit', 'meter / second'), ('display_name', 'boom'),
                                                                     ('fixed', False), ('max', 505), ('min', -1)]])
@pytest.mark.parametrize('idx', [pytest.param(0, id='Descriptor'), pytest.param(1, id='Parameter')])
def test_SinglesUndoRedo(idx, test):

    obj = createSingleObjs(idx)
    attr = test[0]
    value = test[1]

    if not hasattr(obj, attr):
        pytest.skip(f'Not applicable: {obj} does not have field {attr}')
    e = doUndoRedo(obj, attr, value)
    if e:
        raise e


def test_BaseObjUndoRedo():
    objs = {obj.name: obj for obj in [createSingleObjs(idx) for idx in range(5)]}
    name = 'test'
    obj = BaseObj(name, **objs)
    name2 = 'best'

    # Test name
    # assert not doUndoRedo(obj, 'name', name2)

    # Test setting value
    for b_obj in objs.values():
        e = doUndoRedo(obj, b_obj.name, b_obj.raw_value + 1, 'raw_value')
        if e:
            raise e


def test_BaseCollectionUndoRedo():
    objs = [createSingleObjs(idx) for idx in range(5)]
    name = 'test'
    obj = BaseCollection(name, *objs)
    name2 = 'best'

    # assert not doUndoRedo(obj, 'name', name2)

    from easyCore import borg
    borg.stack.enabled = True

    original_length = len(obj)
    p = Parameter('slip_in', 50)
    idx = 2
    obj.insert(idx, p)
    assert len(obj) == original_length + 1
    objs.insert(idx, p)
    for item, obj_r in zip(obj, objs):
        assert item == obj_r

    # Test inserting items
    borg.stack.undo()
    assert len(obj) == original_length
    _ = objs.pop(idx)
    for item, obj_r in zip(obj, objs):
        assert item == obj_r
    borg.stack.redo()
    assert len(obj) == original_length + 1
    objs.insert(idx, p)
    for item, obj_r in zip(obj, objs):
        assert item == obj_r

    # Test Del Items
    del obj[idx]
    del objs[idx]
    assert len(obj) == original_length
    for item, obj_r in zip(obj, objs):
        assert item == obj_r
    borg.stack.undo()
    assert len(obj) == original_length + 1
    objs.insert(idx, p)
    for item, obj_r in zip(obj, objs):
        assert item == obj_r
    del objs[idx]
    borg.stack.redo()
    assert len(obj) == original_length
    for item, obj_r in zip(obj, objs):
        assert item == obj_r

    # Test Place Item
    old_item = objs[idx]
    objs[idx] = p
    obj[idx] = p
    assert len(obj) == original_length
    for item, obj_r in zip(obj, objs):
        assert item == obj_r
    borg.stack.undo()
    for i in range(len(obj)):
        if i == idx:
            item = old_item
        else:
            item = objs[i]
        assert obj[i] == item
    borg.stack.redo()
    for item, obj_r in zip(obj, objs):
        assert item == obj_r

    borg.stack.enabled = False


def test_UndoRedoMacros():

    items = [createSingleObjs(idx) for idx in range(5)]
    offset = 5
    undo_text = 'test_macro'
    from easyCore import borg
    borg.stack.enabled = True
    borg.stack.beginMacro(undo_text)
    values = [item.raw_value for item in items]

    for item, value in zip(items, values):
        item.value = value + offset
    borg.stack.endMacro()

    for item, old_value in zip(items, values):
        assert item.raw_value == old_value + offset
    assert borg.stack.undoText() == undo_text

    borg.stack.undo()

    for item, old_value in zip(items, values):
        assert item.raw_value == old_value
    assert borg.stack.redoText() == undo_text

    borg.stack.redo()
    for item, old_value in zip(items, values):
        assert item.raw_value == old_value + offset


def test_fittingUndoRedo():
    
    m_value = 6
    c_value = 2
    x = np.linspace(-5, 5, 100)
    dy = np.random.rand(*x.shape)

    class Line(BaseObj):
        def __init__(self, m: Parameter, c: Parameter):
            super(Line, self).__init__('basic_line', m=m, c=c)

        @classmethod
        def default(cls):
            m = Parameter('m', m_value)
            c = Parameter('c', c_value)
            return cls(m=m, c=c)

        @classmethod
        def from_pars(cls, m_value: float, c_value: float):
            m = Parameter('m', m_value)
            c = Parameter('c', c_value)
            return cls(m=m, c=c)

        def __call__(self, x: np.ndarray) -> np.ndarray:
            return self.m.raw_value * x + self.c.raw_value

    l1 = Line.default()
    m_sp = 4
    c_sp = -3

    l2 = Line.from_pars(m_sp, c_sp)
    l2.m.fixed = False
    l2.c.fixed = False

    y = l1(x) + 0.125*(dy - 0.5)

    from easyCore.Fitting.Fitting import Fitter
    f = Fitter(l2, l2)
    from easyCore import borg
    borg.stack.enabled = True
    res = f.fit(x, y)

    assert l1.c.raw_value == pytest.approx(l2.c.raw_value, rel=l2.c.error)
    assert l1.m.raw_value == pytest.approx(l2.m.raw_value, rel=l2.m.error)
    assert borg.stack.undoText() == 'Fitting routine'

    borg.stack.undo()
    assert l2.m.raw_value == m_sp
    assert l2.c.raw_value == c_sp
    assert borg.stack.redoText() == 'Fitting routine'

    borg.stack.redo()
    assert l2.m.raw_value == res.p[f'p{borg.map.convert_id_to_key(l2.m)}']
    assert l2.c.raw_value == res.p[f'p{borg.map.convert_id_to_key(l2.c)}']
