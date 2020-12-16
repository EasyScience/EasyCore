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


def mod_pars(in_mods=None) -> tuple:
    items = []
    keys = pars_dict.keys()
    if in_mods is None:
        in_mods = [[]] * len(keys)
    for key, mod_ in zip(keys, in_mods):
        if mod_:
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
def test_lattice_pars_short_GET(value: list):
    l = Lattice.from_pars(*value)

    items = ['a', 'b', 'c',
             'alpha', 'beta', 'gamma']

    for idx, item in enumerate(items):
        f = getattr(l, item)
        assert f == value[idx]


@pytest.mark.parametrize('in_value, new_value', (
        pytest.param((5, 5, 5, 90, 90, 90), (6, 6, 6, 90, 90, 90), id='cubic'),
        pytest.param((10, 10, 5, 90, 90, 90), (11, 11, 6, 90, 90, 90), id='tetragonal'),
        pytest.param((2, 3, 4, 90, 90, 90), (5, 6, 7, 90, 90, 90), id='orthorhombic'),
        pytest.param((2, 3, 4, 90, 99, 90), (6, 7, 8, 90, 95, 90), id='monoclinic'),
        pytest.param((3, 3, 4, 90, 90, 120), (4, 4, 5, 90, 90, 120), id='hexagonal'),
        pytest.param((4, 4, 4, 99, 99, 99), (6, 6, 6, 95, 95, 95), id='rhombohedral')))
def test_lattice_pars_short_SET(in_value: list, new_value: list):
    l = Lattice.from_pars(*in_value)

    items = ['a', 'b', 'c',
             'alpha', 'beta', 'gamma']

    for idx, item in enumerate(items):
        f = getattr(l, item)
        assert f == in_value[idx]
        setattr(l, item, new_value[idx])
        f = getattr(l, item)
        assert f == new_value[idx]


@pytest.mark.parametrize('in_value, new_value', (
        pytest.param((5, 5, 5, 90, 90, 90), (6, 6, 6, 90, 90, 90), id='cubic'),
        pytest.param((10, 10, 5, 90, 90, 90), (11, 11, 6, 90, 90, 90), id='tetragonal'),
        pytest.param((2, 3, 4, 90, 90, 90), (5, 6, 7, 90, 90, 90), id='orthorhombic'),
        pytest.param((2, 3, 4, 90, 99, 90), (6, 7, 8, 90, 95, 90), id='monoclinic'),
        pytest.param((3, 3, 4, 90, 90, 120), (4, 4, 5, 90, 90, 120), id='hexagonal'),
        pytest.param((4, 4, 4, 99, 99, 99), (6, 6, 6, 95, 95, 95), id='rhombohedral')))
def test_lattice_pars_SET(in_value: list, new_value: list):
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
def test_lattice_angles(value: list):
    l = Lattice.from_pars(*value)
    assert np.all(np.array(value[3:]) == l.angles)


@pytest.mark.parametrize('value', basic_pars)
def test_lattice_lengths(value: list):
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
def test_lattice_volume(value):
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


# @pytest.mark.parametrize('value', matrix_pars)
# def test_Lattice_reciprocal_lattice(value):
#     args = value[0:-1]
#
#     matrix = np.array(value[-1])
#     matrix = np.linalg.inv(matrix).T
#
#     l = Lattice.from_pars(*args)
#     matrix2 = l.reciprocal_lattice.matrix
#     assert np.all(np.isclose(matrix2, 2 * np.pi * matrix))
#
#
# @pytest.mark.parametrize('value', matrix_pars)
# def test_Lattice_reciprocal_lattice_crystallographic(value):
#     args = value[0:-1]
#
#     matrix = np.array(value[-1])
#     matrix = np.linalg.inv(matrix).T
#
#     l = Lattice.from_pars(*args)
#     assert np.all(np.isclose(l.reciprocal_lattice_crystallographic.matrix, matrix))
