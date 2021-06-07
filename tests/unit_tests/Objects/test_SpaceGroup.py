__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import pytest
import itertools

from easyCore.Objects.Base import Descriptor, Parameter
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup, SG_DETAILS
from easyCore.Symmetry.groups import SpaceGroup as SG


def test_SpaceGroup_fromDescriptor():

    sg_items = ['space_group_HM_name', 'P 1']

    d = Descriptor(*sg_items)
    sg = SpaceGroup(d)
    assert sg.space_group_HM_name.raw_value == 'P 1'

    with pytest.raises(AttributeError):
        p = Parameter('space_group_HM_name', 1)
        sg = SpaceGroup(p)

    with pytest.raises(AttributeError):
        sg = SpaceGroup('P 1')


def test_SpaceGroup_default():
    sg = SpaceGroup.default()

    for selector in SG_DETAILS.keys():
        f = getattr(sg, selector)
        for item in SG_DETAILS[selector].keys():
            g_item = item
            if item == 'value':
                g_item = 'raw_value'
            assert getattr(f, g_item) == SG_DETAILS[selector][item]

    assert sg.setting == ''
    assert isinstance(sg.space_group_HM_name, Descriptor)


@pytest.mark.parametrize('sg_in', [sg['hermann_mauguin_fmt'] for sg in SG.SYMM_OPS])
def test_SpaceGroup_fromPars_HM_Full(sg_in):
    sg_p = SpaceGroup.from_pars(sg_in)

    for selector in SG_DETAILS.keys():
        f = getattr(sg_p, selector)
        for item in SG_DETAILS[selector].keys():
            g_item = item
            f_value = SG_DETAILS[selector][item]
            if item == 'value':
                g_item = 'raw_value'
                f_value = sg_in
            assert getattr(f, g_item) == f_value


@pytest.mark.parametrize('sg_in', SG.SYMM_OPS, ids=[sg['hermann_mauguin'] for sg in SG.SYMM_OPS])
def test_SpaceGroup_fromPars_HM_noSpace(sg_in):
    sg_p = SpaceGroup.from_pars(sg_in['hermann_mauguin'])

    for selector in SG_DETAILS.keys():
        f = getattr(sg_p, selector)
        for item in SG_DETAILS[selector].keys():
            g_item = item
            f_value = SG_DETAILS[selector][item]
            if item == 'value':
                g_item = 'raw_value'
                f_value = sg_in['hermann_mauguin_fmt']
            assert getattr(f, g_item) == f_value


@pytest.mark.parametrize('sg_in', SG.SYMM_OPS, ids=[sg['universal_h_m'] for sg in SG.SYMM_OPS])
def test_SpaceGroup_fromPars_HM_noSpace(sg_in):
    sg_p = SpaceGroup.from_pars(sg_in['universal_h_m'])

    for selector in SG_DETAILS.keys():
        f = getattr(sg_p, selector)
        for item in SG_DETAILS[selector].keys():
            g_item = item
            f_value = SG_DETAILS[selector][item]
            if item == 'value':
                g_item = 'raw_value'
                f_value = sg_in['hermann_mauguin_fmt']
            assert getattr(f, g_item) == f_value


@pytest.mark.parametrize('sg_int', range(1, 231), ids=[f'spacegroup_int_{s_id}' for s_id in range(1, 231)])
def test_SpaceGroup_fromIntNumber(sg_int):
    sg_p = SpaceGroup.from_int_number(sg_int)

    for selector in SG_DETAILS.keys():
        f = getattr(sg_p, selector)
        for item in SG_DETAILS[selector].keys():
            g_item = item
            f_value = SG_DETAILS[selector][item]
            if item == 'value':
                g_item = 'raw_value'
                for opt in SG.SYMM_OPS:
                    if opt['number'] == sg_int:
                        f_value = opt['hermann_mauguin_fmt']
                        break
            assert getattr(f, g_item) == f_value


@pytest.mark.parametrize('sg_int,setting', itertools.product([146, 148, 155, 160, 161, 166, 167], [True, False]))
def test_SpaceGroup_fromIntNumber_HexTest(sg_int, setting):
    sg_p = SpaceGroup.from_int_number(sg_int, setting)

    for selector in SG_DETAILS.keys():
        f = getattr(sg_p, selector)
        for item in SG_DETAILS[selector].keys():
            g_item = item
            f_value = SG_DETAILS[selector][item]
            if item == 'value':
                g_item = 'raw_value'
                for opt in SG.SYMM_OPS:
                    if opt['number'] == sg_int:
                        f_value: str = opt['hermann_mauguin_fmt']
                        if f_value.endswith(':H') and setting or f_value.endswith(':R') and not setting:
                            break
            assert getattr(f, g_item) == f_value
