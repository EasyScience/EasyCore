__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import List

from .groups import SpaceGroup, _get_symm_data, sg_symbol_from_int_number


class SpacegroupInfo:

    @staticmethod
    def get_all_systems() -> List[str]:
        return ["triclinic", "monoclinic", "orthorhombic", "tetragonal", "hexagonal", "cubic"]

    @staticmethod
    def get_ints_from_system(system: str) -> List[int]:
        if system == "triclinic":
            return list(range(1, 3))
        elif system == "monoclinic":
            return list(range(3, 16))
        elif system == "orthorhombic":
            return list(range(16, 75))
        elif system == "tetragonal":
            return list(range(75, 143))
        elif system == "trigonal":
            return list(range(143, 168))
        elif system == "hexagonal":
            return list(range(168, 195))
        else:
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
        return sg_symbol_from_int_number(int_number)

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

