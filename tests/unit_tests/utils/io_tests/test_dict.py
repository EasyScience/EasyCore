__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from copy import deepcopy
from typing import Type

import numpy as np
import pytest
from importlib import metadata

from easyCore.Utils.io.dict import DataDictSerializer
from easyCore.Utils.io.dict import DictSerializer

from .test_core import A
from .test_core import B
from .test_core import BaseObj
from .test_core import Descriptor
from .test_core import check_dict
from .test_core import dp_param_dict
from .test_core import skip_dict


def recursive_remove(d, remove_keys: list) -> dict:
    """
    Remove keys from a dictionary.
    """
    if not isinstance(remove_keys, list):
        remove_keys = [remove_keys]
    if isinstance(d, dict):
        dd = {}
        for k in d.keys():
            if k not in remove_keys:
                dd[k] = recursive_remove(d[k], remove_keys)
        return dd
    else:
        return d


########################################################################################################################
# TESTING ENCODING
########################################################################################################################
@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DictSerializer(dp_kwargs: dict, dp_cls: Type[Descriptor], skip):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    dp_kwargs = deepcopy(dp_kwargs)

    if isinstance(skip, str):
        del dp_kwargs[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc = obj.encode(skip=skip, encoder=DictSerializer)

    expected_keys = set(dp_kwargs.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(dp_kwargs, enc)


@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DataDictSerializer(dp_kwargs: dict, dp_cls: Type[Descriptor], skip):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    if isinstance(skip, str):
        del data_dict[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc_d = obj.encode(skip=skip, encoder=DataDictSerializer)

    expected_keys = set(data_dict.keys())
    obtained_keys = set(enc_d.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(data_dict, enc_d)


@pytest.mark.parametrize(
    "encoder", [None, DataDictSerializer], ids=["Default", "DataDictSerializer"]
)
@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_encode_data(dp_kwargs: dict, dp_cls: Type[Descriptor], skip, encoder):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)

    if isinstance(skip, str):
        del data_dict[skip]

    if not isinstance(skip, list):
        skip = [skip]

    enc_d = obj.encode_data(skip=skip, encoder=encoder)

    expected_keys = set(data_dict.keys())
    obtained_keys = set(enc_d.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(data_dict, enc_d)


@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_custom_class_DictSerializer_encode(
    dp_kwargs: dict, dp_cls: Type[Descriptor], skip
):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    a_kw = {data_dict["name"]: dp_cls(**data_dict)}

    full_d = {
        "@module": A.__module__,
        "@class": A.__name__,
        "@version": None,
        "name": "A",
        dp_kwargs["name"]: deepcopy(dp_kwargs),
    }

    if not isinstance(skip, list):
        skip = [skip]

    full_d = recursive_remove(full_d, skip)

    obj = A(**a_kw)

    enc = obj.encode(skip=skip, encoder=DictSerializer)
    expected_keys = set(full_d.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(full_d, enc)


@pytest.mark.parametrize(**skip_dict)
@pytest.mark.parametrize(**dp_param_dict)
def test_custom_class_DataDictSerializer(
    dp_kwargs: dict, dp_cls: Type[Descriptor], skip
):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    a_kw = {data_dict["name"]: dp_cls(**data_dict)}

    full_d = {"name": "A", dp_kwargs["name"]: data_dict}

    full_d = recursive_remove(full_d, skip)

    obj = A(**a_kw)

    enc = obj.encode(skip=skip, encoder=DataDictSerializer)
    expected_keys = set(full_d.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(full_d, enc)


@pytest.mark.parametrize(
    "encoder", [None, DataDictSerializer], ids=["Default", "DataDictSerializer"]
)
@pytest.mark.parametrize(**dp_param_dict)
def test_custom_class_encode_data(dp_kwargs: dict, dp_cls: Type[Descriptor], encoder):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    a_kw = {data_dict["name"]: dp_cls(**data_dict)}

    full_d = {"name": "A", dp_kwargs["name"]: data_dict}

    obj = A(**a_kw)

    enc = obj.encode_data(encoder=encoder)
    expected_keys = set(full_d.keys())
    obtained_keys = set(enc.keys())

    dif = expected_keys.difference(obtained_keys)

    assert len(dif) == 0

    check_dict(full_d, enc)


def test_custom_class_full_encode_with_numpy():
    class B(BaseObj):
        def __init__(self, a, b):
            super(B, self).__init__("B", a=a)
            self.b = b
    # Same as in __init__.py for easyCore
    try:
        version = metadata.version(__package__ or __name__)
    except metadata.PackageNotFoundError:
        version = '0.0.0'

    obj = B(Descriptor("a", 1.0), np.array([1.0, 2.0, 3.0]))
    full_enc = obj.encode(encoder=DictSerializer, full_encode=True)
    expected = {
        "@module": "tests.unit_tests.utils.io_tests.test_dict",
        "@class": "B",
        "@version": None,
        "b": {
            "@module": "numpy",
            "@class": "array",
            "dtype": "float64",
            "data": [1.0, 2.0, 3.0],
        },
        "a": {
            "@module": "easyCore.Objects.Variable",
            "@class": "Descriptor",
            "@version": version,
            "description": "",
            "units": "dimensionless",
            "display_name": "a",
            "name": "a",
            "enabled": True,
            "value": 1.0,
            "url": "",
        },
    }
    check_dict(full_enc, expected)


def test_custom_class_full_decode_with_numpy():

    obj = B(Descriptor("a", 1.0), np.array([1.0, 2.0, 3.0]))
    full_enc = obj.encode(encoder=DictSerializer, full_encode=True)
    obj2 = B.decode(full_enc, decoder=DictSerializer)
    assert obj.name == obj2.name
    assert obj.a.raw_value == obj2.a.raw_value
    assert np.all(obj.b == obj2.b)


########################################################################################################################
# TESTING DECODING
########################################################################################################################
@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DictSerializer_decode(dp_kwargs: dict, dp_cls: Type[Descriptor]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)
    if "units" in data_dict.keys():
        data_dict["unit"] = data_dict.pop("units")
    if "value" in data_dict.keys():
        data_dict["raw_value"] = data_dict.pop("value")

    enc = obj.encode(encoder=DictSerializer)
    dec = dp_cls.decode(enc, decoder=DictSerializer)

    for k in data_dict.keys():
        if hasattr(obj, k) and hasattr(dec, k):
            assert getattr(obj, k) == getattr(dec, k)
        else:
            raise AttributeError(f"{k} not found in decoded object")


@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DictSerializer_from_dict(dp_kwargs: dict, dp_cls: Type[Descriptor]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)
    if "units" in data_dict.keys():
        data_dict["unit"] = data_dict.pop("units")
    if "value" in data_dict.keys():
        data_dict["raw_value"] = data_dict.pop("value")

    enc = obj.encode(encoder=DictSerializer)
    dec = dp_cls.from_dict(enc)

    for k in data_dict.keys():
        if hasattr(obj, k) and hasattr(dec, k):
            assert getattr(obj, k) == getattr(dec, k)
        else:
            raise AttributeError(f"{k} not found in decoded object")


@pytest.mark.parametrize(**dp_param_dict)
def test_variable_DataDictSerializer_decode(dp_kwargs: dict, dp_cls: Type[Descriptor]):
    data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != "@"}

    obj = dp_cls(**data_dict)
    if "units" in data_dict.keys():
        data_dict["unit"] = data_dict.pop("units")
    if "value" in data_dict.keys():
        data_dict["raw_value"] = data_dict.pop("value")

    enc = obj.encode(encoder=DataDictSerializer)
    with pytest.raises(NotImplementedError):
        dec = obj.decode(enc, decoder=DataDictSerializer)


def test_group_encode():
    d0 = Descriptor("a", 0)
    d1 = Descriptor("b", 1)

    from easyCore.Objects.Groups import BaseCollection

    b = BaseCollection("test", d0, d1)
    d = b.as_dict()
    assert isinstance(d["data"], list)


def test_group_encode2():
    d0 = Descriptor("a", 0)
    d1 = Descriptor("b", 1)

    from easyCore.Objects.Groups import BaseCollection

    b = BaseObj("outer", b=BaseCollection("test", d0, d1))
    d = b.as_dict()
    assert isinstance(d["b"], dict)


#
# @pytest.mark.parametrize(**dp_param_dict)
# def test_custom_class_DictSerializer_decode(dp_kwargs: dict, dp_cls: Type[Descriptor]):
#
#     data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != '@'}
#
#     a_kw = {
#         data_dict['name']: dp_cls(**data_dict)
#     }
#
#     obj = A(**a_kw)
#
#     enc = obj.encode(encoder=DictSerializer)
#
#     stripped_encode = {k: v for k, v in enc.items() if k[0] != '@'}
#     stripped_encode[data_dict['name']] = data_dict
#
#     dec = obj.decode(enc, decoder=DictSerializer)
#
#     def test_objs(reference_obj, test_obj, in_dict):
#         if 'value' in in_dict.keys():
#             in_dict['raw_value'] = in_dict.pop('value')
#         if 'units' in in_dict.keys():
#             del in_dict['units']
#         for k in in_dict.keys():
#             if hasattr(reference_obj, k) and hasattr(test_obj, k):
#                 if isinstance(in_dict[k], dict):
#                     test_objs(getattr(obj, k), getattr(test_obj, k), in_dict[k])
#                 assert getattr(obj, k) == getattr(dec, k)
#             else:
#                 raise AttributeError(f"{k} not found in decoded object")
#     test_objs(obj, dec, stripped_encode)
#
#
# @pytest.mark.parametrize(**skip_dict)
# @pytest.mark.parametrize(**dp_param_dict)
# def test_custom_class_DataDictSerializer(dp_kwargs: dict, dp_cls: Type[Descriptor], skip):
#     data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != '@'}
#
#     a_kw = {
#         data_dict['name']: dp_cls(**data_dict)
#     }
#
#     full_d = {
#         "name":        "A",
#         dp_kwargs['name']: data_dict
#     }
#
#     full_d = recursive_remove(full_d, skip)
#
#     obj = A(**a_kw)
#
#     enc = obj.encode(skip=skip, encoder=DataDictSerializer)
#     expected_keys = set(full_d.keys())
#     obtained_keys = set(enc.keys())
#
#     dif = expected_keys.difference(obtained_keys)
#
#     assert len(dif) == 0
#
#     check_dict(full_d, enc)
#
#
# @pytest.mark.parametrize('encoder', [None, DataDictSerializer], ids=['Default', 'DataDictSerializer'])
# @pytest.mark.parametrize(**dp_param_dict)
# def test_custom_class_encode_data(dp_kwargs: dict, dp_cls: Type[Descriptor], encoder):
#     data_dict = {k: v for k, v in dp_kwargs.items() if k[0] != '@'}
#
#     a_kw = {
#         data_dict['name']: dp_cls(**data_dict)
#     }
#
#     full_d = {
#         "name":        "A",
#         dp_kwargs['name']: data_dict
#     }
#
#     obj = A(**a_kw)
#
#     enc = obj.encode_data(encoder=encoder)
#     expected_keys = set(full_d.keys())
#     obtained_keys = set(enc.keys())
#
#     dif = expected_keys.difference(obtained_keys)
#
#     assert len(dif) == 0
#
#     check_dict(full_d, enc)
