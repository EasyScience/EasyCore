#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from easyCore.Elements.periodic_table import Species, Specie as pSpecie
from easyCore.Objects.Base import Descriptor
from easyCore.Utils.classTools import addProp

_SPECIE_DETAILS = {
    'type_symbol': {
        'description': 'A code to identify the atom species occupying this site.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_type_symbol.html',
    },
}


class Specie(Descriptor):

    def __init__(self, specie, **kwargs):
        if kwargs:
           specie = kwargs['value']
        super(Specie, self).__init__('specie', specie, **_SPECIE_DETAILS['type_symbol'])
        self.__gen_data(specie)
        # Monkey patch the unit and the value to take into account the new max/min situation
        self.__previous_set = self.__class__.value.fset

        addProp(self, 'value',
                fget=self.__class__.value.fget,
                fset=lambda obj, val: self.__previous_set(obj, obj.__gen_data(val)),
                fdel=self.__class__.value.fdel)

    def __gen_data(self, value):
        try:
            self._specie = Species.from_string(value)
        except ValueError:
            self._specie = pSpecie(value)
        return value

    def oxi_state(self):
        return self._specie.oxi_state

    def ionic_radius(self):
        return self._specie.ionic_radius

    @property
    def n_scattering_lengths(self):
        return self._specie.data.get('N Scattering Lengths', {})

    def get_attribute(self, attribute):
        return self._specie.data.get(attribute, None)

    @property
    def common_name(self) -> str:
        return self._specie.data['Name']

    @property
    def spin(self):
        if hasattr(self._specie, 'spin'):
            return self._specie.spin
        return None

    @spin.setter
    def spin(self, value):
        if hasattr(self._specie, 'spin') or 'spin' in self._specie.supported_properties:
            self._specie.spin = value
        else:
            raise AttributeError

    def __repr__(self) -> str:
        return str(self._specie)

    def as_dict(self, skip: list = None) -> dict:
        if skip is None:
            skip = []
        skip.append('value')
        return super(Specie, self).as_dict(skip=skip)
            