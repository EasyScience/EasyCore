__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import pytest
from easyCore import np
from numbers import Number
from easyCore.Elements.Basic.Lattice import Lattice, Parameter, CELL_DETAILS

pars_dict = {
    'cubic':        (5, 5, 5, 90, 90, 90),
    'tetragonal':   (10, 10, 5, 90, 90, 90),
    'orthorhombic': (2, 3, 4, 90, 90, 90),
    'monoclinic':   (2, 3, 4, 90, 99, 90),
    'hexagonal':    (3, 3, 4, 90, 90, 120),
    'rhombohedral': (4, 4, 4, 99, 99, 99)
}


def mod_pars(in_mods=None, sep=False) -> tuple:
    items = []
    keys = pars_dict.keys()
    if in_mods is None:
        in_mods = [[]] * len(keys)
    for key, mod_ in zip(keys, in_mods):
        if mod_:
            if sep:
                items.append(pytest.param(pars_dict[key], mod_, id=key))
            else:
                items.append(pytest.param((*pars_dict[key], mod_), id=key))
        else:
            items.append(pytest.param(pars_dict[key], id=key))
    return tuple(items)


basic_pars = mod_pars()

matrix_pars = mod_pars([[[5.000000e+00, 0.000000e+00, 3.061617e-16],
                         [-3.061617e-16, 5.000000e+00, 3.061617e-16],
                         [0.000000e+00, 0.000000e+00, 5.000000e+00]],
                        [[1.000000e+01, 0.000000e+00, 6.123234e-16],
                         [-6.123234e-16, 1.000000e+01, 6.123234e-16],
                         [0.000000e+00, 0.000000e+00, 5.000000e+00]],
                        [[2.0000000e+00, 0.0000000e+00, 1.2246468e-16],
                         [-1.8369702e-16, 3.0000000e+00, 1.8369702e-16],
                         [0.0000000e+00, 0.0000000e+00, 4.0000000e+00]],
                        [[1.97537668e+00, 0.00000000e+00, -3.12868930e-01],
                         [-1.83697020e-16, 3.00000000e+00, 1.83697020e-16],
                         [0.00000000e+00, 0.00000000e+00, 4.00000000e+00]],
                        [[3.00000000e+00, 0.00000000e+00, 1.83697020e-16],
                         [-1.50000000e+00, 2.59807621e+00, 1.83697020e-16],
                         [0.00000000e+00, 0.00000000e+00, 4.00000000e+00]],
                        [[3.95075336, 0., -0.62573786],
                         [-0.7326449, 3.88222663, -0.62573786],
                         [0., 0., 4.]]
                        ])


def test_Lattice_default():
    lattice = Lattice.default()

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for key in items:
        item: Parameter = getattr(lattice, key)
        assert item.name == key
        t = key.split('_')[0]
        test_defaults = CELL_DETAILS[t].copy()
        test_defaults['raw_value'] = test_defaults['value']
        del test_defaults['value']
        test_defaults['unit'] = test_defaults['units']
        del test_defaults['units']
        for default in test_defaults.keys():
            r = test_defaults[default]
            i = getattr(item, default)
            if default == 'unit':
                i = str(i)[0:3]
                r = r[0:3]
            assert i == r


@pytest.mark.parametrize('ang_unit', ('deg', 'rad'))
@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_from_pars(value: list, ang_unit: str):
    ref = [v for v in value]

    if ang_unit == 'rad':
        value = [value[0], value[1], value[2],
                 np.deg2rad(value[3]), np.deg2rad(value[4]), np.deg2rad(value[5])]

    l = Lattice.from_pars(*value, ang_unit=ang_unit)

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for idx, key in enumerate(items):
        item: Parameter = getattr(l, key)
        assert item.name == key
        t = key.split('_')[0]
        test_defaults = CELL_DETAILS[t].copy()
        test_defaults['raw_value'] = ref[idx]
        del test_defaults['value']
        test_defaults['unit'] = test_defaults['units']
        del test_defaults['units']
        for default in test_defaults.keys():
            r = test_defaults[default]
            i = getattr(item, default)
            if default == 'unit':
                i = str(i)[0:3]
                r = r[0:3]
            if isinstance(i, Number) and not isinstance(i, bool):
                assert r == pytest.approx(i)
            else:
                assert i == r


@pytest.mark.parametrize('value', matrix_pars)
def test_Lattice_from_matrix(value):
    args = value[0:-1]
    matrix = value[-1]
    l = Lattice.from_matrix(matrix)
    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']
    for idx, key in enumerate(items):
        item: Parameter = getattr(l, key)
        assert item.name == key
        t = key.split('_')[0]
        test_defaults = CELL_DETAILS[t].copy()
        test_defaults['raw_value'] = args[idx]
        del test_defaults['value']
        test_defaults['unit'] = test_defaults['units']
        del test_defaults['units']
        for default in test_defaults.keys():
            r = test_defaults[default]
            i = getattr(item, default)
            if default == 'unit':
                i = str(i)[0:3]
                r = r[0:3]
            if isinstance(i, Number) and not isinstance(i, bool):
                assert r == pytest.approx(i)
            else:
                assert i == r


@pytest.mark.parametrize('value', mod_pars([[0], [0, 2], [0, 1, 2], [0, 1, 2, 4], [0, 2], [0, 3]]))
def test_Lattice_from_special(request, value):
    ref = np.array(value[0:6])
    cons = ref[value[6:]]
    lattice_type = request.node.name.split('[')[1][:-1]

    f = getattr(Lattice, lattice_type)
    l = f(*cons)

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for idx, key in enumerate(items):
        item: Parameter = getattr(l, key)
        assert item.name == key
        t = key.split('_')[0]
        test_defaults = CELL_DETAILS[t].copy()
        test_defaults['raw_value'] = ref[idx]
        del test_defaults['value']
        test_defaults['unit'] = test_defaults['units']
        del test_defaults['units']
        for default in test_defaults.keys():
            r = test_defaults[default]
            i = getattr(item, default)
            if default == 'unit':
                i = str(i)[0:3]
                r = r[0:3]
            if isinstance(i, Number) and not isinstance(i, bool):
                assert r == pytest.approx(i)
            else:
                assert i == r


@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_pars_short_GET(value: list):
    l = Lattice.from_pars(*value)

    items = ['a', 'b', 'c',
             'alpha', 'beta', 'gamma']

    for idx, item in enumerate(items):
        f = getattr(l, item)
        assert f == value[idx]


@pytest.mark.parametrize('in_value, new_value', mod_pars([(6, 6, 6, 90, 90, 90),
                                                          (11, 11, 6, 90, 90, 90),
                                                          (5, 6, 7, 90, 90, 90),
                                                          (6, 7, 8, 90, 95, 90),
                                                          (4, 4, 5, 90, 90, 120),
                                                          (6, 6, 6, 95, 95, 95)], True))
def test_Lattice_pars_short_SET(in_value: list, new_value: list):
    l = Lattice.from_pars(*in_value)

    items = ['a', 'b', 'c',
             'alpha', 'beta', 'gamma']

    for idx, item in enumerate(items):
        f = getattr(l, item)
        assert f == in_value[idx]
        setattr(l, item, new_value[idx])
        f = getattr(l, item)
        assert f == new_value[idx]


@pytest.mark.parametrize('in_value, new_value', mod_pars([(6, 6, 6, 90, 90, 90),
                                                          (11, 11, 6, 90, 90, 90),
                                                          (5, 6, 7, 90, 90, 90),
                                                          (6, 7, 8, 90, 95, 90),
                                                          (4, 4, 5, 90, 90, 120),
                                                          (6, 6, 6, 95, 95, 95)], True))
def test_Lattice_pars_SET(in_value: list, new_value: list):
    l = Lattice.from_pars(*in_value)

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for idx, item in enumerate(items):
        f = getattr(l, item)
        assert f.raw_value == in_value[idx]
        setattr(l, item, new_value[idx])
        f = getattr(l, item)
        assert f.raw_value == new_value[idx]


@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_angles(value: list):
    l = Lattice.from_pars(*value)
    assert np.all(np.array(value[3:]) == l.angles)


@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_lengths(value: list):
    l = Lattice.from_pars(*value)
    assert np.all(np.array(value[0:3]) == l.lengths)


@pytest.mark.parametrize('value', matrix_pars)
def test_Lattice_matrix(value: list):
    args = value[0:-1]
    matrix = np.array(value[-1])

    l = Lattice.from_pars(*args)
    assert np.all(np.isclose(matrix, l.matrix))


@pytest.mark.parametrize('value', matrix_pars)
def test_Lattice_inv_matrix(value: list):
    args = value[0:-1]
    matrix = np.array(value[-1])
    matrix = np.linalg.inv(matrix)

    l = Lattice.from_pars(*args)
    assert np.all(np.isclose(matrix, l.inv_matrix))


@pytest.mark.parametrize('value', mod_pars([125.0, 500.0, 24.0,
                                            23.704520174283306, 31.1769145362398, 61.35087958926781]))
def test_Lattice_volume(value):
    args = value[:-1]
    volume = value[-1]

    l = Lattice.from_pars(*args)
    assert volume == pytest.approx(l.volume.m)
    assert str(l.volume.units) == 'angstrom ** 3'


@pytest.mark.parametrize('value', matrix_pars)
def test_Lattice_metric_tensor(value):
    args = value[0:-1]

    matrix = np.array(value[-1])
    matrix = np.dot(matrix, matrix.T)

    l = Lattice.from_pars(*args)
    assert np.all(np.isclose(matrix, l.metric_tensor))


@pytest.mark.parametrize('in_value, new_value', mod_pars([(1.256637, 1.256637, 1.256637, 90, 90, 90),
                                                          (0.6283185, 0.6283185, 1.256637, 90, 90, 90),
                                                          (3.14159, 2.09439510, 1.5707963, 90, 90, 90),
                                                          (3.180753, 2.0943951, 1.5903765, 90, 81, 90),
                                                          (2.418399, 2.418399, 1.570796, 90, 90, 60),
                                                          (1.61845, 1.61845, 1.61845, 79.31296, 79.31296, 79.31296)],
                                                         True))
def test_Lattice_reciprocal_lattice(in_value: list, new_value: list):
    l = Lattice.from_pars(*in_value)
    obj = l.reciprocal_lattice

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for idx, item in enumerate(items):
        f = getattr(obj, item)
        assert np.isclose(f.raw_value, new_value[idx])


@pytest.mark.parametrize('in_value, new_value', mod_pars([(0.2, 0.2, 0.2, 90, 90, 90),
                                                          (0.1, 0.1, 0.2, 90, 90, 90),
                                                          (0.5, 1 / 3, 0.25, 90, 90, 90),
                                                          (0.5062325, 1 / 3, 0.253116, 90, 81, 90),
                                                          (0.3849, 0.3849, 0.25, 90, 90, 60),
                                                          (0.257584, 0.257584, 0.257584, 79.31296, 79.31296, 79.31296)],
                                                         True))
def test_Lattice_reciprocal_lattice(in_value: list, new_value: list):
    l = Lattice.from_pars(*in_value)
    obj = l.reciprocal_lattice_crystallographic

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for idx, item in enumerate(items):
        f = getattr(obj, item)
        assert np.isclose(f.raw_value, new_value[idx])


@pytest.mark.parametrize('scale', [0.1, 2, 3.14, 100])
@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_scale(value: list, scale: float):
    l = Lattice.from_pars(*value)

    new_volume = scale * l.volume
    scaled = l.scale(new_volume)

    assert np.isclose(scaled.volume, new_volume)
    assert np.all(np.isclose(l.angles, scaled.angles))


@pytest.mark.parametrize('scale', [0.1, 2, 3.14, 100,
                                   [0.5, 0.5, 1],
                                   [0.5, 1, 0.5],
                                   [1, 0.5, 0.5]])
@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_length_scale(value: list, scale: float):
    l = Lattice.from_pars(*value)

    scaled = l.scale_lengths(scale)
    assert np.all(np.isclose(l.angles, scaled.angles))
    assert np.all(np.isclose(np.array(l.lengths) * scale, scaled.lengths))


@pytest.mark.parametrize('co_ords', [[0.1, 2, 3.14],
                                     [0.5, 0.5, 1],
                                     [0.5, 1, 0.5],
                                     [1, 0.5, 0.5]])
@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_fract_cart_coords(value: list, co_ords: list):
    l = Lattice.from_pars(*value)

    frac = l.get_fractional_coords(co_ords)
    cart_co_ords = l.get_cartesian_coords(frac)

    assert np.all(np.isclose(co_ords, cart_co_ords))


@pytest.mark.parametrize('crystal_system', ['cubic', 'tetragonal', 'orthorhombic'])
def test_Lattice_is_orthogonal(crystal_system):

    l = Lattice.from_pars(*pars_dict[crystal_system])
    assert l.is_orthogonal()


def test_Lattice_is_hexagonal():

    lengths = np.array(pars_dict['hexagonal'][0:3])
    angles = np.array(pars_dict['hexagonal'][3:])

    l = Lattice.from_pars(*lengths, *angles)
    assert l.is_hexagonal()

    l = Lattice.from_pars(*lengths, *(angles + 1E-5))
    assert l.is_hexagonal(hex_angle_tol=1E-4)
    assert not l.is_hexagonal(hex_angle_tol=1E-6)

    l = Lattice.from_pars(*(lengths + [1E-2, -1E-2, 1E-2]), *angles)
    assert l.is_hexagonal(hex_length_tol=1E-1)
    assert not l.is_hexagonal(hex_length_tol=1E-7)


@pytest.mark.parametrize('values, out_str', mod_pars([
    '<Lattice: (a: 5.00 Å, b: 5.00 Å, c: 5.00Å, alpha: 90.00 deg, beta: 90.00 deg, gamma: 90.00 deg>',
    '<Lattice: (a: 10.00 Å, b: 10.00 Å, c: 5.00Å, alpha: 90.00 deg, beta: 90.00 deg, gamma: 90.00 deg>',
    '<Lattice: (a: 2.00 Å, b: 3.00 Å, c: 4.00Å, alpha: 90.00 deg, beta: 90.00 deg, gamma: 90.00 deg>',
    '<Lattice: (a: 2.00 Å, b: 3.00 Å, c: 4.00Å, alpha: 90.00 deg, beta: 99.00 deg, gamma: 90.00 deg>',
    '<Lattice: (a: 3.00 Å, b: 3.00 Å, c: 4.00Å, alpha: 90.00 deg, beta: 90.00 deg, gamma: 120.00 deg>',
    '<Lattice: (a: 4.00 Å, b: 4.00 Å, c: 4.00Å, alpha: 99.00 deg, beta: 99.00 deg, gamma: 99.00 deg>'
], True))
def test_Lattice_repr(values, out_str):
    l = Lattice.from_pars(*values)
    assert str(l) == out_str
