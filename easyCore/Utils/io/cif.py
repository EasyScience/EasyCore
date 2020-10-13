__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import os
import re
from functools import partial
from io import TextIOWrapper, StringIO
from pathlib import Path
from typing import Union
from copy import deepcopy
from inspect import signature
from numbers import Number
from easyCore.Elements.Basic.AtomicDisplacement import AtomicDisplacement
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Atoms, Site
# from easyCore.Symmetry.SymOp import SymmOp
from easyCore.Symmetry.groups import SYMM_DATA
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup

from easyCore.Utils.io.star import StarCollection, StarEntry, StarLoop, FakeItem, FakeCore, StarHeader, StarSection

sub_spgrp = partial(re.sub, r"[\s_]", "")
space_groups = {sub_spgrp(k): k for k in SYMM_DATA['space_group_encoding'].keys()}  # type: ignore
space_groups.update({sub_spgrp(k): k for k in SYMM_DATA['space_group_encoding'].keys()})  # type: ignore


class CifIO:

    def __init__(self, parser: 'CifParser' = None):
        self._parser = parser
        self._writer = None
        if parser is not None:
            self._writer = CifWriter.from_CifParser(parser)

    def use_objects(self, name, *args):
        self._writer = CifWriter(name, *args)
        self._parser = CifParser.from_string(str(self._writer))

    @classmethod
    def from_objects(cls, name, *args):
        obj = cls()
        obj._writer = CifWriter(name, *args)
        obj._parser = CifParser.from_string(str(obj._writer))
        return obj

    @classmethod
    def from_cif_str(cls, in_str: str):
        parser = CifParser(in_str)
        return cls(parser)

    @classmethod
    def from_file(cls, file_path: Union[Path, TextIOWrapper]):
        parser = CifParser(file_path)
        return cls(parser)

    def to_string(self):
        return str(self)

    def to_file(self, file_name: Union[str, Path, TextIOWrapper]):
        with open(file_name, 'w') as writer:
            writer.write(str(self))

    def __str__(self):
        out_str = ''
        if self._writer is not None:
            out_str = str(self._writer)
        return out_str

    def to_crystal_form(self):
        if self._parser is None:
            raise AttributeError
        return self._parser._cif['header'].name, {'cell':       self._parser.get_lattice(),
                                                  'spacegroup': self._parser.get_symmetry(),
                                                  'atoms':      self._parser.get_atoms()
                                                  }


class CifParser:
    """
    Parses a CIF file. Attempts to fix CIFs that are out-of-spec, but will
    issue warnings if corrections applied. These are also stored in the
    CifParser's errors attribute.
    """

    def __init__(self, filename: Union[str, Path, TextIOWrapper], occupancy_tolerance=1., site_tolerance=1e-4):
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
        if isinstance(filename, Path) and os.path.isfile(filename):
            self._cif = StarCollection.from_file(filename)
        elif isinstance(filename, (TextIOWrapper, StringIO)):
            self._cif = StarCollection.from_string(filename.read())
        else:
            self._cif = StarCollection.from_string(filename)

        # store if CIF contains features from non-core CIF dictionaries
        # e.g. magCIF
        self.feature_flags = {}
        self.warnings = []

        def is_magcif():
            """
            Checks to see if file appears to be a magCIF file (heuristic).
            """
            # Doesn't seem to be a canonical way to test if file is magCIF or
            # not, so instead check for magnetic symmetry datanames
            prefixes = ['space_group_magn', 'atom_site_moment',
                        'space_group_symop_magn']
            for prefix in prefixes:
                if prefix in self._cif['data'].keys():
                    return True
            return False

        self.feature_flags['magcif'] = is_magcif()

        def is_magcif_incommensurate():
            """
            Checks to see if file contains an incommensurate magnetic
            structure (heuristic).
            """
            # Doesn't seem to be a canonical way to test if magCIF file
            # describes incommensurate strucure or not, so instead check
            # for common datanames
            if not self.feature_flags["magcif"]:
                return False
            prefixes = ['cell_modulation_dimension', 'cell_wave_vector']
            for prefix in prefixes:
                if prefix in self._cif['data'].keys():
                    return True
            return False

        self.feature_flags['magcif_incommensurate'] = is_magcif_incommensurate()

        new_data = {}
        for k in self._cif['data'].keys():
            # pass individual CifBlocks to _sanitize_data
            obj = self._sanitize_data(self._cif['data'][k])
            new_data[obj.name] = obj
        self._cif['data'] = new_data

        for idx, loop in enumerate(self._cif['loops']):
            self._cif['loops'][idx] = self._sanitize_loop(loop)

    @classmethod
    def from_string(cls, cif_string, occupancy_tolerance=1.):
        """
        Creates a CifParser from a string.
        Args:
            cif_string (str): String representation of a CIF.
            occupancy_tolerance (float): If total occupancy of a site is
                between 1 and occupancy_tolerance, the occupancies will be
                scaled down to 1.
        Returns:
            CifParser
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

        """
        This part of the code deals with handling formats of data as found in
        CIF files extracted from the Springer Materials/Pauling File
        databases, and that are different from standard ICSD formats.
        """

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

        """
        This fixes inconsistencies in naming of several magCIF tags
        as a result of magCIF being in widespread use prior to
        specification being finalized (on advice of Branton Campbell).
        """

        if self.feature_flags["magcif"]:

            raise NotImplementedError

            # CIF-1 style has all underscores, interim standard
            # had period before magn instead of before the final
            # component (e.g. xyz)
            # we want to standardize on a specific key, to simplify
            # parsing code
            correct_keys = ["_space_group_symop_magn_operation.xyz",
                            "_space_group_symop_magn_centering.xyz",
                            "_space_group_magn.name_BNS",
                            "_space_group_magn.number_BNS",
                            "_atom_site_moment_crystalaxis_x",
                            "_atom_site_moment_crystalaxis_y",
                            "_atom_site_moment_crystalaxis_z",
                            "_atom_site_moment_label"]

            # cannot mutate OrderedDict during enumeration,
            # so store changes we want to make
            changes_to_make = {}

            for original_key in data.data:
                for correct_key in correct_keys:
                    # convert to all underscore
                    trial_key = "_".join(correct_key.split("."))
                    test_key = "_".join(original_key.split("."))
                    if trial_key == test_key:
                        changes_to_make[correct_key] = original_key

            # make changes
            for correct_key, original_key in changes_to_make.items():
                data.data[correct_key] = data.data[original_key]

            # renamed_keys maps interim_keys to final_keys
            renamed_keys = {
                "_magnetic_space_group.transform_to_standard_Pp_abc":
                    "_space_group_magn.transform_BNS_Pp_abc"}
            changes_to_make = {}

            for interim_key, final_key in renamed_keys.items():
                if data.data.get(interim_key):
                    changes_to_make[final_key] = interim_key

            if len(changes_to_make) > 0:
                self.warnings.append("Keys changed to match new magCIF specification.")

            for final_key, interim_key in changes_to_make.items():
                data.data[final_key] = data.data[interim_key]

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
        #  This is where we would check for any entry problems....
        return data

    # def _unique_coords(self, coords_in, magmoms_in=None, lattice=None):
    #     """
    #     Generate unique coordinates using coord and symmetry positions
    #     and also their corresponding magnetic moments, if supplied.
    #     """
    #     coords = []
    #     if magmoms_in:
    #         raise NotImplementedError
    #         # magmoms = []
    #         # if len(magmoms_in) != len(coords_in):
    #         #     raise ValueError
    #         # for tmp_coord, tmp_magmom in zip(coords_in, magmoms_in):
    #         #     for op in self.symmetry_operations:
    #         #         coord = op.operate(tmp_coord)
    #         #         coord = np.array([i - math.floor(i) for i in coord])
    #         #         if isinstance(op, MagSymmOp):
    #         #             # Up to this point, magmoms have been defined relative
    #         #             # to crystal axis. Now convert to Cartesian and into
    #         #             # a Magmom object.
    #         #             magmom = Magmom.from_moment_relative_to_crystal_axes(
    #         #                 op.operate_magmom(tmp_magmom),
    #         #                 lattice=lattice
    #         #             )
    #         #         else:
    #         #             magmom = Magmom(tmp_magmom)
    #         #         if not in_coord_list_pbc(coords, coord,
    #         #                                  atol=self._site_tolerance):
    #         #             coords.append(coord)
    #         #             magmoms.append(magmom)
    #         # return coords, magmoms
    #
    #     for tmp_coord in coords_in:
    #         for op in self.symmetry_operations:
    #             coord = op.operate(tmp_coord)
    #             coord = np.array([i - math.floor(i) for i in coord])
    #             if not in_coord_list_pbc(coords, coord,
    #                                      atol=self._site_tolerance):
    #                 coords.append(coord)
    #     return coords, [Magmom(0)] * len(coords)  # return dummy magmoms

    def get_lattice(self, length_strings=("a", "b", "c"),
                    angle_strings=("alpha", "beta", "gamma"),
                    lattice_type=None):
        """
        Generate the lattice from the provided lattice parameters. In
        the absence of all six lattice parameters, the crystal system
        and necessary parameters are parsed
        """
        data = self._cif['data']
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
                lattice = Cell.from_pars(**data_dict)
            else:
                cls = getattr(Cell, lattice_type, None)
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
                        sig = signature(getattr(Cell, lattice_type))
                        required_args = [arg for arg in sig.parameters.keys() if arg != 'interface']
                        lengths = [l for l in length_strings if l in required_args]
                        angles = [a for a in angle_strings if a in required_args]
                        return self.get_lattice(lengths, angles, lattice_type=lattice_type)
                    except AttributeError as exc:
                        self.warnings.append(str(exc))
                else:
                    return None

    def get_atoms(self):
        loops = self._cif['loops']
        atoms = Atoms('sites')
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
                                    self.warnings.append(
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

    def get_symmetry(self):
        data = self._cif['data']
        space_group = None
        for symmetry_label in ["symmetry_space_group_name_H-M",
                               "symmetry_space_group_name_H_M",
                               "symmetry_space_group_name_H-M_",
                               "symmetry_space_group_name_H_M_",
                               "space_group_name_Hall",
                               "space_group_name_Hall_",
                               "space_group_name_H-M_alt",
                               "space_group_name_H-M_alt_",
                               "symmetry_space_group_name_hall",
                               "symmetry_space_group_name_hall_",
                               "symmetry_space_group_name_h-m",
                               "symmetry_space_group_name_h-m_"]:
            sg = data.get(symmetry_label, None)
            if sg:
                sg = sub_spgrp(sg.value)
                try:
                    spg = space_groups.get(sg, None)
                    if spg:
                        space_group = SpaceGroup.from_pars(spg)
                        break
                except ValueError:
                    # Ignore any errors
                    pass
        if space_group is None:
            for symmetry_label in ["_space_group_IT_number",
                                   "_space_group_IT_number_",
                                   "_symmetry_Int_Tables_number",
                                   "_symmetry_Int_Tables_number_"]:
                if data.get(symmetry_label):
                    try:
                        i = int(str2float(data.get(symmetry_label)))
                        space_group = SpaceGroup.from_int_number(i)
                        break
                    except ValueError:
                        continue
        return space_group

    # def get_symops(self):
    #     """
    #     In order to generate symmetry equivalent positions, the symmetry
    #     operations are parsed. If the symops are not present, the space
    #     group symbol is parsed, and symops are generated.
    #     """
    #     data = self._cif['data']
    #     symops = []
    #     for symmetry_label in ["symmetry_equiv_pos_as_xyz",
    #                            "symmetry_equiv_pos_as_xyz_",
    #                            "space_group_symop_operation_xyz",
    #                            "space_group_symop_operation_xyz_"]:
    #         if data.get(symmetry_label, None):
    #             xyz = data.get(symmetry_label)
    #             if isinstance(xyz, str):
    #                 msg = "A 1-line symmetry op P1 CIF is detected!"
    #                 self.warnings.append(msg)
    #                 xyz = [xyz]
    #             try:
    #                 symops = [SymmOp.from_xyz_string(s)
    #                           for s in xyz]
    #                 break
    #             except ValueError:
    #                 continue
    #     if not symops:
    #         # Try to parse symbol
    #         for symmetry_label in ["symmetry_space_group_name_H-M",
    #                                "symmetry_space_group_name_H_M",
    #                                "symmetry_space_group_name_H-M_",
    #                                "symmetry_space_group_name_H_M_",
    #                                "space_group_name_Hall",
    #                                "space_group_name_Hall_",
    #                                "space_group_name_H-M_alt",
    #                                "space_group_name_H-M_alt_",
    #                                "symmetry_space_group_name_hall",
    #                                "symmetry_space_group_name_hall_",
    #                                "symmetry_space_group_name_h-m",
    #                                "symmetry_space_group_name_h-m_"]:
    #             sg = data.get(symmetry_label, None)
    #             if sg:
    #                 sg = sub_spgrp(sg)
    #                 try:
    #                     spg = space_groups.get(sg, None)
    #                     if spg:
    #                         symops = SpaceGroup(spg).symmetry_opts
    #                         msg = "No _symmetry_equiv_pos_as_xyz type key found. " \
    #                               "Spacegroup from %s used." % symmetry_label
    #                         warnings.warn(msg)
    #                         self.warnings.append(msg)
    #                         break
    #                 except ValueError:
    #                     # Ignore any errors
    #                     pass
    #
    #                 try:
    #                     for d in _get_cod_data():
    #                         if sg == re.sub(r"\s+", "",
    #                                         d["hermann_mauguin"]):
    #                             xyz = d["symops"]
    #                             symops = [SymmOp.from_xyz_string(s)
    #                                       for s in xyz]
    #                             msg = "No _symmetry_equiv_pos_as_xyz type key found. " \
    #                                   "Spacegroup from %s used." % symmetry_label
    #                             warnings.warn(msg)
    #                             self.warnings.append(msg)
    #                             break
    #                 except Exception:
    #                     continue
    #
    #                 if symops:
    #                     break
    #     if not symops:
    #         # Try to parse International number
    #         for symmetry_label in ["_space_group_IT_number",
    #                                "_space_group_IT_number_",
    #                                "_symmetry_Int_Tables_number",
    #                                "_symmetry_Int_Tables_number_"]:
    #             if data.data.get(symmetry_label):
    #                 try:
    #                     i = int(str2float(data.data.get(symmetry_label)))
    #                     symops = SpaceGroup.from_int_number(i).symmetry_ops
    #                     break
    #                 except ValueError:
    #                     continue
    #
    #     if not symops:
    #         msg = "No _symmetry_equiv_pos_as_xyz type key found. " \
    #               "Defaulting to P1."
    #         warnings.warn(msg)
    #         self.warnings.append(msg)
    #         symops = [SymmOp.from_xyz_string(s) for s in ['x', 'y', 'z']]
    #
    #     return symops
    #
    # def get_magsymops(self, data):
    #     """
    #     Equivalent to get_symops except for magnetic symmetry groups.
    #     Separate function since additional operation for time reversal symmetry
    #     (which changes magnetic moments on sites) needs to be returned.
    #     """
    #     magsymmops = []
    #
    #     # check to see if magCIF file explicitly contains magnetic symmetry operations
    #     if data.data.get("_space_group_symop_magn_operation.xyz"):
    #
    #         xyzt = data.data.get("_space_group_symop_magn_operation.xyz")
    #         if isinstance(xyzt, str):
    #             xyzt = [xyzt]
    #         magsymmops = [MagSymmOp.from_xyzt_string(s) for s in xyzt]
    #
    #         if data.data.get("_space_group_symop_magn_centering.xyz"):
    #
    #             xyzt = data.data.get("_space_group_symop_magn_centering.xyz")
    #             if isinstance(xyzt, str):
    #                 xyzt = [xyzt]
    #             centering_symops = [MagSymmOp.from_xyzt_string(s) for s in xyzt]
    #
    #             all_ops = []
    #             for op in magsymmops:
    #                 for centering_op in centering_symops:
    #                     new_translation = [i - np.floor(i) for i
    #                                        in
    #                                        op.translation_vector + centering_op.translation_vector]
    #                     new_time_reversal = op.time_reversal * centering_op.time_reversal
    #                     all_ops.append(
    #                         MagSymmOp.from_rotation_and_translation_and_time_reversal(
    #                             rotation_matrix=op.rotation_matrix,
    #                             translation_vec=new_translation,
    #                             time_reversal=new_time_reversal))
    #             magsymmops = all_ops
    #
    #     # else check to see if it specifies a magnetic space group
    #     elif data.data.get("_space_group_magn.name_BNS") or data.data.get(
    #             "_space_group_magn.number_BNS"):
    #
    #         if data.data.get("_space_group_magn.name_BNS"):
    #             # get BNS label for MagneticSpaceGroup()
    #             id = data.data.get("_space_group_magn.name_BNS")
    #         else:
    #             # get BNS number for MagneticSpaceGroup()
    #             # by converting string to list of ints
    #             id = list(map(int, (
    #                 data.data.get("_space_group_magn.number_BNS").split("."))))
    #
    #         if data.data.get("_space_group_magn.transform_BNS_Pp_abc"):
    #             if data.data.get(
    #                     "_space_group_magn.transform_BNS_Pp_abc") != "a,b,c;0,0,0":
    #                 jf = data.data.get("_space_group_magn.transform_BNS_Pp_abc")
    #                 msg = MagneticSpaceGroup(id, jf)
    #
    #         elif data.data.get("_space_group_magn.transform_BNS_Pp"):
    #             return NotImplementedError(
    #                 "Incomplete specification to implement.")
    #         else:
    #             msg = MagneticSpaceGroup(id)
    #
    #         magsymmops = msg.symmetry_ops
    #
    #     if not magsymmops:
    #         msg = "No magnetic symmetry detected, using primitive symmetry."
    #         warnings.warn(msg)
    #         self.warnings.append(msg)
    #         magsymmops = [MagSymmOp.from_xyzt_string("x, y, z, 1")]
    #
    #     return magsymmops
    #
    # @staticmethod
    # def parse_oxi_states(data):
    #     """
    #     Parse oxidation states from data dictionary
    #     """
    #     try:
    #         oxi_states = {
    #             data["_atom_type_symbol"][i]:
    #                 str2float(data["_atom_type_oxidation_number"][i])
    #             for i in range(len(data["_atom_type_symbol"]))}
    #         # attempt to strip oxidation state from _atom_type_symbol
    #         # in case the label does not contain an oxidation state
    #         for i, symbol in enumerate(data["_atom_type_symbol"]):
    #             oxi_states[re.sub(r"\d?[\+,\-]?$", "", symbol)] = \
    #                 str2float(data["_atom_type_oxidation_number"][i])
    #
    #     except (ValueError, KeyError):
    #         oxi_states = None
    #     return oxi_states
    #
    # @staticmethod
    # def parse_magmoms(data, lattice=None):
    #     """
    #     Parse atomic magnetic moments from data dictionary
    #     """
    #     if lattice is None:
    #         raise Exception(
    #             'Magmoms given in terms of crystal axes in magCIF spec.')
    #     try:
    #         magmoms = {
    #             data["_atom_site_moment_label"][i]:
    #                 np.array(
    #                     [str2float(data["_atom_site_moment_crystalaxis_x"][i]),
    #                      str2float(data["_atom_site_moment_crystalaxis_y"][i]),
    #                      str2float(data["_atom_site_moment_crystalaxis_z"][i])]
    #                 )
    #             for i in range(len(data["_atom_site_moment_label"]))
    #         }
    #     except (ValueError, KeyError):
    #         return None
    #     return magmoms
    #
    # def _parse_symbol(self, sym):
    #     """
    #     Parse a string with a symbol to extract a string representing an element.
    #     Args:
    #         sym (str): A symbol to be parsed.
    #     Returns:
    #         A string with the parsed symbol. None if no parsing was possible.
    #     """
    #     # Common representations for elements/water in cif files
    #     # TODO: fix inconsistent handling of water
    #     special = {"Hw":  "H", "Ow": "O", "Wat": "O",
    #                "wat": "O", "OH": "", "OH2": "", "NO3": "N"}
    #
    #     parsed_sym = None
    #     # try with special symbols, otherwise check the first two letters,
    #     # then the first letter alone. If everything fails try extracting the
    #     # first letters.
    #     m_sp = re.match("|".join(special.keys()), sym)
    #     if m_sp:
    #         parsed_sym = special[m_sp.group()]
    #     elif Element.is_valid_symbol(sym[:2].title()):
    #         parsed_sym = sym[:2].title()
    #     elif Element.is_valid_symbol(sym[0].upper()):
    #         parsed_sym = sym[0].upper()
    #     else:
    #         m = re.match(r"w?[A-Z][a-z]*", sym)
    #         if m:
    #             parsed_sym = m.group()
    #
    #     if parsed_sym is not None and (m_sp or not re.match(r"{}\d*".format(parsed_sym), sym)):
    #         msg = "{} parsed as {}".format(sym, parsed_sym)
    #         warnings.warn(msg)
    #         self.warnings.append(msg)
    #
    #     return parsed_sym
    #
    # def _get_structure(self, data, primitive):
    #     """
    #     Generate structure from part of the cif.
    #     """
    #
    #     def get_num_implicit_hydrogens(sym):
    #         num_h = {"Wat": 2, "wat": 2, "O-H": 1}
    #         return num_h.get(sym[:3], 0)
    #
    #     lattice = self.get_lattice(data)
    #
    #     # if magCIF, get magnetic symmetry moments and magmoms
    #     # else standard CIF, and use empty magmom dict
    #     if self.feature_flags["magcif_incommensurate"]:
    #         raise NotImplementedError(
    #             "Incommensurate structures not currently supported.")
    #     if self.feature_flags["magcif"]:
    #         self.symmetry_operations = self.get_magsymops(data)
    #         magmoms = self.parse_magmoms(data, lattice=lattice)
    #     else:
    #         self.symmetry_operations = self.get_symops(data)
    #         magmoms = {}
    #
    #     oxi_states = self.parse_oxi_states(data)
    #
    #     coord_to_species = OrderedDict()
    #     coord_to_magmoms = OrderedDict()
    #
    #     def get_matching_coord(coord):
    #         keys = list(coord_to_species.keys())
    #         coords = np.array(keys)
    #         for op in self.symmetry_operations:
    #             c = op.operate(coord)
    #             inds = find_in_coord_list_pbc(coords, c,
    #                                           atol=self._site_tolerance)
    #             # cant use if inds, because python is dumb and np.array([0]) evaluates
    #             # to False
    #             if len(inds):
    #                 return keys[inds[0]]
    #         return False
    #
    #     for i in range(len(data["_atom_site_label"])):
    #         try:
    #             # If site type symbol exists, use it. Otherwise, we use the
    #             # label.
    #             symbol = self._parse_symbol(data["_atom_site_type_symbol"][i])
    #             num_h = get_num_implicit_hydrogens(
    #                 data["_atom_site_type_symbol"][i])
    #         except KeyError:
    #             symbol = self._parse_symbol(data["_atom_site_label"][i])
    #             num_h = get_num_implicit_hydrogens(data["_atom_site_label"][i])
    #         if not symbol:
    #             continue
    #
    #         if oxi_states is not None:
    #             o_s = oxi_states.get(symbol, 0)
    #             # use _atom_site_type_symbol if possible for oxidation state
    #             if "_atom_site_type_symbol" in data.data.keys():
    #                 oxi_symbol = data["_atom_site_type_symbol"][i]
    #                 o_s = oxi_states.get(oxi_symbol, o_s)
    #             try:
    #                 el = Species(symbol, o_s)
    #             except Exception:
    #                 el = DummySpecies(symbol, o_s)
    #         else:
    #             el = get_el_sp(symbol)
    #
    #         x = str2float(data["_atom_site_fract_x"][i])
    #         y = str2float(data["_atom_site_fract_y"][i])
    #         z = str2float(data["_atom_site_fract_z"][i])
    #         magmom = magmoms.get(data["_atom_site_label"][i],
    #                              np.array([0, 0, 0]))
    #
    #         try:
    #             occu = str2float(data["_atom_site_occupancy"][i])
    #         except (KeyError, ValueError):
    #             occu = 1
    #
    #         if occu > 0:
    #             coord = (x, y, z)
    #             match = get_matching_coord(coord)
    #             comp_d = {el: occu}
    #             if num_h > 0:
    #                 comp_d["H"] = num_h
    #                 self.warnings.append("Structure has implicit hydrogens defined, "
    #                                      "parsed structure unlikely to be suitable for use "
    #                                      "in calculations unless hydrogens added.")
    #             comp = Composition(comp_d)
    #             if not match:
    #                 coord_to_species[coord] = comp
    #                 coord_to_magmoms[coord] = magmom
    #             else:
    #                 coord_to_species[match] += comp
    #                 # disordered magnetic not currently supported
    #                 coord_to_magmoms[match] = None
    #
    #     sum_occu = [sum(c.values()) for c in coord_to_species.values()
    #                 if not set(c.elements) == {Element("O"), Element("H")}]
    #     if any([o > 1 for o in sum_occu]):
    #         msg = "Some occupancies ({}) sum to > 1! If they are within " \
    #               "the occupancy_tolerance, they will be rescaled. " \
    #               "The current occupancy_tolerance is set to: {}".format(sum_occu, self._occupancy_tolerance)
    #         warnings.warn(msg)
    #         self.warnings.append(msg)
    #
    #     allspecies = []
    #     allcoords = []
    #     allmagmoms = []
    #     allhydrogens = []
    #
    #     # check to see if magCIF file is disordered
    #     if self.feature_flags["magcif"]:
    #         for k, v in coord_to_magmoms.items():
    #             if v is None:
    #                 # Proposed solution to this is to instead store magnetic
    #                 # moments as Species 'spin' property, instead of site
    #                 # property, but this introduces ambiguities for end user
    #                 # (such as unintended use of `spin` and Species will have
    #                 # fictious oxidation state).
    #                 raise NotImplementedError(
    #                     'Disordered magnetic structures not currently supported.')
    #
    #     if coord_to_species.items():
    #         for comp, group in groupby(
    #                 sorted(list(coord_to_species.items()), key=lambda x: x[1]),
    #                 key=lambda x: x[1]):
    #             tmp_coords = [site[0] for site in group]
    #             tmp_magmom = [coord_to_magmoms[tmp_coord] for tmp_coord in
    #                           tmp_coords]
    #
    #             if self.feature_flags["magcif"]:
    #                 coords, magmoms = self._unique_coords(tmp_coords,
    #                                                       magmoms_in=tmp_magmom,
    #                                                       lattice=lattice)
    #             else:
    #                 coords, magmoms = self._unique_coords(tmp_coords)
    #
    #             if set(comp.elements) == {Element("O"), Element("H")}:
    #                 # O with implicit hydrogens
    #                 im_h = comp["H"]
    #                 species = Composition({"O": comp["O"]})
    #             else:
    #                 im_h = 0
    #                 species = comp
    #
    #             allhydrogens.extend(len(coords) * [im_h])
    #             allcoords.extend(coords)
    #             allspecies.extend(len(coords) * [species])
    #             allmagmoms.extend(magmoms)
    #
    #         # rescale occupancies if necessary
    #         for i, species in enumerate(allspecies):
    #             totaloccu = sum(species.values())
    #             if 1 < totaloccu <= self._occupancy_tolerance:
    #                 allspecies[i] = species / totaloccu
    #
    #     if allspecies and len(allspecies) == len(allcoords) \
    #             and len(allspecies) == len(allmagmoms):
    #         site_properties = dict()
    #         if any(allhydrogens):
    #             assert len(allhydrogens) == len(allcoords)
    #             site_properties["implicit_hydrogens"] = allhydrogens
    #
    #         if self.feature_flags["magcif"]:
    #             site_properties["magmom"] = allmagmoms
    #
    #         if len(site_properties) == 0:
    #             site_properties = None
    #
    #         struct = Structure(lattice, allspecies, allcoords,
    #                            site_properties=site_properties)
    #
    #         struct = struct.get_sorted_structure()
    #
    #         if primitive and self.feature_flags['magcif']:
    #             struct = struct.get_primitive_structure(use_site_props=True)
    #         elif primitive:
    #             struct = struct.get_primitive_structure()
    #             struct = struct.get_reduced_structure()
    #
    #         return struct
    #
    # def get_structures(self, primitive=True):
    #     """
    #     Return list of structures in CIF file. primitive boolean sets whether a
    #     conventional cell structure or primitive cell structure is returned.
    #     Args:
    #         primitive (bool): Set to False to return conventional unit cells.
    #             Defaults to True. With magnetic CIF files, will return primitive
    #             magnetic cell which may be larger than nuclear primitive cell.
    #     Returns:
    #         List of Structures.
    #     """
    #     structures = []
    #     for i, d in enumerate(self._cif.data.values()):
    #         try:
    #             s = self._get_structure(d, primitive)
    #             if s:
    #                 structures.append(s)
    #         except (KeyError, ValueError) as exc:
    #             # Warn the user (Errors should never pass silently)
    #             # A user reported a problem with cif files produced by Avogadro
    #             # in which the atomic coordinates are in Cartesian coords.
    #             self.warnings.append(str(exc))
    #             warnings.warn("No structure parsed for %d structure in CIF. Section of CIF file below." % (i + 1))
    #             warnings.warn(str(d))
    #             warnings.warn("Error is %s." % str(exc))
    #
    #     if self.warnings:
    #         warnings.warn("Issues encountered while parsing CIF: %s" % "\n".join(self.warnings))
    #     if len(structures) == 0:
    #         raise ValueError("Invalid cif file with no structures!")
    #     return structures
    #
    # def get_bibtex_string(self):
    #     """
    #     Get BibTeX reference from CIF file.
    #     :param data:
    #     :return: BibTeX string
    #     """
    #
    #     try:
    #         from pybtex.database import BibliographyData, Entry
    #     except ImportError:
    #         raise RuntimeError("Bibliographic data extraction requires pybtex.")
    #
    #     bibtex_keys = {'author':     ('_publ_author_name', '_citation_author_name'),
    #                    'title':      ('_publ_section_title', '_citation_title'),
    #                    'journal':    ('_journal_name_full', '_journal_name_abbrev',
    #                                   '_citation_journal_full', '_citation_journal_abbrev'),
    #                    'volume':     ('_journal_volume', '_citation_journal_volume'),
    #                    'year':       ('_journal_year', '_citation_year'),
    #                    'number':     ('_journal_number', '_citation_number'),
    #                    'page_first': ('_journal_page_first', '_citation_page_first'),
    #                    'page_last':  ('_journal_page_last', '_citation_page_last'),
    #                    'doi':        ('_journal_DOI', '_citation_DOI')}
    #
    #     entries = {}
    #
    #     # TODO: parse '_publ_section_references' when it exists?
    #     # TODO: CIF specification supports multiple citations.
    #
    #     for idx, data in enumerate(self._cif.data.values()):
    #
    #         # convert to lower-case keys, some cif files inconsistent
    #         data = {k.lower(): v for k, v in data.data.items()}
    #
    #         bibtex_entry = {}
    #
    #         for field, tags in bibtex_keys.items():
    #             for tag in tags:
    #                 if tag in data:
    #                     if isinstance(data[tag], list):
    #                         bibtex_entry[field] = data[tag][0]
    #                     else:
    #                         bibtex_entry[field] = data[tag]
    #
    #         # convert to bibtex author format ('and' delimited)
    #         if 'author' in bibtex_entry:
    #             # separate out semicolon authors
    #             if isinstance(bibtex_entry["author"], str):
    #                 if ";" in bibtex_entry["author"]:
    #                     bibtex_entry["author"] = bibtex_entry["author"].split(";")
    #
    #             if isinstance(bibtex_entry['author'], list):
    #                 bibtex_entry['author'] = ' and '.join(bibtex_entry['author'])
    #
    #         # convert to bibtex page range format, use empty string if not specified
    #         if ('page_first' in bibtex_entry) or ('page_last' in bibtex_entry):
    #             bibtex_entry['pages'] = '{0}--{1}'.format(bibtex_entry.get('page_first', ''),
    #                                                       bibtex_entry.get('page_last', ''))
    #             bibtex_entry.pop('page_first', None)  # and remove page_first, page_list if present
    #             bibtex_entry.pop('page_last', None)
    #
    #         # cite keys are given as cif-reference-idx in order they are found
    #         entries['cifref{}'.format(idx)] = Entry('article', list(bibtex_entry.items()))
    #
    #     return BibliographyData(entries).to_string(bib_format='bibtex')
    #
    # def as_dict(self):
    #     """
    #     :return: MSONable dict
    #     """
    #     d = OrderedDict()
    #     for k, v in self._cif.data.items():
    #         d[k] = {}
    #         for k2, v2 in v.data.items():
    #             d[k][k2] = v2
    #     return d

    @property
    def has_errors(self):
        """
        :return: Whether there are errors/warnings detected in CIF parsing.
        """
        return len(self.warnings) > 0


class CifWriter:

    def __init__(self, name, *args, significant_figures: int = 8):

        self.name = name
        self._items = list(args)
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
        adp_U_must_conv = ['atom_site_aniso_label', 'atom_site_adp_type','atom_site_aniso_U_11', 'atom_site_aniso_U_12',
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
    def from_CifParser(cls, cif):
        obj = cls(cif._cif['header'].name)
        obj._cif = cif._cif
        return obj


# class CifWriter:
#     """
#     A wrapper around CifFile to write CIF files from pymatgen structures.
#     """
#
#     def __init__(self, struct, symprec=None, write_magmoms=False,
#                  significant_figures=8, angle_tolerance=5.0):
#         """
#         Args:
#             struct (Structure): structure to write
#             symprec (float): If not none, finds the symmetry of the structure
#                 and writes the cif with symmetry information. Passes symprec
#                 to the SpacegroupAnalyzer.
#             write_magmoms (bool): If True, will write magCIF file. Incompatible
#                 with symprec
#             significant_figures (int): Specifies precision for formatting of floats.
#                 Defaults to 8.
#             angle_tolerance (float): Angle tolerance for symmetry finding. Passes
#                 angle_tolerance to the SpacegroupAnalyzer. Used only if symprec
#                 is not None.
#         """
#
#         if write_magmoms and symprec:
#             warnings.warn(
#                 "Magnetic symmetry cannot currently be detected by pymatgen,"
#                 "disabling symmetry detection.")
#             symprec = None
#
#         format_str = "{:.%df}" % significant_figures
#
#         block = OrderedDict()
#         loops = []
#         spacegroup = ("P 1", 1)
#         if symprec is not None:
#             sf = SpacegroupAnalyzer(struct, symprec, angle_tolerance=angle_tolerance)
#             spacegroup = (sf.get_space_group_symbol(),
#                           sf.get_space_group_number())
#             # Needs the refined struture when using symprec. This converts
#             # primitive to conventional structures, the standard for CIF.
#             struct = sf.get_refined_structure()
#
#         latt = struct.lattice
#         comp = struct.composition
#         no_oxi_comp = comp.element_composition
#         block["_symmetry_space_group_name_H-M"] = spacegroup[0]
#         for cell_attr in ['a', 'b', 'c']:
#             block["_cell_length_" + cell_attr] = format_str.format(
#                 getattr(latt, cell_attr))
#         for cell_attr in ['alpha', 'beta', 'gamma']:
#             block["_cell_angle_" + cell_attr] = format_str.format(
#                 getattr(latt, cell_attr))
#         block["_symmetry_Int_Tables_number"] = spacegroup[1]
#         block["_chemical_formula_structural"] = no_oxi_comp.reduced_formula
#         block["_chemical_formula_sum"] = no_oxi_comp.formula
#         block["_cell_volume"] = format_str.format(latt.volume)
#
#         reduced_comp, fu = no_oxi_comp.get_reduced_composition_and_factor()
#         block["_cell_formula_units_Z"] = str(int(fu))
#
#         if symprec is None:
#             block["_symmetry_equiv_pos_site_id"] = ["1"]
#             block["_symmetry_equiv_pos_as_xyz"] = ["x, y, z"]
#         else:
#             sf = SpacegroupAnalyzer(struct, symprec)
#
#             symmops = []
#             for op in sf.get_symmetry_operations():
#                 v = op.translation_vector
#                 symmops.append(SymmOp.from_rotation_and_translation(
#                     op.rotation_matrix, v))
#
#             ops = [op.as_xyz_string() for op in symmops]
#             block["_symmetry_equiv_pos_site_id"] = \
#                 ["%d" % i for i in range(1, len(ops) + 1)]
#             block["_symmetry_equiv_pos_as_xyz"] = ops
#
#         loops.append(["_symmetry_equiv_pos_site_id",
#                       "_symmetry_equiv_pos_as_xyz"])
#
#         try:
#             symbol_to_oxinum = OrderedDict([
#                 (el.__str__(),
#                  float(el.oxi_state))
#                 for el in sorted(comp.elements)])
#             block["_atom_type_symbol"] = symbol_to_oxinum.keys()
#             block["_atom_type_oxidation_number"] = symbol_to_oxinum.values()
#             loops.append(["_atom_type_symbol", "_atom_type_oxidation_number"])
#         except (TypeError, AttributeError):
#             symbol_to_oxinum = OrderedDict([(el.symbol, 0) for el in
#                                             sorted(comp.elements)])
#
#         atom_site_type_symbol = []
#         atom_site_symmetry_multiplicity = []
#         atom_site_fract_x = []
#         atom_site_fract_y = []
#         atom_site_fract_z = []
#         atom_site_label = []
#         atom_site_occupancy = []
#         atom_site_moment_label = []
#         atom_site_moment_crystalaxis_x = []
#         atom_site_moment_crystalaxis_y = []
#         atom_site_moment_crystalaxis_z = []
#         count = 0
#         if symprec is None:
#             for site in struct:
#                 for sp, occu in sorted(site.species.items()):
#                     atom_site_type_symbol.append(sp.__str__())
#                     atom_site_symmetry_multiplicity.append("1")
#                     atom_site_fract_x.append(format_str.format(site.a))
#                     atom_site_fract_y.append(format_str.format(site.b))
#                     atom_site_fract_z.append(format_str.format(site.c))
#                     atom_site_label.append("{}{}".format(sp.symbol, count))
#                     atom_site_occupancy.append(occu.__str__())
#
#                     magmom = Magmom(
#                         site.properties.get('magmom', getattr(sp, 'spin', 0)))
#                     if write_magmoms and abs(magmom) > 0:
#                         moment = Magmom.get_moment_relative_to_crystal_axes(
#                             magmom, latt)
#                         atom_site_moment_label.append(
#                             "{}{}".format(sp.symbol, count))
#                         atom_site_moment_crystalaxis_x.append(format_str.format(moment[0]))
#                         atom_site_moment_crystalaxis_y.append(format_str.format(moment[1]))
#                         atom_site_moment_crystalaxis_z.append(format_str.format(moment[2]))
#
#                     count += 1
#         else:
#             # The following just presents a deterministic ordering.
#             unique_sites = [
#                 (sorted(sites, key=lambda s: tuple([abs(x) for x in
#                                                     s.frac_coords]))[0],
#                  len(sites))
#                 for sites in sf.get_symmetrized_structure().equivalent_sites
#             ]
#             for site, mult in sorted(
#                     unique_sites,
#                     key=lambda t: (t[0].species.average_electroneg,
#                                    -t[1], t[0].a, t[0].b, t[0].c)):
#                 for sp, occu in site.species.items():
#                     atom_site_type_symbol.append(sp.__str__())
#                     atom_site_symmetry_multiplicity.append("%d" % mult)
#                     atom_site_fract_x.append(format_str.format(site.a))
#                     atom_site_fract_y.append(format_str.format(site.b))
#                     atom_site_fract_z.append(format_str.format(site.c))
#                     atom_site_label.append("{}{}".format(sp.symbol, count))
#                     atom_site_occupancy.append(occu.__str__())
#                     count += 1
#
#         block["_atom_site_type_symbol"] = atom_site_type_symbol
#         block["_atom_site_label"] = atom_site_label
#         block["_atom_site_symmetry_multiplicity"] = \
#             atom_site_symmetry_multiplicity
#         block["_atom_site_fract_x"] = atom_site_fract_x
#         block["_atom_site_fract_y"] = atom_site_fract_y
#         block["_atom_site_fract_z"] = atom_site_fract_z
#         block["_atom_site_occupancy"] = atom_site_occupancy
#         loops.append(["_atom_site_type_symbol",
#                       "_atom_site_label",
#                       "_atom_site_symmetry_multiplicity",
#                       "_atom_site_fract_x",
#                       "_atom_site_fract_y",
#                       "_atom_site_fract_z",
#                       "_atom_site_occupancy"])
#         if write_magmoms:
#             block["_atom_site_moment_label"] = atom_site_moment_label
#             block[
#                 "_atom_site_moment_crystalaxis_x"] = atom_site_moment_crystalaxis_x
#             block[
#                 "_atom_site_moment_crystalaxis_y"] = atom_site_moment_crystalaxis_y
#             block[
#                 "_atom_site_moment_crystalaxis_z"] = atom_site_moment_crystalaxis_z
#             loops.append(["_atom_site_moment_label",
#                           "_atom_site_moment_crystalaxis_x",
#                           "_atom_site_moment_crystalaxis_y",
#                           "_atom_site_moment_crystalaxis_z"])
#         d = OrderedDict()
#         d[comp.reduced_formula] = CifBlock(block, loops, comp.reduced_formula)
#         self._cf = CifFile(d)
#
#     @property
#     def ciffile(self):
#         """
#         Returns: CifFile associated with the CifWriter.
#         """
#         return self._cf
#
#     def __str__(self):
#         """
#         Returns the cif as a string.
#         """
#         return self._cf.__str__()
#
#     def write_file(self, filename):
#         """
#         Write the cif file.
#         """
#         with zopen(filename, "wt") as f:
#             f.write(self.__str__())


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
