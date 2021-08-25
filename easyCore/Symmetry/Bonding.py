#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from typing import Tuple, Union, List

from easyCore import np
from easyCore.Symmetry.SymOp import SymmOp


class Bonding:
    def __init__(self, dl: np.ndarray, atom1: np.ndarray, atom2: np.ndarray, idx: np.ndarray, n_sym: int):
        self.dl = dl
        self.atom1 = atom1
        self.atom2 = atom2
        self.idx = idx
        self.nSym = n_sym


def generate_bonds(phase_obj, force_no_sym: bool = False,
                   max_distance: float = 8, tol: float = 1E-5, tol_dist: float = 1E-3, d_min: float = 0.5,
                   max_sym: int = None, magnetic_only: bool = False) -> Bonding:
    """
    `generate_bonds` generates all bonds up to a certain length between magnetic atoms. It also groups bonds based
    either on crystal symmetry or bond length (with `tol_dist`  tolerance) is space group is not defined.
    Sorting bonds based on length can be forced by setting the `forceNoSym` parameter to true.

    :param phase_obj: easyCore phase object for which you want the bonds to be found
    :type phase_obj: Phase
    :param force_no_sym: Do not try to work out symmetry equivalent bonds.
    :type force_no_sym: bool
    :param max_distance: Maximum distance between atoms for which you want to search for a bond
    :type max_distance: float
    :param tol: The tolerance for which we consider unit cells.
    :type tol: float
    :param tol_dist: Tolerance of distance, within two bonds are considered equivalent
    :type tol_dist: float
    :param d_min: The minimum bond length between atoms
    :type d_min: float
    :param max_sym: Return only the 0->`max_sym` symmetry unique bonds.
    :type max_sym: int
    :param magnetic_only: Search for bonds which are between magnetic atoms only.
    :type magnetic_only: bool
    :return: Structure containing bond information
    :rtype: Bonding
    """

    max_distance = max_distance + tol

    # Calculate the height of the parallelepiped of a unit cell
    h_max1 = 1 / np.sqrt(np.sum(np.linalg.inv(phase_obj.cell.matrix.T) ** 2, axis=0))
    # calculate the distance of the[1 1 1] point from the origin
    h_max2 = np.abs(np.sum(phase_obj.cell.matrix, axis=0))

    # calculate the closest point to the origin
    h_max = np.min(np.array([h_max1, h_max2]), axis=0)

    # gives the number of extra unit cells along all 3 axes that are necessary to cover the minimum bond distance
    n_c = np.ceil(max_distance / h_max)

    all_atoms = phase_obj.get_orbits(magnetic_only=magnetic_only)
    all_atoms_r = np.vstack([np.array(all_atoms[key]) for key in all_atoms.keys()])
    n_atoms = all_atoms_r.shape[0]

    c_dim = np.array([n_c[0] + 1, 2 * n_c[1] + 1, 2 * n_c[2] + 1])
    n_half_cube = np.prod(c_dim)

    # generate all cell translations
    c_tr1, c_tr2, c_tr3 = np.mgrid[0:n_c[0] + 1, -n_c[1]:n_c[1] + 1, -n_c[2]:n_c[2] + 1]
    # cell origin translations: Na x Nb x Nc x 1 x 1 x3
    c_tr = np.stack([c_tr1, c_tr2, c_tr3], axis=3).reshape((*c_tr1.shape, 1, 1, 3))
    # remove unit cells that would produce duplicate bonds mark them with NaN (enough to do along a-axis values)
    c_tr[0, :, np.array(range(int(c_dim[2]))) < int(n_c[2]), 0, 0, 0] = np.nan
    c_tr[0, np.array(range(int(c_dim[1]))) < int(n_c[1]), int(n_c[2]), 0, 0, 0] = np.nan
    # % positions of atoms in the half 'cube' in l.u.
    # % Na x Nb x Nc x 1 x nMagAtom x 3
    # % atom2
    r1 = all_atoms_r.reshape((1, 1, 1, 1, -1, 3))
    r2 = all_atoms_r.reshape((1, 1, 1, -1, 1, 3))
    a_pos = r1 + c_tr
    # generate all distances from the atoms in the (0,0,0) cell in l.u.
    # r(atom2) - r(atom1)
    # Na x Nb x Nc x nMagAtom x nMagAtom x 3
    d_r = a_pos - r2
    # mark duplicate bonds within the (0,0,0) cell with nan
    r0 = d_r[0, int(n_c[1]), int(n_c[2]), :, :, :]
    d_r[0, int(n_c[1]), int(n_c[2]), :, :, :] = r0 * (
            1 + np.tril(np.nan * np.ones((n_atoms, n_atoms))).reshape((n_atoms, n_atoms, 1)))
    # calculate the absolute value of the distances in Angstrom
    d_ra = np.sqrt(np.sum(np.einsum('abcdei,ij->abcdej', d_r, phase_obj.cell.matrix) ** 2, axis=5))
    # reshape the numbers into a column list of bonds
    # 3 x Na x Nb x Nc x nMagAtom x nMagAtom
    dl = np.transpose(np.tile(c_tr, [1, 1, 1, n_atoms, n_atoms, 1]), axes=[5, 0, 1, 2, 3, 4])
    atoms1 = np.tile(np.arange(n_atoms).reshape((1, 1, 1, 1, -1, 1)), [1, *[int(d) for d in c_dim], 1, n_atoms])
    atoms2 = np.tile(np.arange(n_atoms).reshape((1, 1, 1, 1, 1, -1)), [1, *[int(d) for d in c_dim], n_atoms, 1])
    d_ra = d_ra.reshape((1, *d_ra.shape))
    # store everything in a single matrix
    # c_mat  = [dl(:,:);atom1(1,:);atom2(1,:);d_ra(1,:)];
    dl_ = dl.reshape((3, -1), order='F')
    atom1_ = atoms1.reshape((1, -1), order='F')
    atom2_ = atoms2.reshape((1, -1), order='F')
    d_ra_ = d_ra.reshape((1, -1), order='F')

    c_mat = np.vstack((dl_, atom1_, atom2_, d_ra_))
    # remove nan bonds
    c_mat = c_mat[:, ~np.isnan(c_mat[0, :])]
    # sort according to distance
    s_index = np.argsort(c_mat[5, :])
    c_mat = c_mat[:, s_index]
    # Apply cutoff
    c_index = c_mat[5, :] <= max_distance
    c_mat = c_mat[:, c_index]
    c_idx = np.cumsum(np.array(np.insert(np.diff(c_mat[5, :]) > tol_dist, 0, True), dtype=int)) - 1
    c_mat = np.vstack((c_mat, c_idx))

    if c_mat[5, 0] < d_min:
        raise ArithmeticError(f'Some atoms are too close (d_min={c_mat[5, 0]} < {d_min}), check your crystal structure!')

    d_ra = c_mat[5, :]
    c_mat = c_mat[[0, 1, 2, 3, 4, 6], :]
    basis_vector = phase_obj.cell.matrix
    sym_ops = phase_obj.spacegroup.symmetry_opts
    if not force_no_sym:
        n_mat = []
        if max_sym is None:
            max_sym = np.inf
        max_idx_sym = max(c_idx[c_idx <= max_sym])
        ii = 0
        idx = 0
        while ii <= max_idx_sym:
            sort_ms = c_mat[:, c_idx == ii]
            while sort_ms.shape[1] > 0:
                gen_c, un_c = bond(all_atoms_r, basis_vector, sort_ms[:, 0], sym_ops, tol)
                gen_c_all = np.hstack((gen_c, np.vstack((-gen_c[0:3, :], gen_c[[4, 3], :]))))
                # remove from sort_ms the identical couplings
                i_new, _ = isnew(gen_c_all, sort_ms[0:5, :], tol)
                sort_ms = sort_ms[:, i_new]
                # Remove identical couplings from the symmetry generated list
                gen_c = gen_c[:, un_c]
                if np.sum(~i_new) != np.sum(un_c):
                    raise ArithmeticError(f'Symmetry error! ii={ii}, idx={idx}. Try to change ''tol'' parameter.')
                n_mat.append(np.vstack((gen_c, np.ones((1, gen_c.shape[1])) * idx)))
                idx += 1
            ii += 1
        n_mat = np.hstack(n_mat)
        # include the increase of bond index in case bonds are split due to symmetry inequivalency
        c_mat = c_mat[:, c_mat[5, :] > max_idx_sym]
        c_mat[5, :] = c_mat[5, :] + n_mat[5, -1] - max_idx_sym
        c_mat = np.hstack((n_mat, c_mat))

        # Save the value of maximum bond index that is generated by symmetry
        n_sym = n_mat[5, -1] + 1
    else:
        n_sym = 0

    return Bonding(c_mat[0:3, :].astype(int),
                   c_mat[3, :].astype(int),
                   c_mat[4, :].astype(int),
                   c_mat[5, :].astype(int),
                   n_sym)


def bond(r: np.ndarray, bv: np.ndarray, single_bond: np.ndarray,
         sym_op: List[SymmOp], tol: float = 1e-5) -> Tuple[np.ndarray, Union[np.ndarray, np.ndarray]]:
    """
    generates all bonds that are symmetry equivalent to the given `bond`. The function uses the given space group
    operators and positions of magnetic atoms to return a list of equivalent bonds in a matrix. The function also checks
     the validity of the calculation by measuring the length of each equivalent bond using the given `bv` base and if
     the difference in length between equivalent bonds is larger than the tolerance throws a warning.

    :param r: Positions of the magnetic atoms in lattice units stored in a matrix
    :type r: np.ndarray
    :param bv: Basis vectors that define the lattice, used for checking the bond length of equivalent bonds
    :type bv: np.ndarray
    :param single_bond: Vector that contains the starting bond with elements of `[dl_a dl_b dl_c atom_1 atom_2]`,
    where `dl`
    is vector of lattice translation between the two atoms if they are not in the same unit cell in lattice units,
    `atom_1` and `atom_2` are indices of atoms in the list of positions stored in `r`.
    :type single_bond: np.ndarray
    :param sym_op: List of symmetry operations for the given spacegroup
    :type sym_op: list
    :param tol: Tolerance
    :type tol: float
    :return:
    :rtype:
    """
    tol_dist = 1e-5

    r1 = r[int(single_bond[3]), :].T
    r2 = r[int(single_bond[4]), :].T
    dl = single_bond[[0, 1, 2]]

    # Generate new atomic positions and translation vectors
    r1new = np.array([s.operate(r1) for s in sym_op]).T
    r2new = np.array([s.operate(r2) for s in sym_op]).T
    dlnew = np.array([s.apply_rotation_only(dl) for s in sym_op]).T - cfloor(r1new, tol) + cfloor(r2new, tol)

    # Modulo to get atoms in the first unit cell
    r1new = np.mod(r1new, 1)
    r2new = np.mod(r2new, 1)

    # Throw away generated couplings with wrong distance
    i_new, atom1 = isnewUC(r.T, r1new, tol_dist)
    if np.any(i_new):
        raise ArithmeticError('The generated positions for atom1 are wrong!')
    i_new, atom2 = isnewUC(r.T, r2new, tol_dist)
    if np.any(i_new):
        raise ArithmeticError('The generated positions for atom2 are wrong!')
    dist = np.sqrt(np.sum(np.dot(bv.T, (r.T[:, atom2] - r.T[:, atom1] + dlnew)) ** 2, axis=0))
    right_dist = np.abs(dist - dist[0]) < tol
    if not np.all(right_dist):
        # TODO This should raise a warning
        print('Symmetry generated couplings are dropped!')
    gen_cp = np.vstack((dlnew, atom1.reshape((1, -1)), atom2.reshape((1, -1))))
    gen_cp = gen_cp[:, right_dist]
    ugen_cp = uniqueB(gen_cp)

    return gen_cp, ugen_cp


def cfloor(r0: np.ndarray, tol: float) -> np.ndarray:
    """
    Floor for atomic positions

    floor(1-tol) == 1

    :param r0: Matrix of positions
    :type r0: np.ndarray
    :param tol: Tolerance
    :type tol: float
    :return: Matrix `r0` where values have been floored
    :rtype: np.ndarray
    """

    r = np.floor(r0)
    idx = np.abs(r0 - r) > 1 - tol
    r[idx] = r[idx] + 1
    return r


def isnewUC(matrix_a: np.ndarray, matrix_b: np.ndarray, tol: float) -> \
        Tuple[Union[np.ndarray, bool], Union[np.ndarray, int, float, complex]]:
    """
    Selects the new vectors from B within the first unit cell.

    Dimensions of A and B have to be [3 n_a] and [3 n_b] respectively. A vector in B is considered new,
    if d(mod(vA-vB,1))<tol.

    :param matrix_a: First matrix
    :type matrix_a: np.ndarray
    :param matrix_b: Second matrix
    :type matrix_b: np.ndarray
    :param tol: Tolerance
    :type tol: float
    :return: Logical numpy array saying of the vector is new and a numpy array with the index
    :rtype: Tuple[np.ndarray, np.ndarray]
    """

    n_a = matrix_a.shape[1]
    n_b = matrix_b.shape[1]

    C = matrix_a.shape[0]
    if C is not matrix_b.shape[0]:
        raise AttributeError('First dimension of A must be the same as that of B')

    aa = np.tile(matrix_a.reshape((*matrix_a.shape, 1)).transpose((1, 2, 0)), (1, n_b, 1))
    bb = np.tile(matrix_b.reshape((*matrix_b.shape, 1)).transpose((2, 1, 0)), (n_a, 1, 1))
    notequal = np.sum(cmod(aa - bb, tol) ** 2, axis=2) > tol

    is_new = np.all(notequal, axis=0)
    idx = np.arange(n_b)
    sym_idx = np.max(np.array(~notequal[:, idx[~is_new]], dtype=int) * np.arange(n_a).reshape((-1, 1)), axis=0)

    return is_new, sym_idx


def isnew(matrix_a: np.ndarray, matrix_b: np.ndarray, tol: float) -> \
        Tuple[Union[np.ndarray, bool], Union[np.ndarray, int, float, complex]]:
    """
    Selects the new vectors from B within the first unit cell.

    Dimensions of A and B have to be [3 nA] and [3 nB] respectively. A vector in B is considered new,
    if d(mod(vA-vB,1))<tol.

    :param matrix_a: First matrix
    :type matrix_a: np.ndarray
    :param matrix_b: Second matrix
    :type matrix_b: np.ndarray
    :param tol: Tolerance
    :type tol: float
    :return: Logical numpy array saying of the vector is new and a numpy array with the index
    :rtype: Tuple[np.ndarray, np.ndarray]
    """

    if not matrix_a.shape[0] == matrix_b.shape[0]:
        raise AttributeError

    aa = np.tile(matrix_a.reshape((*matrix_a.shape, 1)).transpose((1, 2, 0)), (1, matrix_b.shape[1], 1))
    bb = np.tile(matrix_b.reshape((*matrix_b.shape, 1)).transpose((2, 1, 0)), (matrix_a.shape[1], 1, 1))
    notequal = np.sum(np.abs(aa - bb) ** 2, axis=2) > tol

    is_new = np.all(notequal, axis=0)
    idx = np.arange(matrix_b.shape[1])

    def sym_f(this_idx):
        return np.where(~notequal[:, this_idx])[0][0]

    sym_idx = np.array([sym_f(this_idx) for this_idx in idx[~is_new]])
    return is_new, sym_idx


def cmod(r: np.ndarray, tol: float) -> np.ndarray:
    """
    Modulus within tolerance

    :param r: Matrix to be operated on
    :type r: np.ndarray
    :param tol: Tolerance
    :type tol: float
    :return: `r` with modulus applied
    :rtype: np.ndarray
    """
    r = np.mod(r, 1)
    r[r > 1 - tol] = r[r > 1 - tol] - 1
    return r


def uniqueB(bond_matrix: np.ndarray) -> Union[np.ndarray, bool]:
    """
    Given an array of bonds, which ones are unique. Bonds has the shape [dl, atom1, atom2]

    :param bond_matrix: Array of bonds
    :type bond_matrix: np.ndarray
    :return: Logical array for if the corresponding bond is unique
    :rtype: np.ndarray
    """
    n_c = bond_matrix.shape[1]
    c1 = bond_matrix.reshape((*bond_matrix.shape, 1)).transpose((1, 2, 0))
    c2 = bond_matrix.reshape((*bond_matrix.shape, 1)).transpose((2, 1, 0))
    nc1 = np.vstack((-bond_matrix[0:3, :], bond_matrix[[4, 3], :])).reshape((5, -1, 1)).transpose((1, 2, 0))

    unique_b = np.all(np.triu(np.any(np.not_equal(c1, c2), axis=2) &
                              np.any(np.not_equal(nc1, c2), axis=2)) |
                      np.tril(np.ones(n_c, dtype=bool)), axis=0)
    return unique_b
