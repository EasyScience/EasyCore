#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import pytest
from easyCore import np
from easyCore.Objects.Base import Parameter, BaseObj
from easyCore.optimization.fitting import Fitter
from easyCore.optimization.constraints import ObjConstraint


class AbsSin(BaseObj):
    def __init__(self, offset: Parameter, phase: Parameter):
        super(AbsSin, self).__init__("sin", offset=offset, phase=phase)

    @classmethod
    def from_pars(cls, offset, phase):
        offset = Parameter("offset", offset)
        phase = Parameter("phase", phase)
        return cls(offset=offset, phase=phase)

    def __call__(self, x):
        return np.abs(np.sin(self.phase.raw_value * x + self.offset.raw_value))


@pytest.fixture
def genObjs():
    ref_sin = AbsSin.from_pars(0.2, np.pi)
    sp_sin = AbsSin.from_pars(0.354, 3.05)
    return ref_sin, sp_sin


@pytest.fixture
def genObjs2():
    ref_sin = AbsSin.from_pars(np.pi * 0.45, 0.45 * np.pi * 0.5)
    sp_sin = AbsSin.from_pars(1, 0.5)
    return ref_sin, sp_sin


def test_basic_fit(genObjs):
    ref_sin = genObjs[0]
    sp_sin = genObjs[1]

    x = np.linspace(0, 5, 200)
    y = ref_sin(x)

    sp_sin.offset.fixed = False
    sp_sin.phase.fixed = False

    f = Fitter(sp_sin, sp_sin)

    _ = f.fit(x, y)

    assert sp_sin.phase.raw_value == pytest.approx(ref_sin.phase.raw_value, rel=1e-3)
    assert sp_sin.offset.raw_value == pytest.approx(ref_sin.offset.raw_value, rel=1e-3)


@pytest.mark.parametrize("fit_engine", [None, "lmfit", "bumps", "DFO_LS"])
def test_basic_fit(genObjs, fit_engine):
    ref_sin = genObjs[0]
    sp_sin = genObjs[1]

    x = np.linspace(0, 5, 200)
    y = ref_sin(x)

    sp_sin.offset.fixed = False
    sp_sin.phase.fixed = False

    f = Fitter(sp_sin, sp_sin)
    if fit_engine is not None:
        f.switch_engine(fit_engine)
        if f.engine.name != fit_engine:
            # DFO_LS is not installed by default
            pytest.skip(msg=f"{fit_engine} is not installed")
    result = f.fit(x, y)

    if fit_engine is not None:
        assert result.fitting_engine.name == fit_engine
    assert sp_sin.phase.raw_value == pytest.approx(ref_sin.phase.raw_value, rel=1e-3)
    assert sp_sin.offset.raw_value == pytest.approx(ref_sin.offset.raw_value, rel=1e-3)


def check_fit_results(result, sp_sin, ref_sin, x, **kwargs):
    assert result.n_pars == len(sp_sin.get_fit_parameters())
    assert result.goodness_of_fit == pytest.approx(0, abs=1.5e-3)
    assert result.reduced_chi == pytest.approx(0, abs=1.5e-3)
    assert result.success
    if "sp_ref1" in kwargs.keys():
        sp_ref1 = kwargs["sp_ref1"]
        for key, value in sp_ref1.items():
            assert key in result.p.keys()
            assert key in result.p0.keys()
            assert result.p0[key] == pytest.approx(
                value
            )  # Bumps does something strange here
    assert np.all(result.x == x)
    for item1, item2 in zip(sp_sin._kwargs.values(), ref_sin._kwargs.values()):
        # assert item.error > 0 % This does not work as some methods don't calculate error
        assert item1.error == pytest.approx(0, abs=1e-1)
        assert item1.raw_value == pytest.approx(item2.raw_value, abs=2e-3)
    y_calc_ref = ref_sin(x)
    assert result.y_calc == pytest.approx(y_calc_ref, abs=1e-2)
    assert result.residual == pytest.approx(sp_sin(x) - y_calc_ref, abs=1e-2)


@pytest.mark.parametrize("fit_engine", [None, "lmfit", "bumps", "DFO_LS"])
def test_fit_result(genObjs, fit_engine):
    ref_sin = genObjs[0]
    sp_sin = genObjs[1]

    x = np.linspace(0, 5, 200)
    y = ref_sin(x)

    sp_sin.offset.fixed = False
    sp_sin.phase.fixed = False

    sp_ref1 = {
        f"p{sp_sin._borg.map.convert_id_to_key(item1)}": item1.raw_value
        for item1, item2 in zip(sp_sin._kwargs.values(), ref_sin._kwargs.values())
    }
    sp_ref2 = {
        f"p{sp_sin._borg.map.convert_id_to_key(item1)}": item2.raw_value
        for item1, item2 in zip(sp_sin._kwargs.values(), ref_sin._kwargs.values())
    }

    f = Fitter(sp_sin, sp_sin)

    if fit_engine is not None:
        f.switch_engine(fit_engine)
        if f.engine.name != fit_engine:
            # DFO_LS is not installed by default
            pytest.skip(msg=f"{fit_engine} is not installed")

    result = f.fit(x, y)
    check_fit_results(result, sp_sin, ref_sin, x, sp_ref1=sp_ref1, sp_ref2=sp_ref2)


@pytest.mark.parametrize("fit_method", ["leastsq", "powell", "cobyla"])
def test_lmfit_methods(genObjs, fit_method):
    ref_sin = genObjs[0]
    sp_sin = genObjs[1]

    x = np.linspace(0, 5, 200)
    y = ref_sin(x)

    sp_sin.offset.fixed = False
    sp_sin.phase.fixed = False

    f = Fitter(sp_sin, sp_sin)
    assert fit_method in f.available_methods()
    result = f.fit(x, y, method=fit_method)
    check_fit_results(result, sp_sin, ref_sin, x)


@pytest.mark.parametrize("fit_method", ["newton", "lm"])
def test_bumps_methods(genObjs, fit_method):
    ref_sin = genObjs[0]
    sp_sin = genObjs[1]

    x = np.linspace(0, 5, 200)
    y = ref_sin(x)

    sp_sin.offset.fixed = False
    sp_sin.phase.fixed = False

    f = Fitter(sp_sin, sp_sin)
    f.switch_engine("bumps")
    assert fit_method in f.available_methods()
    result = f.fit(x, y, method=fit_method)
    check_fit_results(result, sp_sin, ref_sin, x)


@pytest.mark.parametrize("fit_engine", ["lmfit", "bumps", "DFO_LS"])
def test_fit_constraints(genObjs2, fit_engine):
    ref_sin = genObjs2[0]
    sp_sin = genObjs2[1]

    x = np.linspace(0, 5, 200)
    y = ref_sin(x)

    sp_sin.phase.fixed = False

    f = Fitter(sp_sin, sp_sin)

    assert len(f.fit_constraints()) == 0
    c = ObjConstraint(sp_sin.offset, "2*", sp_sin.phase)
    f.add_fit_constraint(c)

    if fit_engine is not None:
        f.switch_engine(fit_engine)
        if f.engine.name != fit_engine:
            # DFO_LS is not installed by default
            pytest.skip(msg=f"{fit_engine} is not installed")

    result = f.fit(x, y)
    check_fit_results(result, sp_sin, ref_sin, x)
    assert len(f.fit_constraints()) == 1
    f.remove_fit_constraint(0)
    assert len(f.fit_constraints()) == 0


def test_fit_makeModel(genObjs):
    ref_sin = genObjs[0]
    sp_sin = genObjs[1]

    x = np.linspace(0, 5, 200)
    y = ref_sin(x)

    sp_sin.offset.fixed = False
    sp_sin.phase.fixed = False

    f = Fitter(sp_sin, sp_sin)
    model = f.make_model()
    result = f.fit(x, y, model=model)
    check_fit_results(result, sp_sin, ref_sin, x)
