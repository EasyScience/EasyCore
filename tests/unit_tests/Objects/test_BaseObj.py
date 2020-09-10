__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import pytest
import numpy as np

from typing import List, Type, Union
from contextlib import contextmanager

from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
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


@contextmanager
def not_raises(expected_exception: Union[Type[BaseException], List[Type[BaseException]]]):
    try:
        yield
    except expected_exception:
        raise pytest.fail('Did raise exception {0} when it should not.'.format(repr(expected_exception)))
    except Exception as err:
        raise pytest.fail('An unexpected exception {0} raised.'.format(repr(err)))


@pytest.mark.parametrize('a, kw', [([], ['par1']),
                                   (['par1'], []),
                                   (['par1'], ['par2']),
                                   (['par1', 'des1'], ['par2', 'des2'])])
def test_baseobj_create(setup_pars: dict, a: List[str], kw: List[str]):
    name = setup_pars['name']
    args = []
    for key in a:
        args.append(setup_pars[key])
    kwargs = {}
    for key in kw:
        kwargs[key] = setup_pars[key]
    base = BaseObj(name, *args, **kwargs)
    assert base.name == name
    for key in a:
        item = getattr(base, setup_pars[key].name)
        assert isinstance(item, setup_pars[key].__class__)


def test_baseobj_get(setup_pars: dict):
    name = setup_pars['name']
    explicit_name1 = 'par1'
    explicit_name2 = 'par2'
    kwargs = {
        setup_pars[explicit_name1].name: setup_pars[explicit_name1],
        setup_pars[explicit_name2].name: setup_pars[explicit_name2]
    }
    obj = BaseObj(name, **kwargs)
    with not_raises(AttributeError):
        p1: Parameter = obj.p1
    with not_raises(AttributeError):
        p2: Parameter = obj.p2


def test_baseobj_set(setup_pars: dict):
    from copy import deepcopy
    name = setup_pars['name']
    explicit_name1 = 'par1'
    kwargs = {
        setup_pars[explicit_name1].name: setup_pars[explicit_name1],
    }
    obj = BaseObj(name, **kwargs)
    new_value = 5.0
    with not_raises([AttributeError, ValueError]):
        obj.p1 = new_value
        assert obj.p1.raw_value == new_value


def test_baseobj_get_parameters(setup_pars: dict):
    name = setup_pars['name']
    del setup_pars['name']
    obj = BaseObj(name, **setup_pars)
    pars = obj.get_parameters()
    assert isinstance(pars, list)
    assert len(pars) == 2
    par_names = [par.name for par in pars]
    assert 'p2' in par_names
    assert 'p3' in par_names


def test_baseobj_fit_objects(setup_pars: dict):
    pass


def test_baseobj_as_dict(setup_pars: dict):
    name = setup_pars['name']
    del setup_pars['name']
    obj = BaseObj(name, **setup_pars)
    obtained = obj.as_dict()
    assert isinstance(obtained, dict)
    expected = {'@module': 'easyCore.Objects.Base',
                '@class': 'BaseObj',
                '@version': '0.0.1',
                'name': 'test',
                'par1':
                    {'@module': 'easyCore.Objects.Base',
                     '@class': 'Parameter',
                     '@version': '0.0.1',
                     'name': 'p1',
                     'value': 0.1,
                     'error': 0.0,
                     'min': -np.inf,
                     'max': np.inf,
                     'fixed': True,
                     'units': 'dimensionless'
                     },
                'des1':
                    {'@module': 'easyCore.Objects.Base',
                     '@class': 'Descriptor',
                     '@version': '0.0.1',
                     'name': 'd1',
                     'value': 0.1,
                     'units': 'dimensionless',
                     'description': '',
                     'url': '',
                     'display_name': 'd1'
                     },
                'par2':
                    {'@module': 'easyCore.Objects.Base',
                     '@class': 'Parameter',
                     '@version': '0.0.1',
                     'name': 'p2',
                     'value': 0.1,
                     'error': 0.0,
                     'min': -np.inf,
                     'max': np.inf,
                     'fixed': False,
                     'units': 'dimensionless'
                     },
                'des2':
                    {'@module': 'easyCore.Objects.Base',
                     '@class': 'Descriptor',
                     '@version': '0.0.1',
                     'name': 'd2',
                     'value': 0.1,
                     'units': 'dimensionless',
                     'description': '',
                     'url': '',
                     'display_name': 'd2'
                     },
                'par3':
                    {'@module': 'easyCore.Objects.Base',
                     '@class': 'Parameter',
                     '@version': '0.0.1',
                     'name': 'p3',
                     'value': 0.1,
                     'error': 0.0,
                     'min': -np.inf,
                     'max': np.inf,
                     'fixed': False,
                     'units': 'dimensionless'
                     }
                }

    def check_dict(check, item):
        if isinstance(check, dict) and isinstance(item, dict):
            if '@module' in item.keys():
                with not_raises([ValueError, AttributeError]):
                    this_obj = MontyDecoder().process_decoded(item)
            for this_check_key, this_item_key in zip(check.keys(), item.keys()):
                check_dict(check[this_check_key], item[this_item_key])
        else:
            assert isinstance(item, type(check))
            assert item == check

    check_dict(expected, obtained)


def test_baseobj_dir(setup_pars):
    name = setup_pars['name']
    del setup_pars['name']
    obj = BaseObj(name, **setup_pars)
    expected = ['REDIRECT', 'as_dict', 'des1', 'des2', 'fit_objects',
                'from_dict', 'get_parameters', 'par1', 'par2', 'par3',
                'set_binding', 'to_json', 'unsafe_hash']
    obtained = dir(obj)
    assert len(obtained) == len(expected)
    assert obtained == sorted(obtained)
    for this_item, this_expect in zip(obtained, expected):
        assert this_item == this_expect

        

