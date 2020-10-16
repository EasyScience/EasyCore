__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from pathlib import Path
from typing import Dict, Union, List

from easyCore import np
from easyCore.Elements.Basic.Cell import Cell
from easyCore.Elements.Basic.Site import Site, Atoms
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup
from easyCore.Objects.Base import BaseObj, Parameter, Descriptor
from easyCore.Objects.Groups import BaseCollection

from easyCore.Utils.io.cif import CifIO


class Crystal(BaseObj):

    def __init__(self, name, spacegroup=None, cell=None, atoms=None, interface=None):
        self.name = name
        if spacegroup is None:
            spacegroup = SpaceGroup.default()
        if cell is None:
            cell = Cell.default()
        if atoms is None:
            atoms = Atoms('atom_list')

        super(Crystal, self).__init__(name,
                                      cell=cell,
                                      spacegroup=spacegroup,
                                      atoms=atoms)
        self.interface = interface

        self._extent = np.array([1, 1, 1])
        self._centre = np.array([0, 0, 0])

    def add_atom(self, *args, **kwargs):
        """
        Add an atom to the crystal
        """
        supplied_atom = False
        for arg in args:
            if isinstance(arg, Site):
                self.atoms.append(arg)
                supplied_atom = True
        if not supplied_atom:
            self.atoms.append(Site.from_pars(*args, **kwargs))

    def all_sites(self) -> Dict[str, np.ndarray]:
        """
        Generate all atomic positions from the atom array and symmetry operations over an extent.

        :return:  dictionary with keys of atom labels, containing numpy arrays of unique points in the extent
        (0, 0, 0) -> obj.extent
        :rtype: Dict[str, np.ndarray]
        """
        if self.spacegroup is None:
            return {atom.label: atom.fract_coords for atom in self.atoms}

        sym_op = self.spacegroup.symmetry_opts
        sites = {}
        offsets = np.array(np.meshgrid(range(-1, self.extent[0] + 1),
                                       range(-1, self.extent[1] + 1),
                                       range(-1, self.extent[2] + 1))).T.reshape(-1, 3)
        for site in self.atoms:
            all_sites = np.array([op.operate(site.fract_coords) for op in sym_op])
            for offset in offsets[1:, :]:
                all_sites = np.concatenate((all_sites,
                                            np.array([op.operate(site.fract_coords + offset) for op in sym_op])),
                                           axis=0)
            site_positions = np.unique(all_sites, axis=0) - self.center
            sites[site.label.raw_value] = \
                site_positions[np.all(site_positions >= 0, axis=1) & np.all(site_positions <= self.extent, axis=1),
                :] + self.center
        return sites

    def to_cif_str(self) -> str:
        """
        Generate a cif string from the current crystal

        :return: cif string from the current crystal
        :rtype: str
        """
        return str(self.cif)

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
        :return: Crystal parsed from a cif string
        :rtype: Crystal
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
        :return: Crystal parsed from a cif file
        :rtype: Crystal
        """
        cif = CifIO.from_file(file_path)
        name, kwargs = cif.to_crystal_form()
        return cls(name, **kwargs)


class Crystals(BaseCollection):

    def __init__(self, name: str = 'phases', *args, interface=None, **kwargs):
        """
        Generate a collection of crystals.

        :param name: Name of the crystals collection
        :type name: str
        :param args: objects to create the crystal
        :type args: *Crystal
        """
        if not isinstance(name, str):
            raise AttributeError('Name should be a string!')

        super(Crystals, self).__init__(name, *args, **kwargs)
        self.interface = interface
        self._cif = None
        self._create_cif()

    def __repr__(self) -> str:
        return f'Collection of {len(self)} phases.'

    def __getitem__(self, idx: Union[int, slice]) -> Union[Parameter, Descriptor, BaseObj, BaseCollection]:
        if isinstance(idx, str) and idx in self.phase_names:
            idx = self.phase_names.index(idx)
        return super(Crystals, self).__getitem__(idx)

    def append(self, item: Crystal):
        if not isinstance(item, Crystal):
            raise TypeError('Item must be a Crystal')
        if item.name in self.phase_names:
            raise AttributeError(f'An atom of name {item.name} already exists.')
        super(Crystals, self).append(item)
        self._create_cif()

    @property
    def phase_names(self) -> List[str]:
        return [phase.name for phase in self]

    def _create_cif(self):
        if len(self) == 0:
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
        cif = CifIO.from_cif_str(in_string)
        name = 'FromCif'
        crystals = []
        for cif_index in range(cif._parser.number_of_cifs):
            name, kwargs = cif.to_crystal_form(cif_index=cif_index)
            crystals.append(Crystal(name, **kwargs))
        return cls(name, *crystals)

    @classmethod
    def from_cif_file(cls, file_path: Path):
        cif = CifIO.from_file(file_path)
        name = 'FromCif'
        crystals = []
        for cif_index in range(cif._parser.number_of_cifs):
            name, kwargs = cif.to_crystal_form(cif_index=cif_index)
            crystals.append(Crystal(name, **kwargs))
        return cls(name, *crystals)
