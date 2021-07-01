#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

import collections
import itertools
import math
import warnings
from copy import deepcopy
from fractions import Fraction
from functools import reduce

from easyCore import np
from typing import Tuple, Union, List, Sequence, Dict

from easyCore import ureg
from easyCore.Fitting.Constraints import ObjConstraint
from easyCore.Utils.classTools import addProp
from easyCore.Utils.decorators import memoized
from easyCore.Utils.typing import Vector3Like
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.Elements.Basic.SpaceGroup import SpaceGroup
from easyCore.Utils.io.star import StarSection

CELL_DETAILS = {
    'length': {
        'description': 'Unit-cell length of the selected structure in angstroms.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_length_.html',
        'value':       3,
        'units':       'angstrom',
        'min':         0,
        'max':         np.Inf,
        'fixed':       True
    },
    'angle':  {
        'description': 'Unit-cell angle of the selected structure in degrees.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_angle_.html',
        'value':       90,
        'units':       'deg',
        'min':         0,
        'max':         np.Inf,
        'fixed':       True
    }
}


class Lattice(BaseObj):

    def __init__(self, length_a: Parameter, length_b: Parameter, length_c: Parameter,
                 angle_alpha: Parameter, angle_beta: Parameter, angle_gamma: Parameter, interface=None):
        super().__init__('lattice',
                         length_a=length_a, length_b=length_b, length_c=length_c,
                         angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma)
        self.interface = interface

    # Class constructors
    @classmethod
    def default(cls, interface=None) -> "Lattice":
        """
        Default constructor for a crystallographic unit cell.

        :return: Default crystallographic unit cell container
        :rtype: Lattice
        """
        length_a = Parameter('length_a', **CELL_DETAILS['length'])
        length_b = Parameter('length_b', **CELL_DETAILS['length'])
        length_c = Parameter('length_c', **CELL_DETAILS['length'])
        angle_alpha = Parameter('angle_alpha', **CELL_DETAILS['angle'])
        angle_beta = Parameter('angle_beta', **CELL_DETAILS['angle'])
        angle_gamma = Parameter('angle_gamma', **CELL_DETAILS['angle'])
        return cls(length_a, length_b, length_c, angle_alpha, angle_beta, angle_gamma, interface=interface)

    @classmethod
    def from_pars(cls, length_a: float, length_b: float, length_c: float,
                  angle_alpha: float, angle_beta: float, angle_gamma: float, ang_unit: str = 'deg',
                  interface=None) -> "Lattice":
        """
        Constructor of a crystallographic unit cell when parameters are known.

        :param length_a: Unit cell length a
        :type length_a: float
        :param length_b: Unit cell length b
        :type length_b: float
        :param length_c:  Unit cell length c
        :type length_c: float
        :param angle_alpha: Unit cell angle alpha
        :type angle_alpha: float
        :param angle_beta:  Unit cell angle beta
        :type angle_beta: float
        :param angle_gamma:  Unit cell angle gamma
        :type angle_gamma: float
        :param ang_unit: unit for supplied angles. Default is degree ('deg'). Radian is also valid ('rad'/'radian')
        :type ang_unit: str
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        if ang_unit.startswith('rad'):
            angle_alpha = np.rad2deg(angle_alpha)
            angle_beta = np.rad2deg(angle_beta)
            angle_gamma = np.rad2deg(angle_gamma)

        default_options = deepcopy(CELL_DETAILS)
        del default_options['length']['value']
        del default_options['angle']['value']

        length_a = Parameter('length_a', length_a, **default_options['length'])
        length_b = Parameter('length_b', length_b, **default_options['length'])
        length_c = Parameter('length_c', length_c, **default_options['length'])
        angle_alpha = Parameter('angle_alpha', angle_alpha, **default_options['angle'])
        angle_beta = Parameter('angle_beta', angle_beta, **default_options['angle'])
        angle_gamma = Parameter('angle_gamma', angle_gamma, **default_options['angle'])

        return cls(length_a=length_a, length_b=length_b, length_c=length_c,
                   angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma, interface=interface)

    @classmethod
    def from_matrix(cls, matrix: Union[List[float], List[List[float]], np.ndarray], interface=None) -> "Lattice":
        """
        Construct a crystallographic unit cell from the lattice matrix

        :param matrix: Matrix describing the crystallographic unit cell in the form of a numpy array,
        1x9 list or 3x3 list.
        :type matrix: np.ndarray, List[float], List[List[float]]
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """

        matrix = np.array(matrix, dtype=np.float64).reshape((3, 3))
        lengths = np.sqrt(np.sum(matrix ** 2, axis=1))
        angles = np.zeros(3)
        for i in range(3):
            j = (i + 1) % 3
            k = (i + 2) % 3
            angles[i] = np.dot(matrix[j], matrix[k]) / (lengths[j] * lengths[k])
            angles[i] = max(min(angles[i], 1), - 1)
        angles = np.arccos(angles) * 180.0 / np.pi
        return cls.from_pars(*lengths, *angles, interface=interface)

    @classmethod
    def cubic(cls, a: float, interface=None) -> "Lattice":
        """
        Convenience constructor for a cubic lattice.

        :param a: The *a* lattice parameter of the cubic cell.
        :type a: float
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        return cls.from_pars(a, a, a, 90, 90, 90, interface=interface)

    @classmethod
    def tetragonal(cls, a: float, c: float, interface=None) -> "Lattice":
        """
        Convenience constructor for a tetragonal lattice.

        :param a: *a* lattice parameter of the tetragonal cell.
        :type a: float
        :param c: *c* lattice parameter of the tetragonal cell.
        :type c: float
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        return cls.from_pars(a, a, c, 90, 90, 90, interface=interface)

    @classmethod
    def orthorhombic(cls, a: float, b: float, c: float, interface=None) -> "Lattice":
        """
        Convenience constructor for an orthorhombic lattice.

        :param a: *a* lattice parameter of the orthorhombic cell.
        :type a: float
        :param b: *b* lattice parameter of the orthorhombic cell.
        :type b: float
        :param c: *c* lattice parameter of the orthorhombic cell.
        :type c: float
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        return cls.from_pars(a, b, c, 90, 90, 90, interface=interface)

    @classmethod
    def monoclinic(cls, a: float, b: float, c: float, beta: float, interface=None) -> "Lattice":
        """
        Convenience constructor for a monoclinic lattice of dimensions a x b x c with non right-angle
        beta between lattice vectors a and c.

        :param a: *a* lattice parameter of the monoclinc cell.
        :type a: float
        :param b: *b* lattice parameter of the monoclinc cell.
        :type b: float
        :param c: *c* lattice parameter of the monoclinc cell.
        :type c: float
        :param beta: *beta* angle between lattice vectors b and c in degrees.
        :type beta: float
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        return cls.from_pars(a, b, c, 90, beta, 90, interface=interface)

    @classmethod
    def hexagonal(cls, a: float, c: float, interface=None) -> "Lattice":
        """
        Convenience constructor for a hexagonal lattice of dimensions a x a x c

        :param a: *a* lattice parameter of the hexagonal cell.
        :type a: float
        :param c: *c* lattice parameter of the hexagonal cell.
        :type c: float
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        return cls.from_pars(a, a, c, 90, 90, 120, interface=interface)

    @classmethod
    def rhombohedral(cls, a: float, alpha: float, interface=None) -> "Lattice":
        """
        Convenience constructor for a rhombohedral lattice of dimensions a x a x a.

        :param a: *a* lattice parameter of the monoclinc cell.
        :type a: float
        :param alpha: Angle for the rhombohedral lattice in degrees.
        :type alpha: float
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        return cls.from_pars(a, a, a, alpha, alpha, alpha, interface=interface)

    # Dynamic properties
    @property
    def a(self) -> float:
        """
        Get the *a* lattice parameter.

        :return: *a* lattice parameter
        :rtype: float
        """
        return self.length_a.raw_value

    @a.setter
    def a(self, new_a_value: float):
        """
        Set the *a* lattice parameter.

        :param new_a_value: new *a* lattice parameter
        :type new_a_value: float
        :return: noneType
        :rtype: None
        """
        self.length_a.value = new_a_value

    @property
    def b(self) -> float:
        """
        Get the *b* lattice parameter.

        :return: *b* lattice parameter
        :rtype: float
        """
        return self.length_b.raw_value

    @b.setter
    def b(self, new_b_value: float):
        """
        Set the *b* lattice parameter.

        :param new_b_value: new *a* lattice parameter
        :type new_b_value: float
        :return: noneType
        :rtype: None
        """
        self.length_b.value = new_b_value

    @property
    def c(self) -> float:
        """
        Get the *c* lattice parameter.

        :return: *c* lattice parameter
        :rtype: float
        """
        return self.length_c.raw_value

    @c.setter
    def c(self, new_c_value: float):
        """
        Set the *c* lattice parameter.

        :param new_c_value: new *a* lattice parameter
        :type new_c_value: float
        :return: noneType
        :rtype: None
        """
        self.length_c.value = new_c_value

    @property
    def alpha(self) -> float:
        """
        Get the *alpha* lattice parameter.

        :return: *alpha* lattice parameter
        :rtype: float
        """
        return self.angle_alpha.raw_value

    @alpha.setter
    def alpha(self, new_alpha_value: float):
        """
        Set the *alpha* lattice parameter.

        :param new_alpha_value: new *alpha* lattice parameter
        :type new_alpha_value: float
        :return: noneType
        :rtype: None
        """
        self.angle_alpha.value = new_alpha_value

    @property
    def beta(self) -> float:
        """
        Get the *beta* lattice parameter.

        :return: *beta* lattice parameter
        :rtype: float
        """
        return self.angle_beta.raw_value

    @beta.setter
    def beta(self, new_beta_value: float):
        """
        Set the *beta* lattice parameter.

        :param new_beta_value: new *a* lattice parameter
        :type new_beta_value: float
        :return: noneType
        :rtype: None
        """
        self.angle_beta.value = new_beta_value

    @property
    def gamma(self) -> float:
        """
        Get the *gamma* lattice parameter.

        :return: *gamma* lattice parameter
        :rtype: float
        """
        return self.angle_gamma.raw_value

    @gamma.setter
    def gamma(self, new_gamma_value: float):
        """
        Set the *gamma* lattice parameter.

        :param new_gamma_value: new *gamma* lattice parameter
        :type new_gamma_value: float
        :return: noneType
        :rtype: None
        """
        self.angle_gamma.value = new_gamma_value

    @property
    def lengths(self) -> Tuple[float, float, float]:
        """
        Get the lengths of the unit cell.

        :return: Tuple of unit cell lengths (a, b, c)
        :rtype: tuple
        """
        return self.a, self.b, self.c

    @property
    def angles(self) -> Tuple[float, float, float]:
        """
        Get the angles of the unit cell in degrees.

        :return: Tuple of unit cell angles (alpha, beta, gamma)
        :rtype: tuple
        """
        return self.alpha, self.beta, self.gamma

    @property
    def matrix(self) -> np.ndarray:
        """
        Get the lattice matrix.

        :return: Lattice matrix in the form of a 9x9 matrix
        :rtype: np.ndarray
        """
        return self.__matrix(*self.lengths, *self.angles)

    @property
    def volume(self) -> float:
        """
        Volume of the unit cell.

        :return: Volume of the unit cell
        :rtype: ureg.Quantity
        """
        m = self.matrix
        vol = float(abs(np.dot(np.cross(m[0], m[1]), m[2])))
        return ureg.Quantity(vol, units=self.length_a.unit * self.length_b.unit * self.length_c.unit)

    @property
    def inv_matrix(self) -> np.ndarray:
        """
        Inverse of lattice matrix.

        :return: Inverse of lattice matrix
        :rtype: np.ndarray
        """
        return np.linalg.inv(self.matrix)

    @property
    def metric_tensor(self) -> np.ndarray:
        """
        The metric tensor of the lattice.

        :return metric tensor of the lattice
        :rtype: np.ndarray
        """
        matrix = self.matrix
        return np.dot(matrix, self.matrix.T)

    # Functions that create new copies
    @property
    def reciprocal_lattice(self) -> "Lattice":
        """
        Return the reciprocal lattice. Note that this is the standard
        reciprocal lattice used for solid state physics with a factor of 2 *
        pi. If you are looking for the crystallographic reciprocal lattice,
        use the reciprocal_lattice_crystallographic property.

        :return: New cell in the reciprocal lattice
        :rtype: Lattice
        """
        v = np.linalg.inv(self.matrix).T
        return self.__class__.from_matrix(v * 2 * np.pi, interface=self.interface)

    @property
    def reciprocal_lattice_crystallographic(self) -> "Lattice":
        """
        Returns the *crystallographic* reciprocal lattice, i.e., no factor of
        2 * pi.

        :return: New cell in the *crystallographic* reciprocal lattice
        :rtype: Lattice
        """
        return self.__class__.from_matrix(self.reciprocal_lattice.matrix / (2 * np.pi), interface=self.interface)

    def scale(self, new_volume: float) -> "Lattice":
        """
        Return a new Cell with volume new_volume by performing a
        scaling of the lattice vectors so that length proportions and angles
        are preserved.

        :param new_volume: New volume to scale to.
        :type new_volume: float
        :return: New cell scaled to volume
        :rtype: Lattice
        """

        lengths = self.lengths
        versors = self.matrix / lengths
        geo_factor = np.abs(np.dot(np.cross(versors[0], versors[1]), versors[2]))
        ratios = np.array(lengths) / lengths[2]
        new_c = (new_volume / (geo_factor * np.prod(ratios))) ** (1 / 3.0)
        return self.__class__.from_matrix(versors * (new_c * ratios), interface=self.interface)

    def scale_lengths(self, length_scales: Union[float, Vector3Like]) -> "Lattice":
        """
        Return a new Cell where the cell lengths have been scaled by the scaling
        factors. Angles are preserved.

        :param length_scales: Scaling for each length or universal scaling factor
        :type length_scales: Union[float, Vector3Like]
        :return: New Cell scaled by user supplied scale factors
        :rtype: Lattice
        """
        if isinstance(length_scales, float):
            length_scales = 3 * [length_scales]
        new_lengths = np.array(length_scales) * np.array(self.lengths)
        return self.__class__.from_pars(*new_lengths, *self.angles, interface=self.interface)

    # Get functions
    def get_cartesian_coords(self, fractional_coords: Vector3Like) -> np.ndarray:
        """
        Returns the cartesian coordinates given fractional coordinates.

        :param fractional_coords: fractional_coords (3x1 array): Fractional coords.
        :type fractional_coords: np.ndarray , list
        :return: Cartesian coordinates
        :rtype: np.ndarray
        """
        return np.dot(fractional_coords, self.matrix)

    def get_fractional_coords(self, cart_coords: Vector3Like) -> np.ndarray:
        """
        Returns the fractional coordinates given cartesian coordinates.

        :param cart_coords: cart_coords (3x1 array): Fractional coords.
        :type cart_coords: np.ndarray , list
        :return: Fractional coordinates.
        :rtype: np.ndarray
        """
        return np.dot(cart_coords, self.inv_matrix)

    def get_vector_along_lattice_directions(self, cart_coords: Vector3Like) -> np.ndarray:
        """
        Returns the coordinates along lattice directions given cartesian coordinates.
        Note, this is different than a projection of the cartesian vector along the
        lattice parameters. It is simply the fractional coordinates multiplied by the
        lattice vector magnitudes.

        :param cart_coords: cart_coords (3x1 array): Fractional coords.
        :type cart_coords: np.ndarray , list
        :return: Lattice coordinates.
        :rtype: np.ndarray
        """
        return self.lengths * self.get_fractional_coords(cart_coords)

    def d_hkl(self, miller_index: Vector3Like) -> float:
        """
        Returns the distance between the hkl plane and the origin

        :param miller_index: (h. k. l) Miller index of plane
        :type miller_index: Vector3Like
        :return: Distance between the hkl plane and the origin
        :rtype: float
        """

        gstar = self.reciprocal_lattice_crystallographic.metric_tensor
        hkl = np.array(miller_index)
        return 1 / ((np.dot(np.dot(hkl, gstar), hkl.T)) ** (1 / 2))

    # Checking
    def is_orthogonal(self) -> bool:
        """
        Returns true if the cell is orthogonal (all angles 90 degrees)

        :return: Whether all angles are 90 degrees.
        :rtype: bool
        """
        return all([abs(a - 90) < 1e-5 for a in self.angles])

    def is_hexagonal(self, hex_angle_tol: float = 5, hex_length_tol: float = 0.01) -> bool:
        """
        Returns true if the Lattice is hexagonal.

        :param hex_angle_tol: Angle tolerance
        :param hex_length_tol: Length tolerance
        :return: Whether lattice corresponds to hexagonal lattice.
        :rtype: bool
        """
        lengths = self.lengths
        angles = self.angles
        right_angles = [i for i in range(3) if abs(angles[i] - 90) < hex_angle_tol]
        hex_angles = [i for i in range(3)
                      if abs(angles[i] - 60) < hex_angle_tol or abs(angles[i] - 120) < hex_angle_tol]

        return (
                len(right_angles) == 2 and
                len(hex_angles) == 1 and
                abs(lengths[right_angles[0]] - lengths[right_angles[1]]) < hex_length_tol
        )

    @staticmethod
    @memoized
    def __matrix(a: float, b: float, c: float, alpha: float, beta: float, gamma: float) -> np.ndarray:
        """
        Calculating the crystallographic matrix is time consuming and we use it often, so we have memoized it.
        :param a: *a* lattice parameter
        :type a: float
        :param b: *b* lattice parameter
        :type b: float
        :param c: *c* lattice parameter
        :type c: float
        :param alpha: *alpha* lattice parameter
        :type alpha: float
        :param beta: *beta* lattice parameter
        :type beta: float
        :param gamma: *gamma* lattice parameter
        :type gamma: float
        :return: crystallographic matrix
        :rtype: np.ndarray
        """
        angles_r = np.radians([alpha, beta, gamma])
        cos_alpha, cos_beta, cos_gamma = np.cos(angles_r)
        sin_alpha, sin_beta, sin_gamma = np.sin(angles_r)

        val = (cos_alpha * cos_beta - cos_gamma) / (sin_alpha * sin_beta)
        # Sometimes rounding errors result in values slightly > 1.
        val = max(min(val, 1), - 1)
        gamma_star = np.arccos(val)

        vector_a = [a * sin_beta, 0.0, a * cos_beta]
        vector_b = [
            -b * sin_alpha * np.cos(gamma_star),
            b * sin_alpha * np.sin(gamma_star),
            b * cos_alpha,
        ]
        vector_c = [0.0, 0.0, float(c)]
        return np.array([vector_a, vector_b, vector_c], dtype=np.float64)

    def __repr__(self) -> str:
        return '<Lattice: (a: {:.2f} {:~P}, b: {:.2f} {:~P}, c: {:.2f}{:~P}, alpha: {:.2f} {:~P}, beta: {:.2f} {:~P}, ' \
               '' \
               'gamma: {:.2f} {:~P}>'.format(self.length_a.raw_value, self.length_a.unit,
                                             self.length_b.raw_value, self.length_b.unit,
                                             self.length_c.raw_value, self.length_c.unit,
                                             self.angle_alpha.raw_value, self.angle_alpha.unit,
                                             self.angle_beta.raw_value, self.angle_beta.unit,
                                             self.angle_gamma.raw_value, self.angle_gamma.unit)

    def __format__(self, fmt_spec=""):
        """
        Support format printing. Supported formats are:

        1. "l" for a list format that can be easily copied and pasted, e.g.,
           ".3fl" prints something like
           "[[10.000, 0.000, 0.000], [0.000, 10.000, 0.000], [0.000, 0.000, 10.000]]"
        2. "p" for lattice parameters ".1fp" prints something like
           "{10.0, 10.0, 10.0, 90.0, 90.0, 90.0}"
        3. Default will simply print a 3x3 matrix form. E.g.,
           10.000 0.000 0.000
           0.000 10.000 0.000
           0.000 0.000 10.000
        """
        m = (self.lengths, self.angles)

        if fmt_spec.endswith("m"):
            fmt = "[[{}, {}, {}], [{}, {}, {}], [{}, {}, {}]]"
            m = self.matrix.tolist()
            fmt_spec = fmt_spec[:-1]
        elif fmt_spec.endswith("l"):
            fmt = "{{{}, {}, {}, {}, {}, {}}}"
            fmt_spec = fmt_spec[:-1]
        else:
            fmt = "({} {} {}), ({} {} {})"
            fmt_spec = fmt_spec[:-1]
        return fmt.format(*[format(c, fmt_spec) for row in m for c in row])

    def __copy__(self):
        """
        Returns a deep copy of the Lattice


        :return: Deep copy of self
        :rtype:
        """
        return self.__class__.from_pars(*self.lengths, *self.angles, interface=self.interface)

    def to_star(self):
        return StarSection(self)

    @classmethod
    def from_star(cls, in_string):
        return StarSection.from_string(in_string).to_class(cls)

    def get_points_in_sphere(
            self,
            frac_points: List[Vector3Like],
            center: Vector3Like,
            r: float,
            zip_results=True,
    ) -> Union[
        List[Tuple[np.ndarray, float, int, np.ndarray]],
        List[np.ndarray],
    ]:
        """
        Find all points within a sphere from the point taking into account
        periodic boundary conditions. This includes sites in other periodic
        images.
        Algorithm:
        1. place sphere of radius r in crystal and determine minimum supercell
           (parallelpiped) which would contain a sphere of radius r. for this
           we need the projection of a_1 on a unit vector perpendicular
           to a_2 & a_3 (i.e. the unit vector in the direction b_1) to
           determine how many a_1"s it will take to contain the sphere.
           Nxmax = r * length_of_b_1 / (2 Pi)
        2. keep points falling within r.
        Args:
            frac_points: All points in the lattice in fractional coordinates.
            center: Cartesian coordinates of center of sphere.
            r: radius of sphere.
            zip_results (bool): Whether to zip the results together to group by
                 point, or return the raw fcoord, dist, index arrays
        Returns:
            if zip_results:
                [(fcoord, dist, index, supercell_image) ...] since most of the time, subsequent
                processing requires the distance, index number of the atom, or index of the image
            else:
                fcoords, dists, inds, image
        """
        cart_coords = self.get_cartesian_coords(frac_points)
        neighbors = get_points_in_spheres(all_coords=cart_coords, center_coords=np.array([center]), r=r, pbc=True,
                                          numerical_tol=1e-8, lattice=self, return_fcoords=True)[0]
        if len(neighbors) < 1:
            return [] if zip_results else [()] * 4
        if zip_results:
            return neighbors
        return [np.array(i) for i in list(zip(*neighbors))]


class PeriodicLattice(Lattice):
    def __init__(self, length_a: Parameter, length_b: Parameter, length_c: Parameter,
                 angle_alpha: Parameter, angle_beta: Parameter, angle_gamma: Parameter, spacegroup: SpaceGroup,
                 interface=None):
        super().__init__(length_a=length_a, length_b=length_b, length_c=length_c,
                         angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma)
        self._add_component('spacegroup', spacegroup)

        # Do some class voodoo. We can do this as we have hidden space_group_HM_name
        # as _space_group_HM_name and used a simple property.
        self.__previous_SG_setter = spacegroup.__class__.space_group_HM_name.fset
        spacegroup.__class__.space_group_HM_name = property(
            fget=spacegroup.__class__.space_group_HM_name.fget,
            fset=lambda obj, val: self.__new_SG_setter(obj, val),
            fdel=spacegroup.__class__.space_group_HM_name.fdel)

        self.interface = interface
        self.enforce_sym()

    @classmethod
    def from_lattice_and_spacegroup(cls, lattice: Lattice, spacegroup: SpaceGroup):
        length_a = lattice.length_a
        length_b = lattice.length_b
        length_c = lattice.length_c
        angle_alpha = lattice.angle_alpha
        angle_beta = lattice.angle_beta
        angle_gamma = lattice.angle_gamma

        return cls(length_a, length_b, length_c,
                   angle_alpha, angle_beta, angle_gamma,
                   spacegroup, interface=lattice.interface)

    # Class constructors
    @classmethod
    def default(cls, interface=None) -> "Lattice":
        """
        Default constructor for a crystallographic unit cell.

        :return: Default crystallographic unit cell container
        :rtype: Lattice
        """
        length_a = Parameter('length_a', **CELL_DETAILS['length'])
        length_b = Parameter('length_b', **CELL_DETAILS['length'])
        length_c = Parameter('length_c', **CELL_DETAILS['length'])
        angle_alpha = Parameter('angle_alpha', **CELL_DETAILS['angle'])
        angle_beta = Parameter('angle_beta', **CELL_DETAILS['angle'])
        angle_gamma = Parameter('angle_gamma', **CELL_DETAILS['angle'])
        spacegroup = SpaceGroup.default()
        return cls(length_a, length_b, length_c, angle_alpha, angle_beta, angle_gamma, spacegroup, interface=interface)

    @classmethod
    def from_pars(cls, length_a: float, length_b: float, length_c: float,
                  angle_alpha: float, angle_beta: float, angle_gamma: float,
                  spacegroup: str, ang_unit: str = 'deg',
                  interface=None) -> "Lattice":
        """
        Constructor of a crystallographic unit cell when parameters are known.

        :param length_a: Unit cell length a
        :type length_a: float
        :param length_b: Unit cell length b
        :type length_b: float
        :param length_c:  Unit cell length c
        :type length_c: float
        :param angle_alpha: Unit cell angle alpha
        :type angle_alpha: float
        :param angle_beta:  Unit cell angle beta
        :type angle_beta: float
        :param angle_gamma:  Unit cell angle gamma
        :type angle_gamma: float
        :param ang_unit: unit for supplied angles. Default is degree ('deg'). Radian is also valid ('rad'/'radian')
        :type ang_unit: str
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        if ang_unit.startswith('rad'):
            angle_alpha = np.rad2deg(angle_alpha)
            angle_beta = np.rad2deg(angle_beta)
            angle_gamma = np.rad2deg(angle_gamma)

        default_options = deepcopy(CELL_DETAILS)
        del default_options['length']['value']
        del default_options['angle']['value']

        length_a = Parameter('length_a', length_a, **default_options['length'])
        length_b = Parameter('length_b', length_b, **default_options['length'])
        length_c = Parameter('length_c', length_c, **default_options['length'])
        angle_alpha = Parameter('angle_alpha', angle_alpha, **default_options['angle'])
        angle_beta = Parameter('angle_beta', angle_beta, **default_options['angle'])
        angle_gamma = Parameter('angle_gamma', angle_gamma, **default_options['angle'])
        spacegroup = SpaceGroup.from_pars(spacegroup)

        return cls(length_a=length_a, length_b=length_b, length_c=length_c,
                   angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma,
                   spacegroup=spacegroup, interface=interface)

    @classmethod
    def from_matrix(cls, matrix: Union[List[float], List[List[float]], np.ndarray], interface=None) -> "Lattice":
        """
        Construct a crystallographic unit cell from the lattice matrix

        :param matrix: Matrix describing the crystallographic unit cell in the form of a numpy array,
        1x9 list or 3x3 list.
        :type matrix: np.ndarray, List[float], List[List[float]]
        :return: Crystallographic unit cell container
        :rtype: Lattice
        """
        raise NotImplementedError('A periodic Lattice can not be created from just a matrix')

    def clear_sym(self):
        pars = [self.length_a, self.length_b, self.length_c,
                self.angle_alpha, self.angle_beta, self.angle_gamma]
        for par in pars:
            new_con = {con: par.user_constraints[con] for con in par.user_constraints.keys() if
                       not con.startswith('sg_')}
            par.user_constraints = new_con
            if not par.enabled:
                par.enabled = True

    def enforce_sym(self):
        """
        Enforce symmetry constraints on to a Lattice
        """
        # SG system
        crys_system = self.spacegroup.crystal_system
        self.clear_sym()
        trig_test = crys_system == "trigonal" and (
                self.spacegroup.setting.endswith("H") or
                self.spacegroup.int_number in [143, 144, 145, 147, 149, 150, 151, 152,
                                               153, 154, 156, 157, 158, 159, 162, 163,
                                               164, 165])

        # Go through the cell systems
        if crys_system == "cubic":
            self.length_a.user_constraints['sg_1'] = ObjConstraint(self.length_b, '', self.length_a)
            self.length_a.user_constraints['sg_1']()
            self.length_a.user_constraints['sg_2'] = ObjConstraint(self.length_c, '', self.length_a)
            self.length_a.user_constraints['sg_2']()
            self.angle_alpha = 90
            self.angle_alpha.enabled = False
            self.angle_beta = 90
            self.angle_beta.enabled = False
            self.angle_gamma = 90
            self.angle_gamma.enabled = False
        elif crys_system == "hexagonal" or trig_test:
            self.length_a.user_constraints['sg_1'] = ObjConstraint(self.length_b, '', self.length_a)
            self.length_a.user_constraints['sg_1']()
            self.angle_alpha = 90
            self.angle_alpha.enabled = False
            self.angle_beta = 90
            self.angle_beta.enabled = False
            self.angle_gamma = 120
            self.angle_gamma.enabled = False
        elif crys_system == "trigonal" and not trig_test:
            self.length_a.user_constraints['sg_1'] = ObjConstraint(self.length_b, '', self.length_a)
            self.length_a.user_constraints['sg_1']()
            self.length_a.user_constraints['sg_2'] = ObjConstraint(self.length_c, '', self.length_a)
            self.length_a.user_constraints['sg_2']()
            self.angle_alpha.user_constraints['sg_1'] = ObjConstraint(self.angle_beta, '', self.angle_alpha)
            self.angle_alpha.user_constraints['sg_1']()
            self.angle_alpha.user_constraints['sg_2'] = ObjConstraint(self.angle_gamma, '', self.angle_alpha)
            self.angle_alpha.user_constraints['sg_2']()
        elif crys_system == "tetragonal":
            self.length_a.user_constraints['sg_1'] = ObjConstraint(self.length_b, '', self.length_a)
            self.length_a.user_constraints['sg_1']()
            self.angle_alpha = 90
            self.angle_alpha.enabled = False
            self.angle_beta = 90
            self.angle_beta.enabled = False
            self.angle_gamma = 90
            self.angle_gamma.enabled = False
        elif crys_system == "orthorhombic":
            self.angle_alpha = 90
            self.angle_alpha.enabled = False
            self.angle_beta = 90
            self.angle_beta.enabled = False
            self.angle_gamma = 90
            self.angle_gamma.enabled = False
        elif crys_system == "monoclinic":
            self.angle_alpha = 90
            self.angle_alpha.enabled = False
            self.angle_gamma = 90
            self.angle_gamma.enabled = False
        else:
            raise TypeError('The current crystal system is unknown so symmetry cannot be enforced')

    def to_cell(self) -> Lattice:
        """
        Convert the PeriodicLattice to a standard Lattice. i.e. drop spacegroup. The return is a copy

        :return: Lattice with spacegroup information dropped.
        :rtype: Lattice
        """
        return Lattice.from_pars(*self.lengths, *self.angles, interface=None)

    def __copy__(self):
        """
        Returns a deep copy of the Periodic-Lattice. Note that the spacegroup parameter is also a copy!!

        :return: Deep copy of self
        :rtype: PeriodicLattice
        """
        return self.__class__.from_pars(*self.lengths, *self.angles, self.spacegroup.hermann_mauguin,
                                        interface=self.interface)

    def to_star(self):
        """
        Provide a star object of the current lattice. Note that the spacegroup is omitted!

        :return:
        :rtype:
        """
        return StarSection(self.to_cell())

    @classmethod
    def from_star(cls, in_string):
        return StarSection.from_string(cls, in_string)

    def __new_SG_setter(self, obj, value):
        self.clear_sym()
        self.__previous_SG_setter(obj, value)
        self.enforce_sym()


def get_integer_index(miller_index: Sequence[float], round_dp: int = 4, verbose: bool = True) -> Tuple[int, int, int]:
    """
    Attempt to convert a vector of floats to whole numbers.
    Args:
        miller_index (list of float): A list miller indexes.
        round_dp (int, optional): The number of decimal places to round the
            miller index to.
        verbose (bool, optional): Whether to print warnings.
    Returns:
        (tuple): The Miller index.
    """
    mi = np.asarray(miller_index)
    # deal with the case we have small irregular floats
    # that are all equal or factors of each other
    mi /= min([m for m in mi if m != 0])
    mi /= np.max(np.abs(mi))

    # deal with the case we have nice fractions
    md = [Fraction(n).limit_denominator(12).denominator for n in mi]
    mi *= reduce(lambda x, y: x * y, md)
    int_miller_index = np.int_(np.round(mi, 1))
    mi /= np.abs(reduce(math.gcd, int_miller_index))

    # round to a reasonable precision
    mi = np.array([round(h, round_dp) for h in mi])

    # need to recalculate this after rounding as values may have changed
    int_miller_index = np.int_(np.round(mi, 1))
    if np.any(np.abs(mi - int_miller_index) > 1e-6) and verbose:
        warnings.warn("Non-integer encountered in Miller index")
    else:
        mi = int_miller_index

    # minimise the number of negative indexes
    mi += 0  # converts -0 to 0

    def n_minus(index):
        return len([h for h in index if h < 0])

    if n_minus(mi) > n_minus(mi * -1):
        mi *= -1

    # if only one index is negative, make sure it is the smallest
    # e.g. (-2 1 0) -> (2 -1 0)
    if (
            sum(mi != 0) == 2
            and n_minus(mi) == 1
            and abs(min(mi)) > max(mi)
    ):
        mi *= -1

    return tuple(mi)  # type: ignore


def get_points_in_spheres(all_coords: np.ndarray, center_coords: np.ndarray, r: float,
                          pbc: Union[bool, List[bool]] = True, numerical_tol: float = 1e-8,
                          lattice: Lattice = None, return_fcoords: bool = False,
                          ) -> List[List[Tuple[np.ndarray, float, int, np.ndarray]]]:
    """
    For each point in `center_coords`, get all the neighboring points in `all_coords` that are within the
    cutoff radius `r`.
    Args:
        all_coords: (list of cartesian coordinates) all available points
        center_coords: (list of cartesian coordinates) all centering points
        r: (float) cutoff radius
        pbc: (bool or a list of bool) whether to set periodic boundaries
        numerical_tol: (float) numerical tolerance
        lattice: (Lattice) lattice to consider when PBC is enabled
        return_fcoords: (bool) whether to return fractional coords when pbc is set.
    Returns:
        List[List[Tuple[coords, distance, index, image]]]
    """
    if isinstance(pbc, bool):
        pbc = [pbc] * 3
    pbc = np.array(pbc, dtype=bool)
    if return_fcoords and lattice is None:
        raise ValueError("Lattice needs to be supplied to compute fractional coordinates")
    center_coords_min = np.min(center_coords, axis=0)
    center_coords_max = np.max(center_coords, axis=0)
    # The lower bound of all considered atom coords
    global_min = center_coords_min - r - numerical_tol
    global_max = center_coords_max + r + numerical_tol
    if np.any(pbc):
        if lattice is None:
            raise ValueError("Lattice needs to be supplied when considering periodic boundary")
        recp_len = np.array(lattice.reciprocal_lattice.lengths)
        maxr = np.ceil((r + 0.15) * recp_len / (2 * math.pi))
        frac_coords = lattice.get_fractional_coords(center_coords)
        nmin_temp = np.floor(np.min(frac_coords, axis=0)) - maxr
        nmax_temp = np.ceil(np.max(frac_coords, axis=0)) + maxr
        nmin = np.zeros_like(nmin_temp)
        nmin[pbc] = nmin_temp[pbc]
        nmax = np.ones_like(nmax_temp)
        nmax[pbc] = nmax_temp[pbc]
        all_ranges = [np.arange(x, y, dtype='int64') for x, y in zip(nmin, nmax)]
        matrix = lattice.matrix
        # temporarily hold the fractional coordinates
        image_offsets = lattice.get_fractional_coords(all_coords)
        all_fcoords = []
        # only wrap periodic boundary
        for k in range(3):
            if pbc[k]:  # type: ignore
                all_fcoords.append(np.mod(image_offsets[:, k:k + 1], 1))
            else:
                all_fcoords.append(image_offsets[:, k:k + 1])
        all_fcoords = np.concatenate(all_fcoords, axis=1)
        image_offsets = image_offsets - all_fcoords
        coords_in_cell = np.dot(all_fcoords, matrix)
        # Filter out those beyond max range
        valid_coords = []
        valid_images = []
        valid_indices = []
        for image in itertools.product(*all_ranges):
            coords = np.dot(image, matrix) + coords_in_cell
            valid_index_bool = np.all(np.bitwise_and(coords > global_min[None, :], coords < global_max[None, :]),
                                      axis=1)
            ind = np.arange(len(all_coords))
            if np.any(valid_index_bool):
                valid_coords.append(coords[valid_index_bool])
                valid_images.append(np.tile(image, [np.sum(valid_index_bool), 1]) - image_offsets[valid_index_bool])
                valid_indices.extend([k for k in ind if valid_index_bool[k]])
        if len(valid_coords) < 1:
            return [[]] * len(center_coords)
        valid_coords = np.concatenate(valid_coords, axis=0)
        valid_images = np.concatenate(valid_images, axis=0)

    else:
        valid_coords = all_coords
        valid_images = [[0, 0, 0]] * len(valid_coords)
        valid_indices = np.arange(len(valid_coords))

    # Divide the valid 3D space into cubes and compute the cube ids
    all_cube_index = _compute_cube_index(valid_coords, global_min, r)
    nx, ny, nz = _compute_cube_index(global_max, global_min, r) + 1
    all_cube_index = _three_to_one(all_cube_index, ny, nz)
    site_cube_index = _three_to_one(_compute_cube_index(center_coords, global_min, r), ny, nz)
    # create cube index to coordinates, images, and indices map
    cube_to_coords = collections.defaultdict(list)  # type: Dict[int, List]
    cube_to_images = collections.defaultdict(list)  # type: Dict[int, List]
    cube_to_indices = collections.defaultdict(list)  # type: Dict[int, List]
    for i, j, k, l in zip(all_cube_index.ravel(), valid_coords,
                          valid_images, valid_indices):
        cube_to_coords[i].append(j)
        cube_to_images[i].append(k)
        cube_to_indices[i].append(l)

    # find all neighboring cubes for each atom in the lattice cell
    site_neighbors = find_neighbors(site_cube_index, nx, ny, nz)
    neighbors = []  # type: List[List[Tuple[np.ndarray, float, int, np.ndarray]]]

    for i, j in zip(center_coords, site_neighbors):
        l1 = np.array(_three_to_one(j, ny, nz), dtype=int).ravel()
        # use the cube index map to find the all the neighboring
        # coords, images, and indices
        ks = [k for k in l1 if k in cube_to_coords]
        if not ks:
            neighbors.append([])
            continue
        nn_coords = np.concatenate([cube_to_coords[k] for k in ks], axis=0)
        nn_images = itertools.chain(*[cube_to_images[k] for k in ks])
        nn_indices = itertools.chain(*[cube_to_indices[k] for k in ks])
        dist = np.linalg.norm(nn_coords - i[None, :], axis=1)
        nns: List[Tuple[np.ndarray, float, int, np.ndarray]] = []
        for coord, index, image, d in zip(nn_coords, nn_indices, nn_images, dist):
            # filtering out all sites that are beyond the cutoff
            # Here there is no filtering of overlapping sites
            if d < r + numerical_tol:
                if return_fcoords and (lattice is not None):
                    coord = np.round(lattice.get_fractional_coords(coord), 10)
                nn = (coord, float(d), int(index), image)
                nns.append(nn)
        neighbors.append(nns)
    return neighbors


# The following internal methods are used in the get_points_in_sphere method.
def _compute_cube_index(coords: np.ndarray, global_min: float, radius: float
                        ) -> np.ndarray:
    """
    Compute the cube index from coordinates
    Args:
        coords: (nx3 array) atom coordinates
        global_min: (float) lower boundary of coordinates
        radius: (float) cutoff radius
    Returns: (nx3 array) int indices
    """
    return np.array(np.floor((coords - global_min) / radius), dtype=int)


def _one_to_three(label1d: np.ndarray, ny: int, nz: int) -> np.ndarray:
    """
    Convert a 1D index array to 3D index array
    Args:
        label1d: (array) 1D index array
        ny: (int) number of cells in y direction
        nz: (int) number of cells in z direction
    Returns: (nx3) int array of index
    """
    last = np.mod(label1d, nz)
    second = np.mod((label1d - last) / nz, ny)
    first = (label1d - last - second * nz) / (ny * nz)
    return np.concatenate([first, second, last], axis=1)


def _three_to_one(label3d: np.ndarray, ny: int, nz: int) -> np.ndarray:
    """
    The reverse of _one_to_three
    """
    return np.array(label3d[:, 0] * ny * nz +
                    label3d[:, 1] * nz + label3d[:, 2]).reshape((-1, 1))


def find_neighbors(label: np.ndarray, nx: int, ny: int, nz: int
                   ) -> List[np.ndarray]:
    """
    Given a cube index, find the neighbor cube indices
    Args:
        label: (array) (n,) or (n x 3) indice array
        nx: (int) number of cells in y direction
        ny: (int) number of cells in y direction
        nz: (int) number of cells in z direction
    Returns: neighbor cell indices
    """

    array = [[-1, 0, 1]] * 3
    neighbor_vectors = np.array(list(itertools.product(*array)),
                                dtype=int)
    if np.shape(label)[1] == 1:
        label3d = _one_to_three(label, ny, nz)
    else:
        label3d = label
    all_labels = label3d[:, None, :] - neighbor_vectors[None, :, :]
    filtered_labels = []
    # filter out out-of-bound labels i.e., label < 0
    for labels in all_labels:
        ind = (labels[:, 0] < nx) * (labels[:, 1] < ny) * (labels[:, 2] < nz) * np.all(labels > -1e-5, axis=1)
        filtered_labels.append(labels[ind])
    return filtered_labels
