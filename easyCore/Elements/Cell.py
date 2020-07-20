__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Tuple, Union, List

import numpy as np
from easyCore import borg, ureg
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
    _borg = borg

    def __init__(self, length_a: Parameter, length_b: Parameter, length_c: Parameter,
                 angle_alpha: Parameter, angle_beta: Parameter, angle_gamma: Parameter):
        super().__init__('crystallographic_cell',
                         length_a=length_a, length_b=length_b, length_c=length_c,
                         angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma)

    @classmethod
    def default(cls) -> 'Cell':
        """
        Default constructor for a crystallographic unit cell
        :return: Default crystallographic unit cell container
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
                 angle_alpha: float, angle_beta: float, angle_gamma: float) -> 'Cell':
        """
        Constructor of a crystallographic unit cell when parameters are known
        :param length_a: Unit cell length a
        :param length_b: Unit cell length b
        :param length_c:  Unit cell length c
        :param angle_alpha: Unit cell angle alpha
        :param angle_beta:  Unit cell angle beta
        :param angle_gamma:  Unit cell angle gamma
        :return:
        """
        length_a = Parameter('length_a', length_a, **CELL_DETAILS['length'].copy().pop('value'))
        length_b = Parameter('length_b', length_b, **CELL_DETAILS['length'].copy().pop('value'))
        length_c = Parameter('length_c', length_c, **CELL_DETAILS['length'].copy().pop('value'))
        angle_alpha = Parameter('angle_alpha', angle_alpha, **CELL_DETAILS['angle'].copy().pop('value'))
        angle_beta = Parameter('angle_beta', angle_beta, **CELL_DETAILS['angle'].copy().pop('value'))
        angle_gamma = Parameter('angle_gamma', angle_gamma, **CELL_DETAILS['angle'].copy().pop('value'))

        return cls(length_a=length_a, length_b=length_b, length_c=length_c,
                   angle_alpha=angle_alpha, angle_beta=angle_beta, angle_gamma=angle_gamma)

    @classmethod
    def from_matrix(cls, matrix: Union[List[float], List[List[float]], np.ndarray]):
        matrix = np.array(matrix, dtype=np.float64).reshape((3, 3))
        lengths = np.sqrt(np.sum(matrix ** 2, axis=1))
        angles = np.zeros(3)
        for i in range(3):
            j = (i + 1) % 3
            k = (i + 2) % 3
            angles[i] = np.dot(matrix[j], matrix[k]) / (lengths[j] * lengths[k])
            angles[i] = np.max(np.min(angles[i], 1), - 1)
        angles = np.arccos(angles) * 180.0 / np.pi
        return Cell.from_parameters(*lengths, *angles)

    @staticmethod
    def cubic(a: float):
        """
        Convenience constructor for a cubic lattice.
        Args:
            a (float): The *a* lattice parameter of the cubic cell.
        Returns:
            Cubic lattice of dimensions a x a x a.
        """
        return Cell.from_parameters(a, a, a, 90, 90, 90)

    @staticmethod
    def tetragonal(a: float, c: float):
        """
        Convenience constructor for a tetragonal lattice.
        Args:
            a (float): *a* lattice parameter of the tetragonal cell.
            c (float): *c* lattice parameter of the tetragonal cell.
        Returns:
            Tetragonal lattice of dimensions a x a x c.
        """
        return Cell.from_parameters(a, a, c, 90, 90, 90)

    @staticmethod
    def orthorhombic(a: float, b: float, c: float):
        """
        Convenience constructor for an orthorhombic lattice.
        Args:
            a (float): *a* lattice parameter of the orthorhombic cell.
            b (float): *b* lattice parameter of the orthorhombic cell.
            c (float): *c* lattice parameter of the orthorhombic cell.
        Returns:
            Orthorhombic lattice of dimensions a x b x c.
        """
        return Cell.from_parameters(a, b, c, 90, 90, 90)

    @staticmethod
    def monoclinic(a: float, b: float, c: float, beta: float):
        """
        Convenience constructor for a monoclinic lattice.
        Args:
            a (float): *a* lattice parameter of the monoclinc cell.
            b (float): *b* lattice parameter of the monoclinc cell.
            c (float): *c* lattice parameter of the monoclinc cell.
            beta (float): *beta* angle between lattice vectors b and c in
                degrees.
        Returns:
            Monoclinic lattice of dimensions a x b x c with non right-angle
            beta between lattice vectors a and c.
        """
        return Cell.from_parameters(a, b, c, 90, beta, 90)

    @staticmethod
    def hexagonal(a: float, c: float):
        """
        Convenience constructor for a hexagonal lattice.
        Args:
            a (float): *a* lattice parameter of the hexagonal cell.
            c (float): *c* lattice parameter of the hexagonal cell.
        Returns:
            Hexagonal lattice of dimensions a x a x c.
        """
        return Cell.from_parameters(a, a, c, 90, 90, 120)

    @staticmethod
    def rhombohedral(a: float, alpha: float):
        """
        Convenience constructor for a rhombohedral lattice.
        Args:
            a (float): *a* lattice parameter of the rhombohedral cell.
            alpha (float): Angle for the rhombohedral lattice in degrees.
        Returns:
            Rhombohedral lattice of dimensions a x a x a.
        """
        return Cell.from_parameters(a, a, a, alpha, alpha, alpha)

    def lengths(self) -> Tuple[float, float, float]:
        return (self.length_a.raw_value, self.length_b.raw_value, self.length_c.raw_value)

    def angles(self) -> Tuple[float, float, float]:
        return (self.angle_alpha.raw_value, self.angle_beta.raw_value, self.angle_gamma.raw_value)
    
    @property
    def matrix(self) -> np.ndarray:

        (a, b, c) = self.lengths()
        (alpha, beta, gamma) = self.angles()
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

    @property
    def inv_matrix(self) -> np.ndarray:
        """
        Inverse of lattice matrix.
        """
        return np.inv(self.matrix)

    @property
    def metric_tensor(self) -> np.ndarray:
        """
        The metric tensor of the lattice.
        """
        matrix = self.matrix
        return np.dot(matrix, self.matrix.T)

    def get_cartesian_coords(self, fractional_coords: Vector3Like) -> np.ndarray:
        """
        Returns the cartesian coordinates given fractional coordinates.
        Args:
            fractional_coords (3x1 array): Fractional coords.
        Returns:
            Cartesian coordinates
        """
        return np.dot(fractional_coords, self.matrix)

    def get_fractional_coords(self, cart_coords: Vector3Like) -> np.ndarray:
        """
        Returns the fractional coordinates given cartesian coordinates.
        Args:
            cart_coords (3x1 array): Cartesian coords.
        Returns:
            Fractional coordinates.
        """
        return np.dot(cart_coords, self.inv_matrix)

    def get_vector_along_lattice_directions(self, cart_coords: Vector3Like) -> np.ndarray:
        """
        Returns the coordinates along lattice directions given cartesian coordinates.
        Note, this is different than a projection of the cartesian vector along the
        lattice parameters. It is simply the fractional coordinates multiplied by the
        lattice vector magnitudes.
        Args:
            cart_coords (3x1 array): Cartesian coords.
        Returns:
            Lattice coordinates.
        """
        return self.lengths() * self.get_fractional_coords(cart_coords)

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
        return Cell.from_matrix(v * 2 * np.pi)

    @property
    def reciprocal_lattice_crystallographic(self) -> "Cell":
        """
        Returns the *crystallographic* reciprocal lattice, i.e., no factor of
        2 * pi.

        :return: New cell in the *crystallographic* reciprocal lattice
        :rtype: Cell
        """
        return Cell.from_matrix(self.reciprocal_lattice.matrix / (2 * np.pi))

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

        lengths = self.lengths()
        versors = self.matrix / lengths
        geo_factor = np.abs(np.dot(np.cross(versors[0], versors[1]), versors[2]))
        ratios = np.array(lengths) / lengths[2]
        new_c = (new_volume / (geo_factor * np.prod(ratios))) ** (1 / 3.0)
        return Cell.from_matrix(versors * (new_c * ratios))

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
            length_scales = 3*[length_scales]
        new_lengths = np.array(length_scales) * np.array(self.lengths())
        return Cell.from_parameters(*new_lengths, *self.angles())

    def is_orthogonal(self) -> bool:
        """
        Returns true if the cell is orthogonal (all angles 90 degrees)

        :return: Whether all angles are 90 degrees.
        :rtype: bool
        """
        return all([abs(a - 90) < 1e-5 for a in self.angles()])

    def is_hexagonal(self, hex_angle_tol: float = 5, hex_length_tol: float = 0.01) -> bool:
        """
        Returns true if the Cell is hexagonal.

        :param hex_angle_tol: Angle tolerance
        :param hex_length_tol: Length tolerance
        :return: Whether lattice corresponds to hexagonal lattice.
        :rtype: bool
        """
        lengths = self.lengths()
        angles = self.angles()
        right_angles = [i for i in range(3) if abs(angles[i] - 90) < hex_angle_tol]
        hex_angles = [i for i in range(3)
                      if abs(angles[i] - 60) < hex_angle_tol or abs(angles[i] - 120) < hex_angle_tol]

        return (
            len(right_angles) == 2 and
            len(hex_angles) == 1 and
            abs(lengths[right_angles[0]] - lengths[right_angles[1]]) < hex_length_tol
        )

    def __repr__(self) -> str:
        return 'Cell: (a:{}, b:{}, c:{}, alpha:{}, beta:{}, gamma:{}) '.format(self.length_a, self.length_b,
                                                                               self.length_c,
                                                                               self.angle_alpha, self.angle_beta,
                                                                               self.angle_gamma)
