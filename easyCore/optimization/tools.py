#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"


class NameConverter:
    def __init__(self):
        from easyCore import borg

        self._borg = borg

    def get_name_from_key(self, item_key: int) -> str:
        return getattr(self._borg.map.get_item_by_key(item_key), "name", "")

    def get_item_from_key(self, item_key: int) -> object:
        return self._borg.map.get_item_by_key(item_key)

    def get_key(self, item: object) -> int:
        return self._borg.map.convert_id_to_key(item)
