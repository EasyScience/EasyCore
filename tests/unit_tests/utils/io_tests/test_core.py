__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from copy import deepcopy
from typing import Type

import pytest

import easyCore
from easyCore.Objects.ObjectClasses import BaseObj
from easyCore.Objects.ObjectClasses import Descriptor
from easyCore.Objects.ObjectClasses import Parameter

dp_param_dict = {
    "argnames": "dp_kwargs, dp_cls",
    "argvalues": (
        [
            {
                "@module": Descriptor.__module__,
                "@class": Descriptor.__name__,
                "@version": easyCore.__version__,
                "name": "test",
                "value": 1,
                "units": "dimensionless",
                "description": "",
                "url": "",
                "display_name": "test",
                "enabled": True,
            },
            Descriptor,
        ],
        [
            {
                "@module": Parameter.__module__,
                "@class": Parameter.__name__,
                "@version": easyCore.__version__,
                "name": "test",
                "units": "kilometer",
                "value": 1.0,
                "error": 0.0,
                "min": -easyCore.np.inf,
                "max": easyCore.np.inf,
                "fixed": False,
                "url": "https://www.boo.com",
                "description": "",
                "display_name": "test",
                "enabled": True,
            },
            Parameter,
        ],
    ),
    "ids": ["Descriptor", "Parameter"],
}

_skip_opt = [[], None] + [
    k for k in dp_param_dict["argvalues"][0][0].keys() if k[0] != "@"
]
skip_dict = {
    "argnames": "skip",
    "argvalues": _skip_opt,
    "ids": ["skip_" + str(opt) for opt in _skip_opt],
}


def check_dict(check, item):
    if isinstance(check, dict) and isinstance(item, dict):
        for key in check.keys():
            if key == "@id":
                continue
            assert key in item.keys()
            check_dict(check[key], item[key])
    else:
        assert isinstance(item, type(check))
        assert item == check


@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_as_dict_methods(dp_kwargs: dict, dp_cls: Type[Descriptor], skip):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    dp_kwargs = deepcopy(dp_kwargs)

    if isinstance(skip, str):
        del dp_kwargs[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc = obj.as_dict(skip=skip)

    expected_keys = set(dp_kwargs.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(dp_kwargs, enc)


@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_as_data_dict_methods(dp_kwargs: dict, dp_cls: Type[Descriptor], skip):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    if isinstance(skip, str):
        del data_dict[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc_d = obj.as_data_dict(skip=skip)

    expected_keys = set(data_dict.keys())
    obtained_keys = set(enc_d.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(data_dict, enc_d)


class A(BaseObj):
    def __init__(self, name: str = "A", **kwargs):
        super().__init__(name=name, **kwargs)


class B(BaseObj):
    def __init__(self, a, b):
        super(B, self).__init__("B", a=a)
        self.b = b


@pytest.mark.parametrize(**dp_param_dict)
def test_custom_class_as_dict_methods(dp_kwargs: dict, dp_cls: Type[Descriptor]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    a_kw = {data_dict["name"]: dp_cls(**data_dict)}

    full_d = {
        "@module": A.__module__,
        "@class": A.__name__,
        "@version": None,
        "name": "A",
        dp_kwargs["name"]: dp_kwargs,
    }

    obj = A(**a_kw)

    enc = obj.as_dict()
    expected_keys = set(full_d.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(full_d, enc)


@pytest.mark.parametrize(**dp_param_dict)
def test_custom_class_as_data_dict_methods(dp_kwargs: dict, dp_cls: Type[Descriptor]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    a_kw = {data_dict["name"]: dp_cls(**data_dict)}

    full_d = {"name": "A", dp_kwargs["name"]: data_dict}

    obj = A(**a_kw)

    enc = obj.as_data_dict()
    expected_keys = set(full_d.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(full_d, enc)
