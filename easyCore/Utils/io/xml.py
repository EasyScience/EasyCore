from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import textwrap

from collections.abc import MutableMapping
import xml.etree.ElementTree as ET
from math import floor, log10
from numbers import Number
from typing import List, TYPE_CHECKING, Any, Optional, Dict, Union

from easyCore import np
from easyCore.Utils.io.template import BaseEncoderDecoder
from easyCore.Utils.io.dict import DictSerializer, DataDictSerializer

if TYPE_CHECKING:
    from easyCore.Utils.typing import B, V, BV


class XMLSerializer(BaseEncoderDecoder):
    def encode(
        self,
        obj: BV,
        skip: Optional[List[str]] = None,
        data_only: bool = False,
        fast: bool = False,
        header: bool = False,
        **kwargs,
    ) -> str:
        if skip is None:
            skip = []
        encoder = DictSerializer
        if data_only:
            encoder = DataDictSerializer
        obj_dict = obj.encode(encoder=encoder, skip=skip, **kwargs)
        block = ET.Element("data")
        self._check_class(block, None, obj_dict)
        header = ""
        if header:
            header = '?xml version="1.0"  encoding="UTF-8"?'
        if not fast:
            ET.indent(block)
            if header:
                header += "\n"
        return header + ET.tostring(block, encoding="unicode")

    @classmethod
    def decode(cls, data) -> BV:
        data_xml = ET.XML(data)
        out_dict = {}
        for element in data_xml:
            XMLSerializer._element_to_dict(element, out_dict)
        return DictSerializer.decode(out_dict)

    @staticmethod
    def _element_to_dict(element, out_dict):
        label = element.tag
        if label[0] == "_":
            label = "@" + label[2:]
        if len(element) == 0:
            out_dict[label] = XMLSerializer.string_to_variable(element.text)
        else:
            this_dict = {}
            for el in element:
                XMLSerializer._element_to_dict(el, this_dict)
            if label in out_dict.keys():
                old_value = out_dict[label]
                if not isinstance(old_value, list):
                    old_value = [old_value]
                old_value.append(this_dict)
                this_dict = old_value
            out_dict[label] = this_dict

    @staticmethod
    def string_to_variable(in_string: str):
        in_string = in_string.strip()
        if "'" in in_string:
            in_string = in_string.replace("'", "")
        if '"' in in_string:
            in_string = in_string.replace('"', "")
        try:
            value = float(in_string)
        except ValueError:
            if in_string == "True":
                value = True
            elif in_string == "False":
                value = False
            elif in_string == "None":
                value = None
            else:
                value = in_string
        return value

    def _check_class(self, element, key: str, value: Any):
        T_ = type(value)
        if isinstance(value, dict):
            for k, v in value.items():
                kk = k
                if k[0] == "@":
                    kk = "__" + kk[1:]
                if not isinstance(v, list):
                    s = ET.SubElement(element, kk)
                    self._check_class(s, kk, v)
                else:
                    self._check_class(element, kk, v)
        elif isinstance(value, bool):
            element.text = str(value)
        elif isinstance(value, str):
            element.text = value
        elif isinstance(value, list):
            for i in value:
                s = ET.SubElement(element, key)
                self._check_class(s, None, i)
        elif value is None:
            element.text = "None"
        elif issubclass(T_, Number):
            element.text = str(value)
        else:
            raise NotImplementedError
