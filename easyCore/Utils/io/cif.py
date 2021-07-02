#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

import os
import re
from functools import partial
from io import TextIOWrapper, StringIO
from pathlib import Path
from typing import Union, List, Tuple
from copy import deepcopy
from inspect import signature
from numbers import Number

from easyCore.Elements.Basic.AtomicDisplacement import AtomicDisplacement
from easyCore.Elements.Basic.Lattice import Lattice
from easyCore.Elements.Basic.Site import Atoms, Site
from easyCore.Symmetry.groups import SpaceGroup as SpaceGroup2
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup

from easyCore.Utils.io.star import StarCollection, StarEntry, StarLoop, FakeItem, FakeCore, StarHeader, StarSection

sub_spgrp = partial(re.sub, r"[\s_]", "")
space_groups = {sub_spgrp(k): k for k in [opt['hermann_mauguin_fmt'] for opt in SpaceGroup2.SYMM_OPS]}  # type: ignore


class CifIO:

    def __init__(self, parser: 'CifParser' = None):
        self._parser: CifParser = parser
        self._writer: List[CifWriter] = []
        if parser is not None:
            self._writer = CifWriter.from_CifParser(parser)

    def use_objects(self, name, *args):
        self._writer = [CifWriter(name, *args)]
        self._parser = CifParser.from_string(str(self._writer[0]))

    @classmethod
    def from_objects(cls, name, *args):
        obj = cls()
        obj._writer = [CifWriter(name, *args)]
        obj._parser = CifParser.from_string(str(obj._writer[0]))
        return obj

    @classmethod
    def from_cif_str(cls, in_str: str):
        parser = CifParser(in_str)
        return cls(parser)

    def add_cif_from_objects(self, name, *args):
        self._writer.append(CifWriter(name, *args))
        self._parser = CifParser.from_string(str(self._writer))

    @classmethod
    def from_file(cls, file_path: Union[Path, TextIOWrapper]):
        parser = CifParser(file_path)
        return cls(parser)

    def to_string(self, cif_index=None):
        return self.__str__(cif_index)

    def to_file(self, file_name: Union[str, Path, TextIOWrapper], cif_index=None):
        with open(file_name, 'w') as writer:
            writer.write(self.__str__(cif_index))

    def __str__(self, index: Union[int, slice] = None):
        out_str = ''
        items = self._writer
        if index is not None:
            if isinstance(index, int):
                items = [items[index]]
            elif isinstance(index, slice):
                items = items[index]
            else:
                raise AttributeError('Index must be a slice or int')
        for writer in items:
            if writer is not None:
                out_str += str(writer) + '\n'
        return out_str

    def to_crystal_form(self, cif_index: int = 0):
        if self._parser is None:
            raise AttributeError
        return self._parser._cif[cif_index]['header'].name, {
            'cell':       self._parser.get_lattice(cif_index=cif_index),
            'spacegroup': self._parser.get_symmetry(cif_index=cif_index),
            'atoms':      self._parser.get_atoms(cif_index=cif_index)
        }


class CifParser:
    """
    Parses a CIF file. Attempts to fix CIFs that are out-of-spec, but will
    issue warnings if corrections applied. These are also stored in the
    CifParser's errors attribute.
    """

    def __init__(self, filename: Union[str, StringIO, TextIOWrapper], occupancy_tolerance=1., site_tolerance=1e-4):
        """
        Args:
            filename (str): CIF filename, bzipped or gzipped CIF files are fine too.
            occupancy_tolerance (float): If total occupancy of a site is between 1
                and occupancy_tolerance, the occupancies will be scaled down to 1.
            site_tolerance (float): This tolerance is used to determine if two
                sites are sitting in the same position, in which case they will be
                combined to a single disordered site. Defaults to 1e-4.
        """
        self._occupancy_tolerance = occupancy_tolerance
        self._site_tolerance = site_tolerance
        if hasattr(filename, '__str__') and os.path.isfile(str(filename)):
            in_data = StarCollection.from_file(filename)
        elif isinstance(filename, (TextIOWrapper, StringIO)):
            in_data = StarCollection.from_string(filename.read())
        else:
            in_data = StarCollection.from_string(filename)

        if not isinstance(in_data, list):
            # We have multiple data blocks
            in_data = [in_data]
        self._cif = in_data

        # store if CIF contains features from non-core CIF dictionaries
        # e.g. magCIF
        self.feature_flags = {}
        self.warnings = []

        def is_magcif() -> List[bool]:
            """
            Checks to see if file appears to be a magCIF file (heuristic).
            """
            # Doesn't seem to be a canonical way to test if file is magCIF or
            # not, so instead check for magnetic symmetry datanames
            prefixes = ['space_group_magn', 'atom_site_moment',
                        'space_group_symop_magn']
            logic = []
            for cif in self._cif:
                found = False
                for prefix in prefixes:
                    if prefix in cif['data'].keys():
                        found = True
                logic.append(found)
            return logic

        self.feature_flags['magcif'] = is_magcif()

        def is_magcif_incommensurate() -> List[bool]:
            """
            Checks to see if file contains an incommensurate magnetic
            structure (heuristic).
            """
            # Doesn't seem to be a canonical way to test if magCIF file
            # describes incommensurate strucure or not, so instead check
            # for common datanames
            logic = []
            for idx, cif in enumerate(self._cif):
                found = False
                if not self.feature_flags["magcif"][idx]:
                    logic.append(False)
                    continue
                prefixes = ['cell_modulation_dimension', 'cell_wave_vector']
                for prefix in prefixes:
                    if prefix in cif['data'].keys():
                        found = True
                logic.append(found)
            return logic

        self.feature_flags['magcif_incommensurate'] = is_magcif_incommensurate()


        for cif in self._cif:
            new_data = {}
            for k in cif['data'].keys():
                # pass individual CifBlocks to _sanitize_data
                obj = self._sanitize_data(cif['data'][k])
                new_data[obj.name] = obj
            cif['data'] = new_data

            # Sanitize the loops
            for idx, loop in enumerate(cif['loops']):
                cif['loops'][idx] = self._sanitize_loop(loop)

    @property
    def number_of_cifs(self) -> int:
        """
        Get the number of cif's stored

        :return: number of cif's stored
        :rtype: int
        """
        return len(self._cif)

    @classmethod
    def from_string(cls, cif_string, occupancy_tolerance=1.):
        """
        Creates a CifParser from a string.

        :param cif_string: String representation of a CIF.
        :type cif_string: str
        :param occupancy_tolerance:
        :type occupancy_tolerance:
        :return: If total occupancy of a site is between 1 and occupancy_tolerance, the occupancies will be scaled down
         to 1.
        :rtype: CifParser
        """
        stream = StringIO(cif_string)
        return cls(stream, occupancy_tolerance)

    def _sanitize_loop(self, data: StarLoop) -> StarLoop:
        """
        Some CIF files do not conform to spec. This function corrects
        known issues, particular in regards to Springer materials/
        Pauling files.
        This function is here so that CifParser can assume its
        input conforms to spec, simplifying its implementation.
        :param data: CifBlock
        :return: data CifBlock
        """

        # """
        # This part of the code deals with handling formats of data as found in
        # CIF files extracted from the Springer Materials/Pauling File
        # databases, and that are different from standard ICSD formats.
        # """

        # check for implicit hydrogens, warn if any present
        if "atom_site_attached_hydrogens" in data.labels:
            attached_hydrogens = [x._kwargs['atom_site_attached_hydrogens'].raw_value for x in data.data
                                  if x._kwargs['atom_site_attached_hydrogens'].raw_value != 0]
            if len(attached_hydrogens) > 0:
                self.warnings.append("Structure has implicit hydrogens defined, "
                                     "parsed structure unlikely to be suitable for use "
                                     "in calculations unless hydrogens added.")

        # Check to see if "_atom_site_type_symbol" exists, as some test CIFs do
        # not contain this key.
        if "atom_site_type_symbol" in data.labels:

            # Keep a track of which data row needs to be removed.
            # Example of a row: Nb,Zr '0.8Nb + 0.2Zr' .2a .m-3m 0 0 0 1 14
            # 'rhombic dodecahedron, Nb<sub>14</sub>'
            # Without this code, the above row in a structure would be parsed
            # as an ordered site with only Nb (since
            # CifParser would try to parse the first two characters of the
            # label "Nb,Zr") and occupancy=1.
            # However, this site is meant to be a disordered site with 0.8 of
            # Nb and 0.2 of Zr.
            idxs_to_remove = []
            new_atoms = []

            for idx, this_data in enumerate(data.data):

                # CIF files from the Springer Materials/Pauling File have
                # switched the label and symbol. Thus, in the
                # above shown example row, '0.8Nb + 0.2Zr' is the symbol.
                # Below, we split the strings on ' + ' to
                # check if the length (or number of elements) in the label and
                # symbol are equal.
                if len(this_data._kwargs["atom_site_type_symbol"].raw_value.split(' + ')) > \
                        len(this_data._kwargs["atom_site_label"].raw_value.split(' + ')):

                    # parse symbol to get element names and occupancy and store
                    # in "els_occu"
                    symbol_str = this_data._kwargs["atom_site_type_symbol"].raw_value
                    symbol_str_lst = symbol_str.split(' + ')
                    for elocc_idx, sym in enumerate(symbol_str_lst):
                        # Remove any bracketed items in the string
                        symbol_str_lst[elocc_idx] = re.sub(r'\([0-9]*\)', '', sym.strip())

                        # Extract element name and its occupancy from the
                        # string, and store it as a
                        # key-value pair in "els_occ".
                        new_item: FakeCore = deepcopy(this_data)
                        new_item._kwargs['atom_site_type_symbol'].raw_value = str(re.findall(r'\D+', symbol_str_lst[
                            elocc_idx].strip())[1]).replace('<sup>', '')
                        new_item._kwargs['atom_site_label'].raw_value = new_item._kwargs[
                                                                            'atom_site_type_symbol'].raw_value + "_fix"
                        if 'atom_site_occupancy' in new_item._kwargs.keys():
                            new_item._kwargs['atom_site_label'].raw_value = float(
                                '0' + re.findall(r'\.?\d+', symbol_str_lst[
                                    elocc_idx].strip())[1])
                        new_atoms.append(new_item)
                    idxs_to_remove.append(idx)

            # Remove the original row by iterating over all keys in the CIF
            # data looking for lists, which indicates
            # multiple data items, one for each row, and remove items from the
            # list that corresponds to the removed row,
            # so that it's not processed by the rest of this function (which
            # would result in an error).
            for this_id in sorted(idxs_to_remove, reverse=True):
                del data.data[this_id]
            if idxs_to_remove:
                data.data = data.data.extend[new_atoms]

            if len(idxs_to_remove) > 0:
                self.warnings.append("Pauling file corrections applied.")

        # Now some CIF's dont have occupancy....
        if "atom_site_type_symbol" in data.labels and \
                "atom_site_occupancy" not in data.labels:
            for this_data in data.data:
                this_data._kwargs['atom_site_occupancy'] = FakeItem(1)
            data.labels.append('atom_site_occupancy')

        # """
        # This fixes inconsistencies in naming of several magCIF tags
        # as a result of magCIF being in widespread use prior to
        # specification being finalized (on advice of Branton Campbell).
        # """

        # check for finite precision frac co-ordinates (e.g. 0.6667 instead of 0.6666666...7)
        # this can sometimes cause serious issues when applying symmetry operations
        important_fracs = (1 / 3., 2 / 3.)
        fracs_changed = False
        if 'atom_site_fract_x' in data.labels:
            for this_data in data.data:
                for label in ('atom_site_fract_x', 'atom_site_fract_y', 'atom_site_fract_z'):
                    if label in this_data._kwargs.keys():
                        frac = this_data._kwargs[label].raw_value
                        for comparison_frac in important_fracs:
                            if abs(1 - frac / comparison_frac) < 1e-4:
                                this_data._kwargs[label].raw_value = comparison_frac
                                fracs_changed = True
        if fracs_changed:
            self.warnings.append("Some fractional co-ordinates rounded to ideal values to "
                                 "avoid issues with finite precision.")
        return data

    def _sanitize_data(self, data: StarEntry) -> StarEntry:
        #  This is where we would check for any entry problems.
        #  At the moment it's empty, but maybe later...
        return data

    def get_lattice(self, cif_index: int = 0,
                    length_strings=("a", "b", "c"),
                    angle_strings=("alpha", "beta", "gamma"),
                    lattice_type=None):
        """
        Generate the lattice from the provided lattice parameters. In the absence of all six lattice parameters, the
        crystal system and necessary parameters are parsed

        :param cif_index: Which lattice do you want. There may be more than one
        :type cif_index: int
        :param length_strings: Length parameters to be searched for
        :type length_strings: tuple
        :param angle_strings: Angle parameters to be searched for
        :type angle_strings: tuple
        :param lattice_type: Lattice system (Optional)
        :type lattice_type: str
        :return: Constructed lattice
        :rtype: Lattice
        """

        if cif_index > self.number_of_cifs:
            raise AttributeError
        data = self._cif[cif_index]['data']
        find_keys = ['cell_length_' + key for key in length_strings]
        find_keys.extend(['cell_angle_' + key for key in angle_strings])
        if lattice_type is None:
            dict_keys = ['length_' + key for key in length_strings]
            dict_keys.extend(['angle_' + key for key in angle_strings])
        else:
            dict_keys = [key for key in length_strings]
            dict_keys.extend([key for key in angle_strings])
        data_dict = dict.fromkeys(dict_keys)
        try:
            # In this case all keys are specified as the cif writer was not a moron
            for idx, key in enumerate(find_keys):
                data_dict[dict_keys[idx]] = data[key].value
            if lattice_type is None:
                lattice = Lattice.from_pars(**data_dict)
            else:
                cls = getattr(Lattice, lattice_type, None)
                if cls is None:
                    raise AttributeError
                lattice = cls(**data_dict)
            for idx, key in enumerate(dict_keys):
                obj = getattr(lattice, key)
                if hasattr(data[find_keys[idx]], 'fixed') and data[find_keys[idx]].fixed is not None:
                    obj.fixed = data[find_keys[idx]].fixed
                if hasattr(data[find_keys[idx]], 'error') and data[find_keys[idx]].error is not None:
                    obj.error = data[find_keys[idx]].error
            return lattice
        except KeyError:
            # Missing Key search for cell setting
            for lattice_label in ["symmetry_cell_setting",
                                  "space_group_crystal_system"]:
                if data.get(lattice_label):
                    lattice_type = data.get(lattice_label).value.lower()
                    try:
                        sig = signature(getattr(Lattice, lattice_type))
                        required_args = [arg for arg in sig.parameters.keys() if arg != 'interface']
                        lengths = [l for l in length_strings if l in required_args]
                        angles = [a for a in angle_strings if a in required_args]
                        return self.get_lattice(lengths, angles, lattice_type=lattice_type)
                    except AttributeError as exc:
                        self.warnings.append(str(exc))
                else:
                    return None

    def get_atoms(self, cif_index: int = 0):
        """
        Generate the an atoms list with adp if available

        :param cif_index: Which lattice do you want. There may be more than one.
        :type cif_index: int
        :return: Parsed atoms and adp
        :rtype: Atoms
        """

        if cif_index > self.number_of_cifs:
            raise AttributeError
        loops = self._cif[cif_index]['loops']

        atoms_obj_name = 'atoms'
        atoms = Atoms(atoms_obj_name)
        # We should have parsed the loop so that there is at least the following
        required_fields = ['atom_site_label', 'atom_site_type_symbol', 'atom_site_occupancy', 'atom_site_fract_x',
                           'atom_site_fract_y',
                           'atom_site_fract_z']
        our_fields = ['label', 'specie', 'occupancy', 'fract_x', 'fract_y', 'fract_z']
        found = False
        for loop in loops:
            if set(loop.labels).issuperset(set(required_fields)):
                found = True
                this_loop: StarLoop = deepcopy(loop)
                this_loop.labels = required_fields
                for idx, entry in enumerate(loop.data):
                    this_loop.data[idx]._kwargs = {}
                    for key in required_fields:
                        this_loop.data[idx]._kwargs[key] = loop.data[idx]._kwargs[key]
                atoms = this_loop.to_class(Atoms, Site,
                                           [[k1, k2] for k1, k2 in zip(our_fields, required_fields)])
                atoms.name = atoms_obj_name
                for idx0, atom in enumerate(atoms):
                    for idx, key in enumerate(our_fields):
                        obj = getattr(atom, key)
                        if hasattr(loop.data[idx0]._kwargs[required_fields[idx]], 'fixed') and \
                                loop.data[idx0]._kwargs[required_fields[idx]].fixed is not None:
                            obj.fixed = loop.data[idx0]._kwargs[required_fields[idx]].fixed
                        if hasattr(loop.data[idx0]._kwargs[required_fields[idx]], 'error') and \
                                loop.data[idx0]._kwargs[required_fields[idx]].error is not None:
                            obj.error = loop.data[idx0]._kwargs[required_fields[idx]].error
                break
        if not found:
            raise AttributeError
        # Now look for atomic displacement
        fields = ['atom_site_U_iso_or_equiv', 'atom_site_aniso_U_11',
                  'atom_site_B_iso_or_equiv', 'atom_site_aniso_B_11']
        adp_types = {'Uiso': ['Uiso'],
                     'Uani': ['U_11', 'U_12', 'U_13', 'U_22', 'U_23', 'U_33'],
                     'Biso': ['Biso'],
                     'Bani': ['B_11', 'B_12', 'B_13', 'B_22', 'B_23', 'B_33']
                     }

        found = False
        for loop in loops:
            for idx0, field in enumerate(fields):
                if field in loop.labels:
                    found = True
                    needed_labels = []
                    adp_type = 'Uiso'
                    if 'aniso' in field:
                        adp_type = 'Uani'
                        # Aniso should always be accompanied by atom_site_aniso_label
                        if 'atom_site_aniso_label' not in loop.labels and 'atom_site_label' in loop.labels:
                            needed_labels.append('atom_site_label')
                        else:
                            needed_labels.append('atom_site_aniso_label')
                        needed_labels.extend(['atom_site_aniso_U_11', 'atom_site_aniso_U_12', 'atom_site_aniso_U_13',
                                              'atom_site_aniso_U_22', 'atom_site_aniso_U_23', 'atom_site_aniso_U_33'])
                        if '_B_' in field:
                            needed_labels = [this_str.replace('_U_', '_B_') for this_str in needed_labels]
                            adp_type = 'Bani'
                    else:
                        needed_labels = ['atom_site_label', field]
                        if '_B_' in field:
                            adp_type = 'Biso'
                    these_sections = loop.to_StarSections()
                    for idx, section in enumerate(these_sections):
                        if set(loop.labels).issuperset(set(needed_labels)):
                            data_dict = {}
                            for idx2, key in enumerate(needed_labels[1:]):
                                temp_value = section.data[0]._kwargs[key].raw_value
                                if not isinstance(temp_value, Number):
                                    temp_value = 0
                                    self.append = self.warnings.append(
                                        f'Atom {section.data[0]._kwargs[needed_labels[0]].raw_value} has non-numeric '
                                        f'{key}. Setting to 0')
                                data_dict[adp_types[adp_type][idx2]] = temp_value
                            adps = AtomicDisplacement.from_pars(adp_type, **data_dict)
                            # Add the errors/fixed
                            for idx2, key in enumerate(adp_types[adp_type]):
                                obj = getattr(adps, key)
                                if hasattr(section.data[0]._kwargs[needed_labels[1 + idx2]], 'fixed') and \
                                        section.data[0]._kwargs[needed_labels[1 + idx2]].fixed is not None:
                                    obj.fixed = section.data[0]._kwargs[needed_labels[1 + idx2]].fixed
                                if hasattr(section.data[0]._kwargs[needed_labels[1 + idx2]], 'error') and \
                                        section.data[0]._kwargs[needed_labels[1 + idx2]].error is not None:
                                    obj.error = section.data[0]._kwargs[needed_labels[1 + idx2]].error

                            current_atom_label = section.data[0]._kwargs[needed_labels[0]].raw_value
                            # Add to an atom
                            if current_atom_label in atoms.atom_labels:
                                idx2 = atoms.atom_labels.index(current_atom_label)
                                atoms[idx2].add_adp(adps)
                        else:
                            raise AttributeError
                    break
        # There is no adp in the cif. Add default
        if not found:
            for atom in atoms:
                self.warnings.append('There is no ADP defined in the CIF')
                atom.add_adp('Uiso')
        return atoms

    def get_symmetry(self, cif_index: int = 0):

        data = self._cif[cif_index]['data']
        space_group = None
        # All of these keys can be upper and lower case.
        lower_labels = [key.lower() for key in data.keys()]

        def caller(str1: str, str2: str, current_sep: str) -> Tuple[bool, str]:
            """
            Simple string constructor and checker for different cif standards.

            :param str1: First part of the string
            :type str1: str
            :param str2: Second part of the string
            :type str2: str
            :param current_sep: How the string is to be joined.
            :type current_sep: str
            :return: Has been found in `lower_labels`
            :rtype: bool
            """
            test_label = str1 + current_sep + str2.lower()
            is_found = False
            if test_label in lower_labels:
                is_found = True
            if not is_found:
                test_label = test_label + '_'
                if test_label in lower_labels:
                    is_found = True
            return is_found, test_label

        def check_hm(code: str) -> dict:
            """
            Check to see if the data block contains a Hermann-Mauguin symbol

            :param code: symbol to be checked.
            :type code: str
            :return: dictionary corresponding to Hermann-Mauguin symbol if found (None otherwise)
            :rtype: dict
            """
            found_op = None
            for op in SpaceGroup2.SYMM_OPS:
                if code in [op['hermann_mauguin_fmt'], op['hermann_mauguin'], op['universal_h_m']]:
                    found_op = op
                    break
            return found_op

        def check_hall(code):
            """
            Check to see if the data block contains a Hall symbol

            :param code: symbol to be checked.
            :type code: str
            :return: dictionary corresponding to Hall symbol if found (None otherwise)
            :rtype: dict
            """
            found_op = None
            for op in SpaceGroup2.SYMM_OPS:
                if op['hall'] in [code, ' ' + code]:
                    found_op = op
                    break
            return found_op

        def check_full(code):
            """
            Attempt to check to see if the data block contains a full crystallographic symbol

            :param code: symbol to be checked.
            :type code: str
            :return: dictionary corresponding to full crystallographic symbol if found (None otherwise)
            :rtype: dict
            """
            code = sub_spgrp(code)
            found_op = None
            for key in SpaceGroup2.sgencoding.keys():
                if code in [SpaceGroup2.sgencoding[key]['full_symbol']]:
                    found_op = check_hm(key)
                    break
            return found_op

        seps = ["_", "."]
        # Do the standard H-M lookup. All of these keys may have the form:
        #   'C m c m'
        #   'C 2/c 2/m 21/m'
        #   'A m a m'
        for symmetry_label in [["symmetry_space", "group_name_H-M"],
                               ["space_group", "name_Hall"],
                               ["space_group", "name_H-M_alt"],
                               ["symmetry_space", "group_name_Hall"]
                               ]:

            found = False
            this_label = ''
            for sep in seps:
                found, this_label = caller(symmetry_label[0], symmetry_label[1], sep)
                if found:
                    break
            if not found:
                continue

            key_idx = lower_labels.index(this_label)
            real_symmetry_label = list(data.keys())[key_idx]

            sg = data.get(real_symmetry_label)
            sg = sub_spgrp(sg.value)
            for check in [check_hm, check_hall, check_full]:
                op = check(sg)
                if op is not None:
                    break
            if op is None:
                pass
            setting = ''
            if ':' in sg:
                setting = sg.split(':')[1]
            setting_additional = 'space_group.IT_coordinate_system_code'
            if setting_additional.lower() in lower_labels:
                key_idx = lower_labels.index(setting_additional.lower())
                real_symmetry_setting = list(data.keys())[key_idx]
                setting = data.get(real_symmetry_setting).value
                if isinstance(setting, float) and setting.is_integer():
                    setting = int(setting)
            setting = str(setting)
            in_string = op['hermann_mauguin_fmt'].split(':')[0]
            space_group = SpaceGroup.from_pars(in_string, setting=setting)
            if space_group is not None:
                return space_group

        # All of these keys can be upper and lower case.
        # All of these keys may have the form:
        #   'C m c m'
        for symmetry_label in [["space_group", "name_H-M_ref"]]:

            found = False
            this_label = ''
            for sep in seps:
                found, this_label = caller(symmetry_label[0], symmetry_label[1], sep)
                if found:
                    break
            if not found:
                continue

            key_idx = lower_labels.index(this_label)
            real_symmetry_label = list(data.keys())[key_idx]

            sg = data.get(real_symmetry_label)
            sg = sub_spgrp(sg.value)
            for check in [check_hm]:
                op = check(sg)
                if op is not None:
                    break
            if op is None:
                pass
            space_group = SpaceGroup.from_pars(op['hermann_mauguin_fmt'])
            if space_group is not None:
                return space_group

        # All of these keys can be upper and lower case.
        # All of these keys may have the form:
        #   'C 2/c 2/m 21/m'
        for symmetry_label in [["space_group", "name_H-M_full"]]:

            found = False
            this_label = ''
            for sep in seps:
                found, this_label = caller(symmetry_label[0], symmetry_label[1], sep)
                if found:
                    break
            if not found:
                continue

            key_idx = lower_labels.index(this_label)
            real_symmetry_label = list(data.keys())[key_idx]

            sg = data.get(real_symmetry_label)
            sg = sub_spgrp(sg.value)
            for check in [check_full]:
                op = check(sg)
                if op is not None:
                    break
            if op is None:
                pass
            space_group = SpaceGroup.from_pars(op['hermann_mauguin_fmt'])

            if space_group is not None:
                return space_group

        # Sometimes there's only the spacegroup number
        for symmetry_label in [["space_group", "IT_number"],
                               ["symmetry_Int", "Tables_number"]]:

            found = False
            this_label = ''
            for sep in seps:
                found, this_label = caller(symmetry_label[0], symmetry_label[1], sep)
                if found:
                    break

            if not found:
                continue

            key_idx = lower_labels.index(this_label)
            real_symmetry_label = list(data.keys())[key_idx]

            try:
                i = int(str2float(data.get(real_symmetry_label)))
                space_group = SpaceGroup.from_int_number(i)
                break
            except ValueError:
                continue
        return space_group

    @property
    def has_errors(self):
        """
        :return: Whether there are errors/warnings detected in CIF parsing.
        """
        return len(self.warnings) > 0


class CifWriter:
    #     """
    #     A wrapper around CifFile to write CIF files from easyCore structures.
    #     """

    def __init__(self, name, *args, decimal_places: int = 8):

        self.name = name
        self._items = list(args)
        self.decimal_places = decimal_places
        self._cif = self._create_cif_obj()

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items
        self._cif = self._create_cif_obj()

    def _create_cif_obj(self) -> dict:

        atoms_must = ['label', 'specie', 'occupancy', 'fract_x', 'fract_y', 'fract_z']
        atoms_must_conv = ['atom_site_label', 'atom_site_type_symbol', 'atom_site_occupancy', 'atom_site_fract_x',
                           'atom_site_fract_y', 'atom_site_fract_z']
        atoms_optional = ['adp_type', 'Biso', 'Uiso']
        atoms_optional_conv = ['atom_site_adp_type', 'atom_site_B_iso_or_equiv', 'atom_site_U_iso_or_equiv']

        adp_U_must = ['label', 'U_11', 'U_12', 'U_13', 'U_22', 'U_23', 'U_33']
        adp_B_must = [item.replace('U_', 'B_') for item in adp_U_must]
        adp_U_must_conv = ['atom_site_aniso_label', 'atom_site_adp_type', 'atom_site_aniso_U_11',
                           'atom_site_aniso_U_12',
                           'atom_site_aniso_U_13',
                           'atom_site_aniso_U_22', 'atom_site_aniso_U_23', 'atom_site_aniso_U_33']
        adp_B_must_conv = [item.replace('U_', 'B_') for item in adp_U_must_conv]

        lattice_must = ['length_a', 'length_b', 'length_c', 'angle_alpha', 'angle_beta', 'angle_gamma']
        lattice_conv = ['cell_length_a', 'cell_length_b', 'cell_length_c',
                        'cell_angle_alpha', 'cell_angle_beta', 'cell_angle_gamma']

        sg_must = ['_space_group_HM_name']
        sg_conv = ['space_group_name_H-M_alt']

        blocks = {'header': StarHeader(self.name), 'loops': [], 'data': {}}

        def parse_block(item: StarLoop):
            if set(item.labels).issuperset(set(atoms_must)):
                labels = atoms_must_conv.copy()
                for idx2, option in enumerate(atoms_optional):
                    if option in item.labels:
                        labels.append(atoms_optional_conv[idx2])
                item.labels = labels
            elif any(['U_' in opt for opt in item.labels]):
                item.labels = adp_U_must_conv.copy()
            elif any(['B_' in opt for opt in item.labels]):
                item.labels = adp_B_must_conv.copy()

        def parse_section(item: StarSection):
            if set(item.labels).issuperset(set(lattice_must)):
                item.labels = lattice_conv
            if set(item.labels).issuperset(set(sg_must)):
                for idx, label in enumerate(sg_must):
                    if label in item.labels:
                        item.labels[item.labels.index(label)] = sg_conv[idx]

        def parse_entry(item: StarEntry):
            if item.name in sg_must:
                item.name = sg_conv[sg_must.index(item.name)]

        for idx, entry_item in enumerate(self._items):
            block = self.items[idx].to_star()
            if isinstance(block, list):
                for item in block:
                    parse_block(item)
                blocks['loops'].extend(block)
            elif isinstance(block, StarLoop):
                parse_block(block)
                blocks['loops'].append(block)
            elif isinstance(block, StarSection):
                parse_section(block)
                entries = block.to_StarEntries()
                for entry in entries:
                    blocks['data'][entry.name] = entry
            elif isinstance(block, StarEntry):
                parse_entry(block)
                blocks['data'][block.name] = block
        return blocks

    def __str__(self) -> str:
        out_str = ''
        if self._cif['header']:
            out_str += str(self._cif['header']) + '\n\n'

            for key in self._cif['data'].keys():
                out_str += str(self._cif['data'][key]) + '\n'
            out_str += '\n'
            for item in self._cif['loops']:
                out_str += str(item) + '\n'
        return out_str

    @classmethod
    def from_CifParser(cls, cif_parser: CifParser):

        obj = []
        for idx in range(cif_parser.number_of_cifs):
            this_obj = cls(cif_parser._cif[idx]['header'].name)
            this_obj._cif = cif_parser._cif[idx]
            obj.append(this_obj)
        if len(obj) == 1:
            obj = obj[0]
        return obj


def str2float(text):
    """
    Remove uncertainty brackets from strings and return the float.
    """

    try:
        # Note that the ending ) is sometimes missing. That is why the code has
        # been modified to treat it as optional. Same logic applies to lists.
        return float(re.sub(r"\(.+\)*", "", text))
    except TypeError:
        if isinstance(text, list) and len(text) == 1:
            return float(re.sub(r"\(.+\)*", "", text[0]))
    except ValueError as ex:
        if text.strip() == ".":
            return 0
        raise ex
