__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List

import pytest
from copy import deepcopy
from easyCore import np
from easyCore.Elements.Basic.Site import Site, PeriodicSite, Parameter, _SITE_DETAILS

site_details = [('Al', 'Al'), ('Fe', 'Fe3+'), ('TEST', 'H')]


@pytest.fixture
def instance(request):
    def class_creation(*args, **kwargs):
        return Site.from_pars(*request.param, *args, **kwargs)

    return class_creation


def _generate_inputs(do_occ=True):
    # These are the parameters which will always be present
    # These will be the optional parameters
    a = [1]
    if do_occ:
        a = [0, 0.1, 1.1]
    b = [0.1, 0.5]

    advanced = {'occupancy': a.copy(),
                'fract_x':   b.copy(),
                'fract_y':   b.copy(),
                'fract_z':   b.copy(),
                }
    occ = _SITE_DETAILS['occupancy'].copy()
    occ['value'] = a.copy()

    pos = _SITE_DETAILS['position'].copy()
    pos['value'] = b.copy()

    advanced_result = {
        'occupancy': {'name': 'occupancy', **occ},
        'fract_x':   {'name': 'fract_x', **pos},
        'fract_y':   {'name': 'fract_y', **pos},
        'fract_z':   {'name': 'fract_z', **pos}
    }

    def create_entry(base, key, value, ref, ref_key=None):
        this_temp = deepcopy(base)
        if this_temp:
            for item in base:
                test, res = item
                new_opt = deepcopy(test)
                new_res = deepcopy(res)
                if ref_key is None:
                    ref_key = key
                new_res[ref_key] = ref
                new_opt[key] = value
                this_temp.append((new_opt, new_res))
        else:
            this_temp.append(({key: value}, {ref_key: ref}))
        return this_temp

    temp = []
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


@pytest.mark.parametrize('instance', site_details, indirect=True)
@pytest.mark.parametrize("element, expected", _generate_inputs())
def test_Site_creation(instance, element: List, expected: dict):
    d = instance(**element)
    for field in expected.keys():
        ref = expected[field]
        obtained = getattr(d, field)
        if isinstance(obtained, Parameter):
            assert obtained.raw_value == ref
        else:
            assert obtained == ref


@pytest.mark.parametrize('label, elm', site_details)
def test_Site_default(label, elm):
    site = Site.default(label, elm)

    assert site.name == label
    assert site.specie.raw_value == elm

    positions = _SITE_DETAILS['position']
    for item_label in ['fract_x', 'fract_y', 'fract_z']:
        item = getattr(site, item_label)
        for key in positions.keys():
            test_key = key
            if key == 'value':
                test_key = 'raw_value'
            assert getattr(item, test_key) == positions[key]

    occupancy = _SITE_DETAILS['occupancy']
    for item_label in ['occupancy']:
        item = getattr(site, item_label)
        for key in occupancy.keys():
            test_key = key
            if key == 'value':
                test_key = 'raw_value'
            assert getattr(item, test_key) == occupancy[key]


@pytest.mark.parametrize('instance', site_details, indirect=True)
@pytest.mark.parametrize("element, expected", _generate_inputs(do_occ=False))
def test_Site_short_pos(instance, element: List, expected: dict):
    d = instance(**element)
    pars = [('x', 'fract_x'),
            ('y', 'fract_y'),
            ('z', 'fract_z')]

    for par in pars:
        if par[1] in expected.keys():
            expected_value = expected[par[1]]
        else:
            expected_value = _SITE_DETAILS['position']['value']
        obtained = getattr(d, par[0])
        assert expected_value == obtained.raw_value


@pytest.mark.parametrize('instance', site_details, indirect=True)
@pytest.mark.parametrize("element, expected", _generate_inputs(do_occ=False))
def test_Site_fract_coords(instance, element: List, expected: dict):
    d = instance(**element)

    el_for_check = ['fract_x', 'fract_y', 'fract_z']

    expected_value = []
    for par in el_for_check:
        if par in expected.keys():
            expected_value.append(expected[par])
        else:
            expected_value.append(_SITE_DETAILS['position']['value'])
    assert np.all(d.fract_coords == expected_value)


@pytest.mark.parametrize('instance', site_details, indirect=True)
@pytest.mark.parametrize("element, expected", _generate_inputs(do_occ=False))
@pytest.mark.parametrize('second_pt', ([0.0, 0.0, 0.0], [0.25, 0.1, 0.1], [1 / 8, 1 / 3, 1 / 4]))
def test_Site_fract_dist(instance, element: List, expected: dict, second_pt):
    d = instance(**element)
    other_site = Site.from_pars('H', 'H', 1, *second_pt)
    expected_value = np.linalg.norm(np.array(second_pt) - d.fract_coords)
    assert np.all(d.fract_distance(other_site) == expected_value)


@pytest.mark.parametrize('label, elm', site_details)
@pytest.mark.parametrize("element, expected", _generate_inputs(do_occ=False))
def test_Site_repr(label, elm, element, expected):
    d = Site.from_pars(label, elm, **element)

    el_for_check = ['fract_x', 'fract_y', 'fract_z']

    expected_value = []
    for par in el_for_check:
        if par in expected.keys():
            expected_value.append(expected[par])
        else:
            expected_value.append(float(_SITE_DETAILS['position']['value']))

    assert str(d) == f'Atom {label} ({elm}) @ ({expected_value[0]}, {expected_value[1]}, {expected_value[2]})'


@pytest.mark.parametrize('label, elm', site_details)
def test_Site_as_dict(label, elm):
    s = Site.from_pars(label, elm)
    obtained = s.as_dict()
    expected = {
        '@module':   'easyCore.Elements.Basic.Site',
        '@class':    'Site',
        '@version':  '0.0.1',
        '@id':       None,
        'label':     {
            '@module':      'easyCore.Objects.Base',
            '@class':       'Descriptor',
            '@version':     '0.0.1',
            '@id':          None,
            'name':         'label',
            'value':        label,
            'units':        'dimensionless',
            'description':  'A unique identifier for a particular site in the crystal',
            'url':          'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_label'
                            '.html',
            'display_name': 'label',
            'enabled':      True
        },
        # Note that we are skipping specie checking as it it covered in another file...
        # 'specie': {
        #      '@module':  'easyCore.Elements.Basic.Specie', '@class': 'Specie',
        #      '@version': '0.0.1',
        #      '@id':      None,
        #      'specie':
        #                  {
        #                      '@module':         'easyCore.Elements.periodic_table',
        #                      '@class':          'Specie' + ('s' if '+' in elm else ''),
        #                      'element':         elm,
        #                      'oxidation_state': 0.0
        #                  },
        #      'value':    elm,
        #      'units':    'dimensionless',
        #  },
        'occupancy': {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'occupancy',
            'value':       1.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'The fraction of the atom type present at this site.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_occupancy.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'fract_x':   {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'fract_x',
            'value':       0.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'Atom-site coordinate as fractions of the unit cell length.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_fract_.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'fract_y':   {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'fract_y',
            'value':       0.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'Atom-site coordinate as fractions of the unit cell length.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_fract_.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'fract_z':   {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'fract_z',
            'value':       0.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'Atom-site coordinate as fractions of the unit cell length.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_fract_.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'interface': None,
    }

    def check_dict(check, item):
        if isinstance(check, dict) and isinstance(item, dict):
            for this_check_key in check.keys():
                if this_check_key == '@id':
                    continue
                check_dict(check[this_check_key], item[this_check_key])
        else:
            assert isinstance(item, type(check))
            assert item == check

    check_dict(expected, obtained)


@pytest.mark.parametrize('label, elm', site_details)
def test_Site_from_dict(label, elm):
    d = {
        '@module':   'easyCore.Elements.Basic.Site',
        '@class':    'Site',
        '@version':  '0.0.1',
        '@id':       None,
        'label':     {
            '@module':      'easyCore.Objects.Base',
            '@class':       'Descriptor',
            '@version':     '0.0.1',
            '@id':          None,
            'name':         'label',
            'value':        label,
            'units':        'dimensionless',
            'description':  'A unique identifier for a particular site in the crystal',
            'url':          'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_label'
                            '.html',
            'display_name': 'label',
            'enabled':      True
        },
        'specie':    {
            '@module':  'easyCore.Elements.Basic.Specie', '@class': 'Specie',
            '@version': '0.0.1',
            '@id':      None,
            'specie':   elm,
            'value':    elm,
            'units':    'dimensionless',
        },
        'occupancy': {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'occupancy',
            'value':       1.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'The fraction of the atom type present at this site.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_occupancy.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'fract_x':   {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'fract_x',
            'value':       0.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'Atom-site coordinate as fractions of the unit cell length.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_fract_.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'fract_y':   {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'fract_y',
            'value':       0.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'Atom-site coordinate as fractions of the unit cell length.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_fract_.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'fract_z':   {
            '@module':     'easyCore.Objects.Base',
            '@class':      'Parameter',
            '@version':    '0.0.1',
            '@id':         None,
            'name':        'fract_z',
            'value':       0.0,
            'error':       0.0,
            'min':         -np.inf,
            'max':         np.inf,
            'fixed':       True,
            'description': 'Atom-site coordinate as fractions of the unit cell length.',
            'url':
                           'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic'
                           '/Iatom_site_fract_.html',
            'units':       'dimensionless',
            'enabled':     True
        },
        'interface': None,
    }

    s = Site.from_dict(d)

    def check_dict(check, item):
        if isinstance(check, dict) and isinstance(item, dict):
            for this_check_key in check.keys():
                if this_check_key == '@id' or this_check_key == 'specie':
                    continue
                check_dict(check[this_check_key], item[this_check_key])
        else:
            assert isinstance(item, type(check))
            assert item == check

    check_dict(d, s.as_dict())
