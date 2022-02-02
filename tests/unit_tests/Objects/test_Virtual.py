#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import pytest
from easyCore.Objects import Virtual
from easyCore.Objects.Variable import Parameter, Descriptor
from easyCore.models.polynomial import Line

@pytest.mark.parametrize("cls", [
    Parameter,
])
def test_virtual_variable(cls):
    obj = cls(name='test', value=1)
    v_obj = Virtual.virtualizer(obj)

    attrs = ["is_virtual", "_derived_from", "__non_virtual_class__", "realize", "relalize_component"]
    for attr in attrs:
        assert hasattr(v_obj, attr)

    assert obj.name == v_obj.name
    assert obj.raw_value == v_obj.raw_value


@pytest.mark.parametrize("cls", [
    Parameter,
])
def test_virtual_variable_modify(cls):
    obj = cls(name='test', value=1)
    v_obj = Virtual.virtualizer(obj)
    assert obj.name == v_obj.name
    assert obj.raw_value == v_obj.raw_value

    new_value = 2.
    obj.value = new_value
    assert obj.raw_value == v_obj.raw_value

    id_vobj = str(cls._borg.map.convert_id(v_obj).int)
    assert id_vobj in list(obj._constraints["virtual"].keys())

    del v_obj
    # assert id_vobj not in list(obj._constraints["virtual"].keys())

def test_Base_obj():
    l = Line.from_pars(2, 1)
    v_l = Virtual.virtualizer(l)
    assert l.name == v_l.name
    assert l.m.raw_value == v_l.m.raw_value
    assert l.c.raw_value == v_l.c.raw_value

    m = 4.

    l.m = m
    assert l.m.raw_value == m
    assert l.m.raw_value == v_l.m.raw_value
    assert l.c.raw_value == v_l.c.raw_value


def test_Base_obj():
    old_m = 2.
    l = Line.from_pars(old_m, 1)
    v_l = Virtual.virtualizer(l)
    assert l.name == v_l.name
    assert l.m.raw_value == v_l.m.raw_value
    assert l.c.raw_value == v_l.c.raw_value

    Virtual.component_realizer(v_l, 'm')

    m = 4.
    l.m = m
    assert l.m.raw_value == m
    assert v_l.m.raw_value == old_m
    assert l.c.raw_value == v_l.c.raw_value

    m_other = 5.
    v_l.m = m_other
    assert l.m.raw_value == m
    assert v_l.m.raw_value == m_other
    assert l.c.raw_value == v_l.c.raw_value
