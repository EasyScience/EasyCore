__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List

import pytest

from easyCore.Objects.Groups import BaseCollection, BaseObj
from easyCore.Objects.Base import Descriptor, Parameter
from easyCore.Utils.json import MontyDecoder

test_dict = {
    '@module':  'easyCore.Objects.Groups',
    '@class':   'BaseCollection',
    '@version': '0.0.1',
    'name':     'testing',
    'data':     [
        {
            '@module': 'easyCore.Objects.Base',
            '@class': 'Descriptor',
            '@version': '0.0.1',
            'name': 'par1',
            'value': 1,
            'units': 'dimensionless',
            'description': '',
            'url': '',
            'display_name': 'par1',
            'enabled': True,
            '@id':     '137972150639753919686442328054550030033'
        }
    ],
    '@id': '276645396109151960980117648876826100232'
}


@pytest.fixture
def setup_pars():
    d = {
        'name': 'test',
        'par1': Parameter('p1', 0.1, fixed=True),
        'des1': Descriptor('d1', 0.1),
        'par2': Parameter('p2', 0.1),
        'des2': Descriptor('d2', 0.1),
        'par3': Parameter('p3', 0.1),
    }
    return d


def test_baseCollection_from_base(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']
    coll = BaseCollection(name, **setup_pars)

    assert coll.name == name
    assert len(coll) == 5
    assert coll.user_data == {}

    for item, key in zip(coll, setup_pars.keys()):
        assert item.name == setup_pars[key].name
        assert item.value == setup_pars[key].value


@pytest.mark.parametrize('value', range(1, 11))
def test_baseCollection_from_baseObj(setup_pars: dict, value: int):
    name = setup_pars['name']
    del setup_pars['name']
    objs = {}

    prefix = 'obj'
    for idx in range(value):
        objs[prefix + str(idx)] = BaseObj(prefix + str(idx), **setup_pars)

    coll = BaseCollection(name, **objs)

    assert coll.name == name
    assert len(coll) == value
    assert coll.user_data == {}

    idx = 0
    for item, key in zip(coll, objs.keys()):
        assert item.name == prefix + str(idx)
        assert isinstance(item, objs[key].__class__)
        idx += 1


@pytest.mark.parametrize('value', ('abc', False, (), []))
def test_baseCollection_create_fail(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']
    setup_pars['to_fail'] = value

    with pytest.raises(AttributeError):
        coll = BaseCollection(name, **setup_pars)


@pytest.mark.parametrize('key', ('user_data', '_kwargs', 'interface'))
def test_baseCollection_create_fail2(setup_pars, key):
    name = setup_pars['name']
    del setup_pars['name']
    setup_pars[key] = Descriptor('fail_name', 0)

    with pytest.raises(AttributeError):
        coll = BaseCollection(name, **setup_pars)


def test_baseCollection_append_base(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']

    new_item_name = 'boo'
    new_item_value = 100
    new_item = Parameter(new_item_name, new_item_value)

    coll = BaseCollection(name, **setup_pars)
    n_before = len(coll)

    coll.append(new_item)
    assert len(coll) == n_before + 1
    assert coll[-1].name == new_item_name
    assert coll[-1].value == new_item_value


@pytest.mark.parametrize('value', ('abc', False, (), []))
def test_baseCollection_append_fail(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)
    with pytest.raises(AttributeError):
        coll.append(value)


@pytest.mark.parametrize('value', (0, 1, 3, 'par1', 'des1'))
def test_baseCollection_getItem(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)

    get_item = coll[value]
    if isinstance(value, str):
        key = value
    else:
        key = list(setup_pars.keys())[value]
    assert get_item.name == setup_pars[key].name


@pytest.mark.parametrize('value', (False, [], (), 100, 100.4))
def test_baseCollection_getItem_type_fail(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)

    with pytest.raises((IndexError, TypeError)):
        get_item = coll[value]


def test_baseCollection_getItem_slice(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)

    get_item = coll[0:2]
    assert len(get_item) == 2


@pytest.mark.parametrize('value', (0, 1, 3))
def test_baseCollection_setItem(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)
    n_coll = len(coll)
    name_coll_idx = coll[value].name

    new_item_value = 100

    coll[value] = new_item_value

    assert len(coll) == n_coll
    assert coll[value].name == name_coll_idx
    assert coll[value].value == new_item_value


@pytest.mark.parametrize('value', ('abc', (), []))
def test_baseCollection_setItem_fail(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)

    with pytest.raises(NotImplementedError):
        for idx in range(len(coll)):
            coll[idx] = value


@pytest.mark.parametrize('value', (0, 1, 3))
def test_baseCollection_delItem(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)
    n_coll = len(coll)
    # On del we should shift left
    name_coll_idx = coll[value].name
    name_coll_idxp = coll[value + 1].name

    del coll[value]

    assert len(coll) == n_coll - 1
    assert coll[value].name == name_coll_idxp
    assert name_coll_idx not in [col.name for col in coll]


@pytest.mark.parametrize('value', (0, 1, 3))
def test_baseCollection_len(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    keys = list(setup_pars.keys())
    keys = keys[0:(value + 1)]

    coll = BaseCollection(name, **{key: setup_pars[key] for key in keys})
    assert len(coll) == (value + 1)


def test_baseCollection_get_parameters(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']
    obj = BaseCollection(name, **setup_pars)
    pars = obj.get_parameters()
    assert len(pars) == 3


def test_baseCollection_get_parameters_nested(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']
    obj = BaseObj(name, **setup_pars)

    name2 = name + '_2'
    obj2 = BaseCollection(name2, obj=obj, **setup_pars)

    pars = obj2.get_parameters()
    assert len(pars) == 6


def test_baseCollection_get_fit_parameters(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']
    obj = BaseCollection(name, **setup_pars)
    pars = obj.get_fit_parameters()
    assert len(pars) == 2


def test_baseCollection_get_fit_parameters_nested(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']
    obj = BaseObj(name, **setup_pars)

    name2 = name + '_2'
    obj2 = BaseCollection(name2, obj=obj, **setup_pars)

    pars = obj2.get_fit_parameters()
    assert len(pars) == 4


def test_baseCollection_dir():
    name = 'testing'
    kwargs = {
        'p1': Descriptor('par1', 1)
    }
    obj = BaseCollection(name, **kwargs)
    d = set(dir(obj))

    expected = {'constraints', 'as_dict', 'from_dict',
                'to_json', 'generate_bindings', 'count', 'REDIRECT',
                'get_fit_parameters', 'unsafe_hash', 'to_data_dict',
                'switch_interface', 'get_parameters', 'index', 'append'}
    assert not d.difference(expected)


def test_baseCollection_as_dict():
    name = 'testing'
    kwargs = {
        'p1': Descriptor('par1', 1)
    }
    obj = BaseCollection(name, **kwargs)
    d = obj.as_dict()

    def check_dict(dict_1: dict, dict_2: dict):
        keys_1 = dict_1.keys()
        keys_2 = dict_2.keys()
        assert not set(keys_1).difference(set(keys_2))
        
        def testit(item1, item2):
            if isinstance(item1, dict) and isinstance(item2, dict):
                check_dict(item1, item2)
            elif isinstance(item1, list) and isinstance(item2, list):
                for v1, v2 in zip(item1, item2):
                    testit(v1, v2)
            else:
                if isinstance(item1, str) and isinstance(item2, str):
                    assert item1 == item2
                else:
                    assert item1 is item2
        
        for k1, k2 in zip(keys_1, keys_2):
            if k1 == '@id':
                continue
            testit(dict_1[k1], dict_2[k2])

    check_dict(d, test_dict)


def test_baseCollection_from_dict():
    name = 'testing'
    kwargs = {
        'p1': Descriptor('par1', 1)
    }
    ref = BaseCollection(name, **kwargs)
    expected = BaseCollection.from_dict(test_dict)

    assert ref.name == expected.name
    assert len(ref) == len(expected)
    for item1, item2 in zip(ref, expected):
        assert item1.name == item2.name
        assert item1.value == item2.value


def test_baseCollection_constraints():
    name = 'test'
    p1 = Parameter('p1', 1)
    p2 = Parameter('p2', 2)

    from easyCore.Fitting.Constraints import ObjConstraint
    p2.constraints['user']['testing'] = ObjConstraint(p2, '2*', p1)

    obj = BaseCollection(name, p1, p2)

    cons: List[ObjConstraint] = obj.constraints
    assert len(cons) == 1


def test_baseCollection_repr():
    name = 'test'
    p1 = Parameter('p1', 1)
    obj = BaseCollection(name, p1)
    test_str = str(obj)
    ref_str = 'BaseCollection `test` of length 1'
    assert test_str == ref_str
