#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from pathlib import Path
from typing import Dict, Union, List

from easyCore import np
from easyCore.Elements.Basic.Lattice import Lattice, PeriodicLattice
from easyCore.Elements.Basic.Site import Site, PeriodicSite, PeriodicAtoms, Atoms
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup
from easyCore.Objects.Base import BaseObj, Parameter, Descriptor
from easyCore.Objects.Groups import BaseCollection

from easyCore.Utils.io.cif import CifIO


class Phase(BaseObj):

    def __init__(self, name, spacegroup=None, cell=None, atoms=None, interface=None, enforce_sym=True):
        self.name = name
        if spacegroup is None:
            spacegroup = SpaceGroup.default()
        if cell is None:
            cell = Lattice.default()
        if isinstance(cell, Lattice):
            cell = PeriodicLattice.from_lattice_and_spacegroup(cell, spacegroup)
        if atoms is None:
            atoms = Atoms('atoms')
        ## TODO get PeriodicAtoms to work :-/
        # if isinstance(atoms, Atoms):
        #     atoms = PeriodicAtoms(atoms.name, *atoms, lattice=cell, interface=atoms.interface)

        super(Phase, self).__init__(name,
                                    cell=cell,
                                    _spacegroup=spacegroup,
                                    atoms=atoms)
        if not enforce_sym:
            self.cell.clear_sym()
        self._enforce_sym = enforce_sym
        self.interface = interface

        self._extent = np.array([1, 1, 1])
        self._centre = np.array([0, 0, 0])
        self.atom_tolerance = 1e-4

    def add_atom(self, *args, **kwargs):
        """
        Add an atom to the crystal
        """
        supplied_atom = False
        for arg in args:
            if issubclass(arg.__class__, Site):
                self.atoms.append(arg)
                supplied_atom = True
        if not supplied_atom:
            atom = Site.from_pars(*args, **kwargs)
            self.atoms.append(atom)

    def remove_atom(self, key):
        del self.atoms[key]


    def all_orbits(self, extent=None, magnetic_only: bool = False) -> Dict[str, np.ndarray]:
        """
        Generate all atomic positions from the atom array and symmetry operations over an extent.

        :return:  dictionary with keys of atom labels, containing numpy arrays of unique points in the extent
        (0, 0, 0) -> obj.extent
        :rtype: Dict[str, np.ndarray]
        """

        if extent is None:
            extent = self._extent

        offsets = np.array(np.meshgrid(range(0, extent[0] + 1),
                                       range(0, extent[1] + 1),
                                       range(0, extent[2] + 1))).T.reshape(-1, 3)

        orbits = self.get_orbits(magnetic_only=magnetic_only)
        for orbit_key in orbits.keys():
            orbit = orbits[orbit_key]
            site_positions = np.apply_along_axis(np.add, 1, offsets, orbit).reshape((-1, 3)) - self.center
            orbits[orbit_key] = \
                site_positions[np.all(site_positions >= -self.atom_tolerance, axis=1) &
                               np.all(site_positions <= extent + self.atom_tolerance, axis=1),
                :] + self.center
        return orbits

    def get_orbits(self, magnetic_only: bool = False) -> Dict[str, np.ndarray]:
        """
        Generate all atomic positions from the atom array and symmetry operations over an extent.

        :return:  dictionary with keys of atom labels, containing numpy arrays of unique points in the extent
        (0, 0, 0) -> obj.extent
        :rtype: Dict[str, np.ndarray]
        """
        atoms = PeriodicAtoms.from_atoms(self.cell, self.atoms)
        orbits = atoms.get_orbits(magnetic_only=magnetic_only)
        return orbits

    def to_cif_str(self) -> str:
        """
        Generate a cif string from the current crystal

        :return: cif string from the current crystal
        :rtype: str
        """
        return str(self.cif)

    @property
    def enforce_sym(self):
        return self._enforce_sym

    @enforce_sym.setter
    def enforce_sym(self, value: bool):
        if value:
            self.cell.enforce_sym()
        else:
            self.cell.clear_sym()

    @property
    def spacegroup(self):
        return self._spacegroup

    def set_spacegroup(self, value):
        if self._enforce_sym:
            self.cell.space_group_HM_name = value
        else:
            self._spacegroup.space_group_HM_name = value

    @property
    def extent(self) -> np.ndarray:
        """
        Get the current extent in unit cells

        :return: current extent in unit cells
        :rtype: np.ndarray
        """
        return self._extent

    @extent.setter
    def extent(self, new_extent: Union[list, np.ndarray]):
        """
        The current extent of in unit cells. Default (1, 1, 1)

        :param new_extent: The new extent in unit cells.
        :type new_extent: Union[list, tuple, np.ndarray]
        """
        if isinstance(new_extent, list):
            new_extent = np.array(new_extent)
        if np.prod(new_extent.shape) != 3:
            raise ValueError
        new_extent = new_extent.reshape((3,))
        self._extent = new_extent

    @property
    def center(self) -> np.ndarray:
        """
        Get the center position

        :return: center position
        :rtype: np.ndarray
        """
        return self._centre

    @center.setter
    def center(self, new_center: Union[list, tuple, np.ndarray]):
        """
        Set the center position. Default (0, 0, 0)

        :param new_center: New center position.
        :type new_center: Union[list, tuple, np.ndarray]
        """

        if isinstance(new_center, list):
            new_center = np.array(new_center)
        if np.prod(new_center.shape) != 3:
            raise ValueError
        new_center = new_center.reshape((3,))
        self._centre = new_center

    @property
    def cif(self) -> CifIO:
        """
        The current structure in a cif form.

        :return: Cif object representing the current crystal
        :rtype: CifIO
        """
        return CifIO.from_objects(self.name, self.cell, self.spacegroup, self.atoms)

    @classmethod
    def from_cif_str(cls, in_string: str):
        """
        Generate a crystal from a cif string.
        !Note! If more than one phase is present, only the first will be used.

        :param in_string: cif string
        :type in_string: str
        :return: Phase parsed from a cif string
        :rtype: Phase
        """
        cif = CifIO.from_cif_str(in_string)
        name, kwargs = cif.to_crystal_form()
        return cls(name, **kwargs)

    @classmethod
    def from_cif_file(cls, file_path: Union[str, Path]):
        """
        Generate a crystal from a cif file.
        !Note! If more than one phase is present, only the first will be used.

        :param file_path: cif file path
        :type file_path: str, Path
        :return: Phase parsed from a cif file
        :rtype: Phase
        """
        cif = CifIO.from_file(file_path)
        name, kwargs = cif.to_crystal_form()
        return cls(name, **kwargs)

    def _generate_positions(self, site, extent) -> np.ndarray:
        """
        Generate all orbits for a given fractional position.
        """
        sym_op = self.spacegroup._sg_data.get_orbit
        offsets = np.array(np.meshgrid(range(0, extent[0] + 1),
                                       range(0, extent[1] + 1),
                                       range(0, extent[2] + 1))).T.reshape(-1, 3)
        return np.apply_along_axis(np.add, 1, offsets, np.array(sym_op(site.fract_coords))).reshape((-1, 3))

    def all_sites(self, extent=None) -> Dict[str, np.ndarray]:
        """
        Generate all atomic positions from the atom array and symmetry operations over an extent.
        :return:  dictionary with keys of atom labels, containing numpy arrays of unique points in the extent
        (0, 0, 0) -> obj.extent
        :rtype: Dict[str, np.ndarray]
        """
        if self.spacegroup is None:
            return {atom.label: atom.fract_coords for atom in self.atoms}

        if extent is None:
            extent = self._extent

        sites = {}
        for site in self.atoms:
            unique_sites = self._generate_positions(site, extent)
            site_positions = unique_sites - self.center
            sites[site.label.raw_value] = \
                site_positions[np.all(site_positions >= -self.atom_tolerance, axis=1) &
                               np.all(site_positions <= extent + self.atom_tolerance, axis=1),
                :] + self.center
        return sites

    def as_dict(self, skip: list = None) -> dict:
        d = super(Phase, self).as_dict(skip=skip)
        del d['_spacegroup']
        return d


class Phases(BaseCollection):

    def __init__(self, name: str = 'phases', *args, interface=None, **kwargs):
        """
        Generate a collection of crystals.

        :param name: Name of the crystals collection
        :type name: str
        :param args: objects to create the crystal
        :type args: *Phase
        """
        if not isinstance(name, str):
            raise AttributeError('Name should be a string!')

        super(Phases, self).__init__(name, *args, **kwargs)
        self.interface = interface
        self._cif = None
        self._create_cif()

    def __repr__(self) -> str:
        return f'Collection of {len(self)} phases.'

    def __getitem__(self, idx: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, BaseCollection]:
        if isinstance(idx, str) and idx in self.phase_names:
            idx = self.phase_names.index(idx)
        return super(Phases, self).__getitem__(idx)

    def __delitem__(self, key):
        if isinstance(key, str) and key in self.phase_names:
            key = self.phase_names.index(key)
        return super(Phases, self).__delitem__(key)

    def append(self, item: Phase):
        if not isinstance(item, Phase):
            raise TypeError('Item must be a Phase')
        if item.name in self.phase_names:
            raise AttributeError(f'An atom of name {item.name} already exists.')
        super(Phases, self).append(item)
        self._create_cif()

    @property
    def phase_names(self) -> List[str]:
        return [phase.name for phase in self]

    def _create_cif(self):
        if len(self) == 0:
            self._cif = CifIO(None)
            return
        self._cif = CifIO.from_objects(self[0].name, self[0].cell, self[0].spacegroup, self[0].atoms)
        for item in self[1:]:
            self._cif.add_cif_from_objects(item.name, item.cell, item.spacegroup, item.atoms)

    @property
    def cif(self):
        self._create_cif()
        return self._cif

    @classmethod
    def from_cif_str(cls, in_string: str):
        _, crystals = cls._from_external(CifIO.from_cif_str, in_string)
        return cls('Phases', *crystals)

    @classmethod
    def from_cif_file(cls, file_path: Path):
        _, crystals = cls._from_external(CifIO.from_file, file_path)
        return cls('Phases', *crystals)

    @staticmethod
    def _from_external(constructor, *args):
        cif = constructor(*args)
        name = 'FromCif'
        crystals = []
        for cif_index in range(cif._parser.number_of_cifs):
            name, kwargs = cif.to_crystal_form(cif_index=cif_index)
            crystals.append(Phase(name, **kwargs))
        return name, crystals
