#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from copy import deepcopy
from easyCore.Objects.Base import BaseObj, Descriptor
from easyCore.Symmetry.groups import SpaceGroup as SpaceGroupOpts

from easyCore.Utils.io.star import StarEntry, StarSection, FakeCore, FakeItem
from easyCore.Fitting.Constraints import ObjConstraint

SG_DETAILS = {
    'space_group_HM_name': {
        'description': 'Hermann-Mauguin symbols given in Table 4.3.2.1 of International Tables for Crystallography '
                       'Vol. A (2002) or a Hermann-Mauguin symbol for a conventional or unconventional setting.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_name_H-M_alt.html',
        'value':       'P 1',
    }
}


class SpaceGroup(BaseObj):

    def __init__(self, _space_group_HM_name: Descriptor, interface=None, setting=''):

        # Note that you can't use isinstance here as Parameter is derived and we ONLY WANT a Parameter
        if not type(_space_group_HM_name) == Descriptor:
            raise AttributeError("`space_group_HM_name` must be of `Descriptor` class")

        if setting and setting[0] != ':':
            setting = ':' + setting
            in_value = self._space_group_HM_name.raw_value
            if ':' in in_value:
                setting = ':' + self._space_group_HM_name.raw_value.split(':')[1]
            else:
                self._space_group_HM_name.raw_value = self._space_group_HM_name.raw_value + setting
        super(SpaceGroup, self).__init__('space_group',
                                         _space_group_HM_name=_space_group_HM_name)
        self.setting = setting
        self._sg_data = SpaceGroupOpts(self._space_group_HM_name.raw_value)
        self.interface = interface
        self._cell = None

    @classmethod
    def from_pars(cls, _space_group_HM_name: str, setting: str = '', interface=None):
        if ':' in _space_group_HM_name:
            opt = _space_group_HM_name.split(':')
            setting = opt[1]
            _space_group_HM_name = opt[0]
        default_options = deepcopy(SG_DETAILS)
        del default_options['space_group_HM_name']['value']
        in_setting = setting
        if setting:
            in_setting = ':' + in_setting
        return cls(Descriptor('_space_group_HM_name',
                              SpaceGroupOpts(_space_group_HM_name + in_setting).hm_for_cif,
                              **default_options['space_group_HM_name']),
                   interface=interface, setting=in_setting)

    @classmethod
    def default(cls, interface=None):
        return cls(Descriptor('_space_group_HM_name', **SG_DETAILS['space_group_HM_name']), interface=interface)

    @classmethod
    def from_int_number(cls, int_number, hexagonal=True, interface=None):
        sgs = [op for op in SpaceGroupOpts.SYMM_OPS if op['number'] == int_number]
        this_str = sgs[0]['hermann_mauguin']
        if int_number in [146, 148, 155, 160, 161, 166, 167]:
            if hexagonal:
                this_str += ':H'
            else:
                this_str += ':R'
        return cls.from_pars(this_str, interface=interface)

    def __on_change(self, value):
        if isinstance(value, int):
            self._sg_data = SpaceGroupOpts.from_int_number(value)
        else:
            self._sg_data = SpaceGroupOpts(value)
            # TODO THIS NEEDS A SELF.SETTING CHECK
        return self._sg_data.hm_for_cif

    @property
    def space_group_HM_name(self):
        return self._space_group_HM_name

    @space_group_HM_name.setter
    def space_group_HM_name(self, value):
        self._space_group_HM_name.value = self.__on_change(value)

    @property
    def full_symbol(self) -> str:
        return self._sg_data.full_symbol

    @property
    def int_symbol(self):
        return self._sg_data.int_number

    @property
    def point_group(self) -> str:
        return self._sg_data.point_group

    @property
    def order(self) -> int:
        return self._sg_data.order

    @property
    def crystal_system(self) -> str:
        return self._sg_data.crystal_system

    @property
    def int_number(self) -> int:
        return self._sg_data.int_number

    @property
    def hermann_mauguin(self):
        return self._sg_data.hm_for_cif

    @property
    def symmetry_opts(self):
        return self._sg_data.symmetry_ops

    def get_orbit(self, p, tol=1e-5):
        return self._sg_data.get_orbit(p, tol=tol)

    def to_star(self):
        if ':' in self.space_group_HM_name.raw_value:
            s = FakeCore()
            s_list = self.space_group_HM_name.raw_value.split(':')
            item = FakeItem(s_list[0])
            item.name = '_space_group_HM_name'
            s._kwargs['space_group_HM_name'] = item
            # item = FakeItem(s_list[1])
            # item.name = 'space_group.IT_coordinate_system_code'
            # s._kwargs['space_group.IT_coordinate_system_code'] = item
            return StarSection(s)
        return StarEntry(self.space_group_HM_name)

    @classmethod
    def from_star(cls, in_string: str):
        return StarEntry.from_string(cls, in_string)

    @classmethod
    def from_dict(cls, d):
        obj = None
        try:
            obj = super(SpaceGroup, cls).from_dict(d)
        except ValueError:
            d['_space_group_HM_name']['value'] = d['_space_group_HM_name']['value'].split(':')[0]
            obj = super(SpaceGroup, cls).from_dict(d)
        return obj

    def __repr__(self) -> str:
        out_str = "<Spacegroup: system: '{:s}', number: {}, H-M: '{:s}'".format(self.crystal_system, self.int_number,
                                                                                self.hermann_mauguin)
        if self.setting:
            out_str = "{:s} setting: '{:s}'".format(out_str, self.setting)
        return out_str + '>'