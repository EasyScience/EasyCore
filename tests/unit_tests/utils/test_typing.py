#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import pytest
from easyCore import np
from easyCore.Objects.ObjectClasses import BaseObjNew, Parameter
from easyCore.Utils.typing import noneType, Vector3Like, ClassVar


def test_noneType():
    assert isinstance(noneType, type)
    assert isinstance(None, noneType)


@pytest.mark.parametrize("value", [1, 1.1, np.array([1, 2, 3]), True, "boo"])
def test_NOT_noneType(value):
    assert not isinstance(value, noneType)


# @pytest.mark.parametrize("value", [[1, 2, 3], (1, 2, 3), np.array([1, 2, 3])])
# def test_Vector3Like(value):
#     assert isinstance(value, Vector3Like)


# @pytest.mark.parametrize("value", [1, 1.1, (1, 2), [1, 2], np.array([1, 2]), True, None, "boo"])
# def test_NOT_Vector3Like(value):
#     assert not isinstance(value, Vector3Like)


def test_ClassVar_replicate_builtin():
    class Foo:
        bar: ClassVar[np.linspace]
        dum: ClassVar[int] = 1
        rum: ClassVar[int]

        def __init__(self, bar, rum):
            arg = []
            kwarg = {}
            for item in bar:
                if isinstance(item, dict):
                    kwarg.update(item)
                else:
                    arg.append(item)
            self.bar = np.linspace(*arg, **kwarg)
            self.rum = rum

    # This should set 'bar' to a numpy array of size 100 with dtype float32
    # This should set 'foo' to a numpy array of size (5, 6, 2) (not call our fancy logic)
    # This should set 'dum' to 1, using usual logic
    # This should set 'rum' to 3, using usual logic AFTER initialization
    rum = 3
    f = Foo(bar=(0, 100, 101), rum=rum)
    assert isinstance(f.bar, np.ndarray)
    assert f.bar.shape == (101,)
    assert f.dum == 1
    assert f.rum == rum


def test_ClassVar_core():

    bar_name = "a"
    bar_value = 1.1
    bar_value_new = 2
    rum_value = 3

    class Foo(BaseObjNew):
        bar: ClassVar[Parameter, (bar_name, bar_value)]
        dum: ClassVar[int] = 1
        rum: ClassVar[int]

        def __init__(self, name, *args, **kwargs):

            rum = None
            if "rum" in kwargs.keys():
                rum = kwargs.pop("rum")
            super().__init__(name, *args, **kwargs)
            if rum is not None:
                self.rum = rum

    # This should set 'bar' to a numpy array of size 100 with dtype float32
    # This should set 'foo' to a numpy array of size (5, 6, 2) (not call our fancy logic)
    # This should set 'dum' to 1, using usual logic
    # This should set 'rum' to 3, using usual logic AFTER initialization
    f = Foo("foo", rum=rum_value)
    assert isinstance(f.bar, Parameter)
    assert f.bar.name == bar_name
    assert f.bar.raw_value == bar_value
    assert f.dum == 1
    assert f.rum == rum_value

    f.bar.value = bar_value_new
    assert f.bar.raw_value == bar_value_new
