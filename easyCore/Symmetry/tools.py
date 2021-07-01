#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from typing import List

from .groups import SpaceGroup, _get_symm_data


def _make_SG_names() -> list:
    sg_list = []
    for ind in range(1, 231):
        for op in SpaceGroup.SYMM_OPS:
            if op['number'] == ind:
                s = op['hermann_mauguin_fmt']
                if ':' in s:
                    s = s.split(':')[0]
                sg_list.append(s)
                break
    return sg_list


SG_NAMES = _make_SG_names()


class SpacegroupInfo:

    @staticmethod
    def get_all_systems() -> List[str]:
        return ["triclinic", "monoclinic", "orthorhombic", "tetragonal", "hexagonal", "cubic"]

    @staticmethod
    def get_ints_from_system(system: str) -> List[int]:
        if system == "triclinic":
            return list(range(1, 3))
        if system == "monoclinic":
            return list(range(3, 16))
        if system == "orthorhombic":
            return list(range(16, 75))
        if system == "tetragonal":
            return list(range(75, 143))
        if system == "trigonal":
            return list(range(143, 168))
        if system == "hexagonal":
            return list(range(168, 195))
        return list(range(195, 231))

    @staticmethod
    def get_system_from_int(int_number: int):
        if int_number <= 2:
            return "triclinic"
        if int_number <= 15:
            return "monoclinic"
        if int_number <= 74:
            return "orthorhombic"
        if int_number <= 142:
            return "tetragonal"
        if int_number <= 167:
            return "trigonal"
        if int_number <= 194:
            return "hexagonal"
        return "cubic"

    @staticmethod
    def get_symbol_from_int_number(int_number: int):
        return SG_NAMES[int_number - 1]

    @staticmethod
    def get_compatible_HM_from_int(int_number: int):
        return [sop['hermann_mauguin_fmt'] for sop in SpaceGroup.SYMM_OPS if sop['number'] == int_number]

    @staticmethod
    def get_compatible_HM_from_name(name: str):
        enc: dict = _get_symm_data("space_group_encoding")
        opt = enc.get(name.replace(' ', ''), None)
        if opt is None:
            raise AttributeError
        return SpacegroupInfo.get_compatible_HM_from_int(opt['int_number'])

    @staticmethod
    def get_int_from_HM(HM_str: str):
        ints = [sop['number'] for sop in SpaceGroup.SYMM_OPS if sop['hermann_mauguin'] == HM_str.replace(' ', '')]
        if not ints:
            raise AttributeError
        return ints[0]
