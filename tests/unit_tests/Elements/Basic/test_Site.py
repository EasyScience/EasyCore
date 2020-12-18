__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import pytest
from easyCore import np
from numbers import Number
from easyCore.Elements.Basic.Site import Site, PeriodicSite, Parameter, _SITE_DETAILS


@pytest.mark.parametrize('label, elm', [('Al', 'Al'), ('Fe', 'Fe3+'), ('TEST', 'H')])
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

