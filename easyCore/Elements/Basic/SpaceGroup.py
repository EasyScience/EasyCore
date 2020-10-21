__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from copy import deepcopy
from easyCore.Objects.Base import BaseObj, Descriptor
from easyCore.Symmetry.groups import SpaceGroup as SpaceGroupOpts

from easyCore.Utils.io.star import StarEntry
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
        super(SpaceGroup, self).__init__('space_group',
                                         _space_group_HM_name=_space_group_HM_name)
        if setting and setting[0] != ':':
            setting = ':' + setting
        self.setting = setting
        self._sg_data = SpaceGroupOpts(self._space_group_HM_name.raw_value + self.setting)
        self.interface = interface
        self._cell = None

    @classmethod
    def from_pars(cls, _space_group_HM_name: str, interface=None):
        setting = ''
        if ':' in _space_group_HM_name:
            opt = _space_group_HM_name.split(':')
            setting =opt[1]
            _space_group_HM_name = opt[0]
        default_options = deepcopy(SG_DETAILS)
        del default_options['space_group_HM_name']['value']
        return cls(Descriptor('_space_group_HM_name',
                              SpaceGroupOpts(_space_group_HM_name).hm_for_cif, **default_options['space_group_HM_name']),
                        interface=interface, setting=setting)
        return obj

    @classmethod
    def default(cls, interface=None):
        return cls(Descriptor('_space_group_HM_name', **SG_DETAILS['space_group_HM_name']), interface=interface)

    @classmethod
    def from_int_number(cls, int_number, hexagonal=True, interface=None):
        sg = SpaceGroupOpts.from_int_number(int_number, hexagonal)
        this_str = sg.hm_for_cif
        if not hexagonal and sg.int_number in [146, 148, 155, 160, 161, 166, 167]:
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
        self.clear_sym()
        self._space_group_HM_name.value = self.__on_change(value)
        self.enforce_sym()

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
        return StarEntry(self.space_group_HM_name)

    @classmethod
    def from_star(cls, in_string: str):
        return StarEntry.from_string(cls, in_string)

    def __repr__(self) -> str:
        return "<Spacegroup: system: '{:s}', number: {}, H-M: '{:s}'>".format(self.crystal_system, self.int_number, self.hermann_mauguin)

    def clear_sym(self, cell=None):
        if cell is None and self._cell is None:
            return
        if cell is not None:
            self._cell = cell
        cell = self._cell
        pars = cell.get_parameters()
        for par in pars:
            new_con = {con: par.constraints['user'][con] for con in par.constraints['user'].keys() if not con.startswith('sg_')}
            par.constraints['user'] = new_con
            if not par.enabled:
                par.enabled = True

    def enforce_sym(self, cell=None):
        """
        Enforce symmetry constraints on to a cell
        :param cell: Cell for which the symmetry applies
        :return: None
        """
        if cell is None and self._cell is None:
            return
        if cell is not None:
            self._cell = cell
        cell = self._cell

        # SG system
        crys_system = self.crystal_system

        # Go through the cell systems
        if crys_system == "cubic":
            cell.length_a.constraints['user']['sg_1'] = ObjConstraint(cell.length_b, '',  cell.length_a)
            cell.length_a.constraints['user']['sg_1']()
            cell.length_a.constraints['user']['sg_2'] = ObjConstraint(cell.length_c, '',  cell.length_a)
            cell.length_a.constraints['user']['sg_2']()
            cell.angle_alpha = 90
            cell.angle_alpha.enabled = False
            cell.angle_beta = 90
            cell.angle_beta.enabled = False
            cell.angle_gamma = 90
            cell.angle_gamma.enabled = False
            return
        if crys_system == "hexagonal" or (
                crys_system == "trigonal" and (
                self.setting.endswith("H") or
                self.int_number in [143, 144, 145, 147, 149, 150, 151, 152,
                                    153, 154, 156, 157, 158, 159, 162, 163,
                                    164, 165])):
            cell.length_a.constraints['user']['sg_1'] = ObjConstraint(cell.length_b, '',  cell.length_a)
            cell.length_a.constraints['user']['sg_1']()
            cell.angle_alpha = 90
            cell.angle_alpha.enabled = False
            cell.angle_beta = 90
            cell.angle_beta.enabled = False
            cell.angle_gamma = 120
            cell.angle_gamma.enabled = False
            return
        if crys_system == "trigonal":
            cell.length_a.constraints['user']['sg_1'] = ObjConstraint(cell.length_b, '',  cell.length_a)
            cell.length_a.constraints['user']['sg_1']()
            cell.length_a.constraints['user']['sg_2'] = ObjConstraint(cell.length_c, '',  cell.length_a)
            cell.length_a.constraints['user']['sg_2']()
            cell.angle_alpha.constraints['user']['sg_1'] = ObjConstraint(cell.angle_beta, '',  cell.angle_alpha)
            cell.angle_alpha.constraints['user']['sg_1']()
            cell.angle_alpha.constraints['user']['sg_2'] = ObjConstraint(cell.angle_gamma, '',  cell.angle_alpha)
            cell.angle_alpha.constraints['user']['sg_2']()
            return
        if crys_system == "tetragonal":
            cell.length_a.constraints['user']['sg_1'] = ObjConstraint(cell.length_b, '',  cell.length_a)
            cell.length_a.constraints['user']['sg_1']()
            cell.angle_alpha = 90
            cell.angle_alpha.enabled = False
            cell.angle_beta = 90
            cell.angle_beta.enabled = False
            cell.angle_gamma = 90
            cell.angle_gamma.enabled = False
            return
        if crys_system == "orthorhombic":
            cell.angle_alpha = 90
            cell.angle_alpha.enabled = False
            cell.angle_beta = 90
            cell.angle_beta.enabled = False
            cell.angle_gamma = 90
            cell.angle_gamma.enabled = False
            return
        if crys_system == "monoclinic":
            cell.angle_alpha = 90
            cell.angle_alpha.enabled = False
            cell.angle_gamma = 90
            cell.angle_gamma.enabled = False
            return