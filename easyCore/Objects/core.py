#  SPDX-FileCopyrightText: 2023 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2023 Contributors to the easyCore project <https://github.com/easyScience/easyCore

from __future__ import annotations

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import json
from collections import OrderedDict
from hashlib import sha1
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from easyCore.Utils.io.dict import DataDictSerializer
from easyCore.Utils.io.dict import DictSerializer
from easyCore.Utils.io.json import jsanitize

if TYPE_CHECKING:
    from easyCore.Utils.io.template import EC


class ComponentSerializer:
    """
    This is the base class for all easyCore objects and deals with the data conversion to other formats via the `encode`
    and `decode` functions. Shortcuts for dictionary and data dictionary encoding is also present.
    """

    _CORE = True

    def encode(self, skip: Optional[List[str]] = None, encoder: Optional[EC] = None, **kwargs) -> Any:
        """
        Use an encoder to covert an easyCore object into another format. Default is to a dictionary using `DictSerializer`.

        :param skip: List of field names as strings to skip when forming the encoded object
        :param encoder: The encoder to be used for encoding the data. Default is `DictSerializer`
        :param kwargs: Any additional key word arguments to be passed to the encoder
        :return: encoded object containing all information to reform an easyCore object.
        """

        if encoder is None:
            encoder = DictSerializer
        encoder_obj = encoder()
        return encoder_obj.encode(self, skip=skip, **kwargs)

    @classmethod
    def decode(cls, obj: Any, decoder: Optional[EC] = None) -> Any:
        """
        Re-create an easyCore object from the output of an encoder. The default decoder is `DictSerializer`.

        :param obj: encoded easyCore object
        :param decoder: decoder to be used to reform the easyCore object
        :return: Reformed easyCore object
        """

        if decoder is None:
            decoder = DictSerializer
        return decoder.decode(obj)

    def as_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert an easyCore object into a full dictionary using `DictSerializer`.
        This is a shortcut for ```obj.encode(encoder=DictSerializer)```

        :param skip: List of field names as strings to skip when forming the dictionary
        :return: encoded object containing all information to reform an easyCore object.
        """

        return self.encode(skip=skip, encoder=DictSerializer)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> None:
        """
        Re-create an easyCore object from a full encoded dictionary.

        :param obj_dict: dictionary containing the serialized contents (from `DictSerializer`) of an easyCore object
        :return: Reformed easyCore object
        """

        return cls.decode(obj_dict, decoder=DictSerializer)

    def encode_data(self, skip: Optional[List[str]] = None, encoder: Optional[EC] = None, **kwargs) -> Any:
        """
        Returns just the data in an easyCore object win the format specified by an encoder.

        :param skip: List of field names as strings to skip when forming the dictionary
        :param encoder: The encoder to be used for encoding the data. Default is `DataDictSerializer`
        :param kwargs: Any additional keywords to pass to the encoder when encoding
        :return: encoded object containing just the data of an easyCore object.
        """

        if encoder is None:
            encoder = DataDictSerializer
        return self.encode(skip=skip, encoder=encoder, **kwargs)

    def as_data_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Returns a dictionary containing just the data of an easyCore object.

        :param skip: List of field names as strings to skip when forming the dictionary
        :return: dictionary containing just the data of an easyCore object.
        """

        return self.encode(skip=skip, encoder=DataDictSerializer)

    def unsafe_hash(self) -> sha1:
        """
        Returns an hash of the current object. This uses a generic but low
        performance method of converting the object to a dictionary, flattening
        any nested keys, and then performing a hash on the resulting object
        """

        def flatten(obj, seperator='.'):
            # Flattens a dictionary

            flat_dict = {}
            for key, value in obj.items():
                if isinstance(value, dict):
                    flat_dict.update({seperator.join([key, _key]): _value for _key, _value in flatten(value).items()})
                elif isinstance(value, list):
                    list_dict = {'{}{}{}'.format(key, seperator, num): item for num, item in enumerate(value)}
                    flat_dict.update(flatten(list_dict))
                else:
                    flat_dict[key] = value

            return flat_dict

        ordered_keys = sorted(flatten(jsanitize(self.as_dict())).items(), key=lambda x: x[0])
        ordered_keys = [item for item in ordered_keys if '@' not in item[0]]
        return sha1(json.dumps(OrderedDict(ordered_keys)).encode('utf-8'))  # noqa: S324
