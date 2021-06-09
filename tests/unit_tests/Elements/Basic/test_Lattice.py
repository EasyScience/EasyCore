__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

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


def make_dict(value) -> dict:
    return {
        '@module': 'easyCore.Elements.Basic.Lattice',
        '@class': 'Lattice',
        '@version': '0.1.0',
        'length_a': {
            '@module': 'easyCore.Objects.Base',
            '@class': 'Parameter',
            '@version': '0.1.0',
            'name': 'length_a',
            'value': float(value[0]),
            'error': 0.0,
            'min': 0,
            'max': np.inf,
            'fixed': True,
            'description': 'Unit-cell length of the selected structure in angstroms.',
            'url': 'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_length_.html',
            'units': 'angstrom',
            '@id': '149027786693506016496254445195239597714',
            'enabled': True
        },
        'length_b': {
            '@module': 'easyCore.Objects.Base',
            '@class': 'Parameter',
            '@version': '0.1.0',
            'name': 'length_b',
            'value': float(value[1]),
            'error': 0.0,
            'min': 0,
            'max': np.inf,
            'fixed': True,
            'description': 'Unit-cell length of the selected structure in angstroms.',
            'url': 'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_length_.html',
            'units': 'angstrom',
            '@id': '294836968667493729920294930317191977696',
            'enabled': True
        },
        'length_c': {
            '@module': 'easyCore.Objects.Base',
            '@class': 'Parameter',
            '@version': '0.1.0',
            'name': 'length_c',
            'value': float(value[2]),
            'error': 0.0,
            'min': 0,
            'max': np.inf,
            'fixed': True,
            'description': 'Unit-cell length of the selected structure in angstroms.',
            'url': 'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_length_.html',
            'units': 'angstrom',
            '@id': '275642519607899521714432039990092728990',
            'enabled': True
        },
        'angle_alpha': {
            '@module': 'easyCore.Objects.Base',
            '@class': 'Parameter',
            '@version': '0.1.0',
            'name': 'angle_alpha',
            'value': float(value[3]),
            'error': 0.0,
            'min': 0,
            'max': np.inf,
            'fixed': True,
            'description': 'Unit-cell angle of the selected structure in degrees.',
            'url': 'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_angle_.html',
            'units': 'degree',
            '@id': '161899496656810433045540450883723049023',
            'enabled': True
        },
        'angle_beta': {
            '@module': 'easyCore.Objects.Base',
            '@class': 'Parameter',
            '@version': '0.1.0',
            'name': 'angle_beta',
            'value': float(value[4]),
            'error': 0.0,
            'min': 0,
            'max': np.inf,
            'fixed': True,
            'description': 'Unit-cell angle of the selected structure in degrees.',
            'url': 'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_angle_.html',
            'units': 'degree',
            '@id': '186637124621565458307862080073460500737',
            'enabled': True
        },
        'angle_gamma': {
            '@module': 'easyCore.Objects.Base',
            '@class': 'Parameter',
            '@version': '0.1.0',
            'name': 'angle_gamma',
            'value': float(value[5]),
            'error': 0.0,
            'min': 0,
            'max': np.inf,
            'fixed': True,
            'description': 'Unit-cell angle of the selected structure in degrees.',
            'url': 'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_angle_.html',
            'units': 'degree',
            '@id': '225244117838730303286513043607480352526',
            'enabled': True
        },
        'interface': None,
        '@id': '78109834334085432621980127205750673524'
    }


@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_as_dict(value: list):
    l = Lattice.from_pars(*value)
    obtained = l.as_dict()
    expected = make_dict(value)

    def check_dict(check, item):
        if isinstance(check, dict) and isinstance(item, dict):
            for this_check_key in check.keys():
                if this_check_key == '@id':
                    continue
                check_dict(check[this_check_key], item[this_check_key])
        else:
            assert isinstance(item, type(check))
            assert item == check

    check_dict(expected, obtained)


@pytest.mark.parametrize('value', basic_pars)
def test_Lattice_from_dict(value: list):

    expected = make_dict(value)
    l = Lattice.from_dict(expected)
    obtained = l.as_dict()

    def check_dict(check, item):
        if isinstance(check, dict) and isinstance(item, dict):
            for this_check_key in check.keys():
                if this_check_key == '@id':
                    continue
                check_dict(check[this_check_key], item[this_check_key])
        else:
            assert isinstance(item, type(check))
            assert item == check

    check_dict(expected, obtained)


@pytest.mark.parametrize('value', basic_pars)
@pytest.mark.parametrize('fmt', ['.3f'])
@pytest.mark.parametrize('opt', ['m', 'l', 't'])
def test_Lattice_fmt(value, fmt, opt):

    l = Lattice.from_pars(*value)
    out_fmt = '{}{}'.format(fmt, opt)

    def do_test(in_str):
        m = (l.lengths, l.angles)
        if opt == 'm':
            m = l.matrix.tolist()
            fmt2 = "[[{}, {}, {}], [{}, {}, {}], [{}, {}, {}]]"
        elif opt == 'l':
            fmt2 = "{{{}, {}, {}, {}, {}, {}}}"
        else:
            fmt2 = "({} {} {}), ({} {} {})"
        check_str = fmt2.format(*[format(c, fmt) for row in m for c in row])
        assert in_str == check_str
    # Ancient Python. We won't be supporting this
    with pytest.raises(TypeError):
        out_fmt2 = '%' + out_fmt
        out_str = out_fmt2 % l
        do_test(out_str)
    # Python >2.7 "{:03fm}".format(l)
    out_fmt2 = '{:' + f'{out_fmt}' + '}'
    out_str = out_fmt2.format(l)
    do_test(out_str)
    # Python >3.6 + f"{l:03fm}"
    # This is stupidly dangerous.
    # Releases dragons, orks and is where darkness lies. You've been warned
    # !!!! DO NOT USE OUT OF THIS UNIQUE CONTEXT !!!!

    def effify(non_f_str: str, l: Lattice) ->str:
        return eval(f'f"""{non_f_str}"""')

    out_str = effify(f'{{l:{out_fmt}}}', l)
    do_test(out_str)


@pytest.mark.parametrize('value', basic_pars)
def test_lattice_copy(value):
    from copy import copy

    l1 = Lattice.from_pars(*value)
    l2 = copy(l1)

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for item in items:
        f1 = getattr(l1, item)
        f2 = getattr(l2, item)
        assert np.isclose(f1.raw_value, f2.raw_value)
        assert f1 != f2


@pytest.mark.parametrize('value', basic_pars)
def test_lattice_to_star(value):
    l = Lattice.from_pars(*value)
    star = l.to_star()

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    for item in items:
        assert item in star.labels
    assert star.data[0] == l


@pytest.mark.parametrize('value', basic_pars)
def test_lattice_from_star(value):
    l1 = Lattice.from_pars(*value)
    star_string = str(l1.to_star())
    l2 = Lattice.from_star(star_string)

    items = ['length_a', 'length_b', 'length_c',
             'angle_alpha', 'angle_beta', 'angle_gamma']

    assert l1 != l2

    for item in items:
        f1 = getattr(l1, item)
        f2 = getattr(l2, item)
        assert np.isclose(f1.raw_value, f2.raw_value)
        assert f1 != f2
