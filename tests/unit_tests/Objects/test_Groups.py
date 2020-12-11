__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import pytest

from easyCore.Objects.Groups import BaseCollection, BaseObj
from easyCore.Objects.Base import Descriptor, Parameter
from easyCore.Utils.json import MontyDecoder


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


@pytest.mark.parametrize('value', (0, 1, 3))
def test_baseCollection_getItem(setup_pars, value):
    name = setup_pars['name']
    del setup_pars['name']

    coll = BaseCollection(name, **setup_pars)

    get_item = coll[value]
    key = list(setup_pars.keys())[value]
    assert get_item.name == setup_pars[key].name


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
