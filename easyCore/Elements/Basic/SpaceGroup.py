__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore.Objects.Base import BaseObj, Descriptor
from easyCore.Symmetry.groups import SpaceGroup as SpaceGroupOpts

from easyCore.Utils.io.star import StarEntry


class SpaceGroup(BaseObj):

    def __init__(self, _space_group_HM_name: Descriptor, interface=None):
        super(SpaceGroup, self).__init__('space_group',
                                         _space_group_HM_name=_space_group_HM_name)
        self._sg_data = SpaceGroupOpts(self._space_group_HM_name.raw_value)
        self.interface = interface

    @classmethod
    def from_pars(cls, _space_group_HM_name: str, interface=None):
        return cls(Descriptor('_space_group_HM_name',
                              SpaceGroupOpts(_space_group_HM_name).hm_for_cif),
                   interface=interface)

    @classmethod
    def default(cls, interface=None):
        this_id = SpaceGroupOpts.SYMM_OPS[0]["hermann_mauguin_fmt"]
        return cls(Descriptor('_space_group_HM_name', this_id), interface=interface)

    @classmethod
    def from_int_number(cls, int_number, hexagonal=True, interface=None):
        sg = SpaceGroupOpts.from_int_number(int_number, hexagonal)
        return cls.from_pars(sg.hm_for_cif, interface=interface)

    def __on_change(self, value):
        if isinstance(value, int):
            self._sg_data = SpaceGroupOpts.from_int_number(value)
        else:
            self._sg_data = SpaceGroupOpts(value)
        return self._sg_data.hm_for_cif

    @property
    def space_group_HM_name(self):
        return self._space_group_HM_name

    @space_group_HM_name.setter
    def space_group_HM_name(self, value):
        self._space_group_HM_name.value = self.__on_change(value)

    @property
    def full_symbol(self):
        return self._sg_data.full_symbol

    @property
    def int_symbol(self):
        return self._sg_data.int_number

    @property
    def point_group(self):
        return self._sg_data.point_group

    @property
    def order(self):
        return self._sg_data.order

    @property
    def crystal_system(self):
        return self._sg_data.crystal_system

    @property
    def int_number(self):
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
        return StarEntry(self.space_group_HM_name)

    @classmethod
    def from_star(cls, in_string):
        return StarEntry.from_string(cls, in_string)
