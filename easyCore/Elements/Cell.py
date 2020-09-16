__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from copy import deepcopy

import numpy as np
from typing import Tuple, Union, List

from easyCore import ureg
from easyCore.Utils.decorators import memoized
from easyCore.Utils.typing import Vector3Like
from easyCore.Objects.Base import Parameter, BaseObj

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


class Cell(BaseObj):

    def __init__(self, length_a: Parameter, length_b: Parameter, length_c: Parameter,
                 angle_alpha: Parameter, angle_beta: Parameter, angle_gamma: Parameter):
        super().__init__('crystallographic_cell',
                         length_a=length_a, length_b=length_b, length_c=length_c,
                         angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma)

    # Class constructors
    @classmethod
    def default(cls) -> "Cell":
        """
        Default constructor for a crystallographic unit cell.

        :return: Default crystallographic unit cell container
        :rtype: Cell
        """
        length_a = Parameter('length_a', **CELL_DETAILS['length'])
        length_b = Parameter('length_b', **CELL_DETAILS['length'])
        length_c = Parameter('length_c', **CELL_DETAILS['length'])
        angle_alpha = Parameter('angle_alpha', **CELL_DETAILS['angle'])
        angle_beta = Parameter('angle_beta', **CELL_DETAILS['angle'])
        angle_gamma = Parameter('angle_gamma', **CELL_DETAILS['angle'])
        return cls(length_a, length_b, length_c, angle_alpha, angle_beta, angle_gamma)

    @classmethod
    def from_parameters(cls, length_a: float, length_b: float, length_c: float,
                        angle_alpha: float, angle_beta: float, angle_gamma: float, ang_unit: str = 'deg') -> "Cell":
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
        :rtype: Cell
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
                   angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma)

    @classmethod
    def from_matrix(cls, matrix: Union[List[float], List[List[float]], np.ndarray]) -> "Cell":
        """
        Construct a crystallographic unit cell from the lattice matrix

        :param matrix: Matrix describing the crystallographic unit cell in the form of a numpy array,
        1x9 list or 3x3 list.
        :type matrix: np.ndarray, List[float], List[List[float]]
        :return: Crystallographic unit cell container
        :rtype: Cell
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
        return cls.from_parameters(*lengths, *angles)

    @classmethod
    def cubic(cls, a: float) -> "Cell":
        """
        Convenience constructor for a cubic lattice.

        :param a: The *a* lattice parameter of the cubic cell.
        :type a: float
        :return: Crystallographic unit cell container
        :rtype: Cell
        """
        return cls.from_parameters(a, a, a, 90, 90, 90)

    @classmethod
    def tetragonal(cls, a: float, c: float) -> "Cell":
        """
        Convenience constructor for a tetragonal lattice.

        :param a: *a* lattice parameter of the tetragonal cell.
        :type a: float
        :param c: *c* lattice parameter of the tetragonal cell.
        :type c: float
        :return: Crystallographic unit cell container
        :rtype: Cell
        """
        return cls.from_parameters(a, a, c, 90, 90, 90)

    @classmethod
    def orthorhombic(cls, a: float, b: float, c: float) -> "Cell":
        """
        Convenience constructor for an orthorhombic lattice.

        :param a: *a* lattice parameter of the orthorhombic cell.
        :type a: float
        :param b: *b* lattice parameter of the orthorhombic cell.
        :type b: float
        :param c: *c* lattice parameter of the orthorhombic cell.
        :type c: float
        :return: Crystallographic unit cell container
        :rtype: Cell
        """
        return cls.from_parameters(a, b, c, 90, 90, 90)

    @classmethod
    def monoclinic(cls, a: float, b: float, c: float, beta: float) -> "Cell":
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
        :rtype: Cell
        """
        return cls.from_parameters(a, b, c, 90, beta, 90)

    @classmethod
    def hexagonal(cls, a: float, c: float) -> "Cell":
        """
        Convenience constructor for a hexagonal lattice of dimensions a x a x c

        :param a: *a* lattice parameter of the hexagonal cell.
        :type a: float
        :param c: *c* lattice parameter of the hexagonal cell.
        :type c: float
        :return: Crystallographic unit cell container
        :rtype: Cell
        """
        return cls.from_parameters(a, a, c, 90, 90, 120)

    @classmethod
    def rhombohedral(cls, a: float, alpha: float) -> "Cell":
        """
        Convenience constructor for a rhombohedral lattice of dimensions a x a x a.

        :param a: *a* lattice parameter of the monoclinc cell.
        :type a: float
        :param alpha: Angle for the rhombohedral lattice in degrees.
        :type alpha: float
        :return: Crystallographic unit cell container
        :rtype: Cell
        """
        return cls.from_parameters(a, a, a, alpha, alpha, alpha)

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
        self.length_a.raw_value = new_a_value

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
        self.length_b.raw_value = new_b_value

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
        self.length_c.raw_value = new_c_value

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
        self.angle_alpha.raw_value = new_alpha_value

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
        self.angle_beta.raw_value = new_beta_value

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
        self.angle_gamma.raw_value = new_gamma_value

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
        return np.inv(self.matrix)

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
    def reciprocal_lattice(self) -> "Cell":
        """
        Return the reciprocal lattice. Note that this is the standard
        reciprocal lattice used for solid state physics with a factor of 2 *
        pi. If you are looking for the crystallographic reciprocal lattice,
        use the reciprocal_lattice_crystallographic property.

        :return: New cell in the reciprocal lattice
        :rtype: Cell
        """
        v = np.linalg.inv(self.matrix).T
        return self.__class__.from_matrix(v * 2 * np.pi)

    @property
    def reciprocal_lattice_crystallographic(self) -> "Cell":
        """
        Returns the *crystallographic* reciprocal lattice, i.e., no factor of
        2 * pi.

        :return: New cell in the *crystallographic* reciprocal lattice
        :rtype: Cell
        """
        return Cell.from_matrix(self.reciprocal_lattice.matrix / (2 * np.pi))

    def scale(self, new_volume: float) -> "Cell":
        """
        Return a new Cell with volume new_volume by performing a
        scaling of the lattice vectors so that length proportions and angles
        are preserved.

        :param new_volume: New volume to scale to.
        :type new_volume: float
        :return: New cell scaled to volume
        :rtype: Cell
        """

        lengths = self.lengths
        versors = self.matrix / lengths
        geo_factor = np.abs(np.dot(np.cross(versors[0], versors[1]), versors[2]))
        ratios = np.array(lengths) / lengths[2]
        new_c = (new_volume / (geo_factor * np.prod(ratios))) ** (1 / 3.0)
        return self.__class__.from_matrix(versors * (new_c * ratios))

    def scale_lengths(self, length_scales: Union[float, Vector3Like]) -> "Cell":
        """
        Return a new Cell where the cell lengths have been scaled by the scaling
        factors. Angles are preserved.

        :param length_scales: Scaling for each length or universal scaling factor
        :type length_scales: Union[float, Vector3Like]
        :return: New Cell scaled by user supplied scale factors
        :rtype: Cell
        """
        if isinstance(length_scales, float):
            length_scales = 3 * [length_scales]
        new_lengths = np.array(length_scales) * np.array(self.lengths)
        return self.__class__.from_parameters(*new_lengths, *self.angles)

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
        Returns true if the Cell is hexagonal.

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
        return 'Cell: (a:{:.2f}, b:{:.2f}, c:{:.2f}, alpha:{:.2f}, beta:{:.2f}, gamma:{:.2f}) '.format(self.a, self.b,
                                                                                                       self.c,
                                                                                                       self.alpha,
                                                                                                       self.beta,
                                                                                                       self.gamma)
