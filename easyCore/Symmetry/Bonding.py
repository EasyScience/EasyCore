__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Tuple, Union, List

from easyCore import np
from easyCore.Symmetry.SymOp import SymmOp


class Bonding:
    def __init__(self, dl, atom1, atom2, idx, nSym):
        self.dl = dl
        self.atom1 = atom1
        self.atom2 = atom2
        self.idx = idx
        self.nSym = nSym


def generate_bonds(phaseObj, force_no_sym: bool = False,
                   max_distance: float = 8, tol: float = 1E-5, tol_dist: float = 1E-3, d_min: float = 0.5,
                   max_sym: int = None, magnetic_only: bool = False) -> Bonding:
    """
    `generate_bonds` generates all bonds up to a certain length between magnetic atoms. It also groups bonds based
    either on crystal symmetry or bond length (with `tol_dist`  tolerance) is space group is not defined.
    Sorting bonds based on length can be forced by setting the `forceNoSym` parameter to true.

    :param phaseObj: easyCore phase object for which you want the bonds to be found
    :type phaseObj: Phase
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
    hMax1 = 1 / np.sqrt(np.sum(np.linalg.inv(phaseObj.cell.matrix.T) ** 2, axis=0))
    # calculate the distance of the[1 1 1] point from the origin
    hMax2 = np.abs(np.sum(phaseObj.cell.matrix, axis=0))

    # calculate the closest point to the origin
    hMax = np.min(np.array([hMax1, hMax2]), axis=0)

    # gives the number of extra unit cells along all 3 axes that are necessary to cover the minimum bond distance
    nC = np.ceil(max_distance / hMax)

    all_atoms = phaseObj.get_orbits(magnetic_only=magnetic_only)
    all_atoms_r = np.vstack([np.array(all_atoms[key]) for key in all_atoms.keys()])
    nAtoms = all_atoms_r.shape[0]

    cDim = np.array([nC[0] + 1, 2 * nC[1] + 1, 2 * nC[2] + 1])
    nHalfCube = np.prod(cDim)

    # generate all cell translations
    cTr1, cTr2, cTr3 = np.mgrid[0:nC[0] + 1, -nC[1]:nC[1] + 1, -nC[2]:nC[2] + 1]
    # cell origin translations: Na x Nb x Nc x 1 x 1 x3
    cTr = np.stack([cTr1, cTr2, cTr3], axis=3).reshape((*cTr1.shape, 1, 1, 3))
    # remove unit cells that would produce duplicate bonds mark them with NaN (enough to do along a-axis values)
    cTr[0, :, np.array(range(int(cDim[2]))) < int(nC[2]), 0, 0, 0] = np.nan
    cTr[0, np.array(range(int(cDim[1]))) < int(nC[1]), int(nC[2]), 0, 0, 0] = np.nan
    # % positions of atoms in the half 'cube' in l.u.
    # % Na x Nb x Nc x 1 x nMagAtom x 3
    # % atom2
    r1 = all_atoms_r.reshape((1, 1, 1, 1, -1, 3))
    r2 = all_atoms_r.reshape((1, 1, 1, -1, 1, 3))
    aPos = r1 + cTr
    # generate all distances from the atoms in the (0,0,0) cell in l.u.
    # r(atom2) - r(atom1)
    # Na x Nb x Nc x nMagAtom x nMagAtom x 3
    dR = aPos - r2
    # mark duplicate bonds within the (0,0,0) cell with nan
    R0 = dR[0, int(nC[1]), int(nC[2]), :, :, :]
    dR[0, int(nC[1]), int(nC[2]), :, :, :] = R0 * (
            1 + np.tril(np.nan * np.ones((nAtoms, nAtoms))).reshape((nAtoms, nAtoms, 1)))
    # calculate the absolute value of the distances in Angstrom
    dRA = np.sqrt(np.sum(np.einsum('abcdei,ij->abcdej', dR, phaseObj.cell.matrix) ** 2, axis=5))
    # reshape the numbers into a column list of bonds
    # 3 x Na x Nb x Nc x nMagAtom x nMagAtom
    dl = np.transpose(np.tile(cTr, [1, 1, 1, nAtoms, nAtoms, 1]), axes=[5, 0, 1, 2, 3, 4])
    atoms1 = np.tile(np.arange(nAtoms).reshape((1, 1, 1, 1, -1, 1)), [1, *[int(d) for d in cDim], 1, nAtoms])
    atoms2 = np.tile(np.arange(nAtoms).reshape((1, 1, 1, 1, 1, -1)), [1, *[int(d) for d in cDim], nAtoms, 1])
    dRA = dRA.reshape((1, *dRA.shape))
    # store everything in a single matrix
    # cMat  = [dl(:,:);atom1(1,:);atom2(1,:);dRA(1,:)];
    dl_ = dl.reshape((3, -1), order='F')
    atom1_ = atoms1.reshape((1, -1), order='F')
    atom2_ = atoms2.reshape((1, -1), order='F')
    dRA_ = dRA.reshape((1, -1), order='F')

    cMat = np.vstack((dl_, atom1_, atom2_, dRA_))
    # remove nan bonds
    cMat = cMat[:, ~np.isnan(cMat[0, :])]
    # sort according to distance
    s_index = np.argsort(cMat[5, :])
    cMat = cMat[:, s_index]
    # Apply cutoff
    c_index = cMat[5, :] <= max_distance
    cMat = cMat[:, c_index]
    cIdx = np.cumsum(np.array(np.insert(np.diff(cMat[5, :]) > tol_dist, 0, True), dtype=int)) - 1
    cMat = np.vstack((cMat, cIdx))

    if cMat[5, 0] < d_min:
        raise ArithmeticError(f'Some atoms are too close (d_min={cMat[5, 0]} < {d_min}), check your crystal structure!')

    dRA = cMat[5, :]
    cMat = cMat[[0, 1, 2, 3, 4, 6], :]
    basisvector = phaseObj.cell.matrix
    symm_opps = phaseObj.spacegroup.symmetry_opts
    if not force_no_sym:
        nMat = []
        if max_sym is None:
            max_sym = np.inf
        maxidxSym = max(cIdx[cIdx <= max_sym])
        ii = 0
        idx = 0
        while ii <= maxidxSym:
            sortMs = cMat[:, cIdx == ii]
            while sortMs.shape[1] > 0:
                genC, unC = bond(all_atoms_r, basisvector, sortMs[:, 0], symm_opps, tol)
                genCAll = np.hstack((genC, np.vstack((-genC[0:3, :], genC[[4, 3], :]))))
                # remove from sortMs the identical couplings
                iNew, _ = isnew(genCAll, sortMs[0:5, :], tol)
                sortMs = sortMs[:, iNew]
                # Remove identical couplings from the symmetry generated list
                genC = genC[:, unC]
                if np.sum(~iNew) != np.sum(unC):
                    raise ArithmeticError(f'Symmetry error! ii={ii}, idx={idx}. Try to change ''tol'' parameter.')
                nMat.append(np.vstack((genC, np.ones((1, genC.shape[1])) * idx)))
                idx += 1
            ii += 1
        nMat = np.hstack(nMat)
        # include the increase of bond index in case bonds are split due to symmetry inequivalency
        cMat = cMat[:, cMat[5, :] > maxidxSym]
        cMat[5, :] = cMat[5, :] + nMat[5, -1] - maxidxSym
        cMat = np.hstack((nMat, cMat))

        # Save the value of maximum bond index that is generated by symmetry
        nSym = nMat[5, -1] + 1
    else:
        nSym = 0

    return Bonding(cMat[0:3, :].astype(int),
                   cMat[3, :].astype(int),
                   cMat[4, :].astype(int),
                   cMat[5, :].astype(int),
                   nSym)


def bond(r: np.ndarray, bv: np.ndarray, bond: np.ndarray,
         symOp: List[SymmOp], tol: float = 1e-5) -> Tuple[np.ndarray, Union[np.ndarray, np.ndarray]]:
    """
    generates all bonds that are symmetry equivalent to the given `bond`. The function uses the given space group
    operators and positions of magnetic atoms to return a list of equivalent bonds in a matrix. The function also checks
     the validity of the calculation by measuring the length of each equivalent bond using the given `bv` base and if
     the difference in length between equivalent bonds is larger than the tolerance throws a warning.

    :param r: Positions of the magnetic atoms in lattice units stored in a matrix
    :type r: np.ndarray
    :param bv: Basis vectors that define the lattice, used for checking the bond length of equivalent bonds
    :type bv: np.ndarray
    :param bond: Vector that contains the starting bond with elements of `[dl_a dl_b dl_c atom_1 atom_2]`, where `dl`
    is vector of lattice translation between the two atoms if they are not in the same unit cell in lattice units,
    `atom_1` and `atom_2` are indices of atoms in the list of positions stored in `r`.
    :type bond: np.ndarray
    :param symOp: List of symmetry operations for the given spacegroup
    :type symOp: list
    :param tol: Tolerance
    :type tol: float
    :return:
    :rtype:
    """
    tolDist = 1e-5

    r1 = r[int(bond[3]), :].T
    r2 = r[int(bond[4]), :].T
    dl = bond[[0, 1, 2]]

    # Generate new atomic positions and translation vectors
    r1new = np.array([s.operate(r1) for s in symOp]).T
    r2new = np.array([s.operate(r2) for s in symOp]).T
    dlnew = np.array([s.apply_rotation_only(dl) for s in symOp]).T - cfloor(r1new, tol) + cfloor(r2new, tol)

    # Modulo to get atoms in the first unit cell
    r1new = np.mod(r1new, 1)
    r2new = np.mod(r2new, 1)

    # Throw away generated couplings with wrong distance
    iNew, atom1 = isnewUC(r.T, r1new, tolDist)
    if np.any(iNew):
        raise ArithmeticError('The generated positions for atom1 are wrong!')
    iNew, atom2 = isnewUC(r.T, r2new, tolDist)
    if np.any(iNew):
        raise ArithmeticError('The generated positions for atom2 are wrong!')
    dist = np.sqrt(np.sum(np.dot(bv.T, (r.T[:, atom2] - r.T[:, atom1] + dlnew)) ** 2, axis=0))
    rightDist = np.abs(dist - dist[0]) < tol
    if not np.all(rightDist):
        # TODO This should raise a warning
        print('Symmetry generated couplings are dropped!')
    genCp = np.vstack((dlnew, atom1.reshape((1, -1)), atom2.reshape((1, -1))))
    genCp = genCp[:, rightDist]
    ugenCp = uniqueB(genCp)

    return genCp, ugenCp


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


def isnewUC(A: np.ndarray, B: np.ndarray, tol: float) -> Tuple[
    Union[np.ndarray, bool], Union[np.ndarray, int, float, complex]]:
    """
    Selects the new vectors from B within the first unit cell.

    Dimensions of A and B have to be [3 nA] and [3 nB] respectively. A vector in B is considered new,
    if d(mod(vA-vB,1))<tol.

    :param A: First matrix
    :type A: np.ndarray
    :param B: Second matrix
    :type B: np.ndarray
    :param tol: Tolerance
    :type tol: float
    :return: Logical numpy array saying of the vector is new and a numpy array with the index
    :rtype: Tuple[np.ndarray, np.ndarray]
    """

    nA = A.shape[1]
    nB = B.shape[1]

    C = A.shape[0]
    if C is not B.shape[0]:
        raise AttributeError

    aa = np.tile(A.reshape((*A.shape, 1)).transpose((1, 2, 0)), (1, nB, 1))
    bb = np.tile(B.reshape((*B.shape, 1)).transpose((2, 1, 0)), (nA, 1, 1))
    notequal = np.sum(cmod(aa - bb, tol) ** 2, axis=2) > tol

    is_new = np.all(notequal, axis=0)
    idx = np.arange(nB)
    symIdx = np.max(np.array(~notequal[:, idx[~is_new]], dtype=int) * np.arange(nA).reshape((-1, 1)), axis=0)

    return is_new, symIdx


def isnew(A: np.ndarray, B: np.ndarray, tol: float) -> Tuple[
    Union[np.ndarray, bool], Union[np.ndarray, int, float, complex]]:
    """
    Selects the new vectors from B within the first unit cell.

    Dimensions of A and B have to be [3 nA] and [3 nB] respectively. A vector in B is considered new,
    if d(mod(vA-vB,1))<tol.

    :param A: First matrix
    :type A: np.ndarray
    :param B: Second matrix
    :type B: np.ndarray
    :param tol: Tolerance
    :type tol: float
    :return: Logical numpy array saying of the vector is new and a numpy array with the index
    :rtype: Tuple[np.ndarray, np.ndarray]
    """

    if not A.shape[0] == B.shape[0]:
        raise AttributeError

    aa = np.tile(A.reshape((*A.shape, 1)).transpose((1, 2, 0)), (1, B.shape[1], 1))
    bb = np.tile(B.reshape((*B.shape, 1)).transpose((2, 1, 0)), (A.shape[1], 1, 1))
    notequal = np.sum(np.abs(aa - bb) ** 2, axis=2) > tol

    isnew = np.all(notequal, axis=0)
    idx = np.arange(B.shape[1])
    symF = lambda this_idx: np.where(~notequal[:, this_idx])[0][0]
    symIdx = np.array([symF(this_idx) for this_idx in idx[~isnew]])
    return isnew, symIdx


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


def uniqueB(bond: np.ndarray) -> Union[np.ndarray, bool]:
    """
    Given an array of bonds, which ones are unique. Bonds has the shape [dl, atom1, atom2]

    :param bond: Array of bonds
    :type bond: np.ndarray
    :return: Logical array for if the corresponding bond is unique
    :rtype: np.ndarray
    """
    nC = bond.shape[1]
    c1 = bond.reshape((*bond.shape, 1)).transpose((1, 2, 0))
    c2 = bond.reshape((*bond.shape, 1)).transpose((2, 1, 0))
    nc1 = np.vstack((-bond[0:3, :], bond[[4, 3], :])).reshape((5, -1, 1)).transpose((1, 2, 0))

    uniqueb = np.all(np.triu(np.any(np.not_equal(c1, c2), axis=2) &
                             np.any(np.not_equal(nc1, c2), axis=2)) |
                     np.tril(np.ones(nC, dtype=bool)), axis=0)
    return uniqueb
