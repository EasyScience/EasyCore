__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from copy import deepcopy
from typing import List

import pytest
from easyCore.Objects.Base import Descriptor, Parameter, ureg, Q_


@pytest.fixture
def instance(request):
    def class_creation(*args, **kwargs):
        return request.param(*args, **kwargs)
    return class_creation


def _generate_inputs():
    # These are the parameters which will always be present
    basic = {
        'name':  'test',
        'value': 1
    }
    basic_result = {
        'name':      basic['name'],
        'raw_value': basic['value'],
    }
    # These will be the optional parameters
    advanced = {'units':        ['cm', 'mm', 'kelvin'],
                'description':  'This is a test',
                'url':          'https://www.whatever.com',
                'display_name': "\Chi",
                }
    advanced_result = {
        'units':        {'name': 'unit', 'value': ['centimeter', 'millimeter', 'kelvin']},
        'description':  {'name': 'description', 'value': advanced['description']},
        'url':          {'name': 'url', 'value': advanced['url']},
        'display_name': {'name': 'display_name', 'value': advanced['display_name']}
    }

    temp = [([[basic['name'], basic['value']], {}], basic_result),
            ([[], basic], basic_result)]

    def create_entry(base, key, value, ref, ref_key=None):
        this_temp = deepcopy(base)
        for item in base:
            test, res = item
            new_opt = deepcopy(test[1])
            new_res = deepcopy(res)
            if ref_key is None:
                ref_key = key
            new_res[ref_key] = ref
            new_opt[key] = value
            this_temp.append(([test[0], new_opt], new_res))
        return this_temp

    for add_opt in advanced.keys():
        if isinstance(advanced[add_opt], list):
            for idx, item in enumerate(advanced[add_opt]):
                temp = create_entry(temp, add_opt, item,
                                    advanced_result[add_opt]['value'][idx],
                                    ref_key=advanced_result[add_opt]['name'])
        else:
            temp = create_entry(temp, add_opt, advanced[add_opt],
                                advanced_result[add_opt]['value'],
                                ref_key=advanced_result[add_opt]['name'])
    return temp


@pytest.mark.parametrize('instance', (Descriptor, Parameter), indirect=True)
@pytest.mark.parametrize("element, expected", _generate_inputs())
def test_item_creation(instance, element: List, expected: dict):
    d = instance(*element[0], **element[1])
    print(d.value)
    for field in expected.keys():
        ref = expected[field]
        obtained = getattr(d, field)
        if isinstance(obtained, (ureg.Unit, Q_)):
            obtained = str(obtained)
        assert obtained == ref


@pytest.mark.parametrize('element, expected', [('', '1 dimensionless'),
                                               ('cm', '1 centimeter'),
                                               ('mm', '1 millimeter'),
                                               ('kelvin', '1 kelvin')])
def test_Descriptor_value_get(element, expected):
    d = Descriptor('test', 1, units=element)
    assert str(d.value) == expected


@pytest.mark.parametrize('element, expected', [('', '(1.0 +/- 0) dimensionless'),
                                               ('cm', '(1.0 +/- 0) centimeter'),
                                               ('mm', '(1.0 +/- 0) millimeter'),
                                               ('kelvin', '(1.0 +/- 0) kelvin')])
def test_Parameter_value_get(element, expected):
    d = Parameter('test', 1, units=element)
    assert str(d.value) == expected


@pytest.mark.parametrize('instance', (Descriptor, Parameter), indirect=True)
def test_item_value_set(instance):
    d = instance('test', 1)
    d.value = 2
    assert d.raw_value == 2
    d = instance('test', 1, units='kelvin')
    d.value = 2
    assert d.raw_value == 2
    assert str(d.unit) == 'kelvin'


@pytest.mark.parametrize('instance', (Descriptor, Parameter), indirect=True)
def test_item_unit_set(instance):
    d = instance('test', 1)
    d.unit = 'kg'
    assert str(d.unit) == 'kilogram'

    d = instance('test', 1, units='kelvin')
    d.unit = 'cm'
    assert str(d.unit) == 'centimeter'


@pytest.mark.parametrize('instance', (Descriptor, Parameter), indirect=True)
def test_item_convert_unit(instance):
    d = instance('test', 273, units='kelvin')
    d.convert_unit('degree_Celsius')
    assert pytest.approx(d.raw_value, -0.149)


@pytest.mark.parametrize('instance', (Descriptor, Parameter), indirect=True)
def test_item_compatible_units(instance):
    reference = ['degree_Fahrenheit',
                 'kelvin',
                 'atomic_unit_of_temperature',
                 'degree_Celsius',
                 'degree_Rankine',
                 'planck_temperature',
                 'degree_Reaumur']
    d = instance('test', 273, units='kelvin')
    obtained = d.compatible_units
    from unittest import TestCase
    TestCase().assertCountEqual(reference, obtained)
