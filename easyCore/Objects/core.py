from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from typing import Optional, List, Dict, Any, TYPE_CHECKING, TypeVar
from hashlib import sha1
import json
from easyCore.Utils.io.dict import DictSerializer, DataDictSerializer
from easyCore.Utils.io.json import jsanitize
from collections import OrderedDict

if TYPE_CHECKING:
    from easyCore.Utils.io.template import BaseEncoderDecoder

    EC = TypeVar("EC", bound=BaseEncoderDecoder)


class ComponentSerializer:
    def encode(
        self, skip: Optional[List[str]] = None, encoder: Optional[EC] = None, **kwargs
    ) -> Any:
        if encoder is None:
            encoder = DictSerializer
        encoder_obj = encoder()
        return encoder_obj.encode(self, skip=skip, **kwargs)

    @classmethod
    def decode(cls, obj: Any, decoder: Optional[EC] = None) -> Any:
        if decoder is None:
            decoder = DictSerializer
        return decoder.decode(obj)

    def as_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.encode(skip=skip, encoder=DictSerializer)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> None:
        """
        Populate the object with values from a JSON serialized dict.
        """
        return cls.decode(d, decoder=DictSerializer)

    def encode_data(
        self, skip: Optional[List[str]] = None, encoder: Optional[EC] = None
    ) -> Any:
        if encoder is None:
            encoder = DataDictSerializer
        return self.encode(skip=skip, encoder=encoder)

    def as_data_dict(self, skip: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.encode(skip=skip, encoder=DataDictSerializer)

    def unsafe_hash(self) -> sha1:
        """
        Returns an hash of the current object. This uses a generic but low
        performance method of converting the object to a dictionary, flattening
        any nested keys, and then performing a hash on the resulting object
        """

        def flatten(obj, seperator="."):
            # Flattens a dictionary

            flat_dict = {}
            for key, value in obj.items():
                if isinstance(value, dict):
                    flat_dict.update(
                        {
                            seperator.join([key, _key]): _value
                            for _key, _value in flatten(value).items()
                        }
                    )
                elif isinstance(value, list):
                    list_dict = {
                        "{}{}{}".format(key, seperator, num): item
                        for num, item in enumerate(value)
                    }
                    flat_dict.update(flatten(list_dict))
                else:
                    flat_dict[key] = value

            return flat_dict

        ordered_keys = sorted(
            flatten(jsanitize(self.as_dict())).items(), key=lambda x: x[0]
        )
        ordered_keys = [item for item in ordered_keys if "@" not in item[0]]
        return sha1(json.dumps(OrderedDict(ordered_keys)).encode("utf-8"))  # nosec
