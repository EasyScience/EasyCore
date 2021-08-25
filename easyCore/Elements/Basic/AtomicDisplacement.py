#  SPDX-FileCopyrightText: 2021 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.1.0'

from typing import List, Tuple, Union

from easyCore import np
from easyCore.Utils.io.star import StarEntry, StarSection, StarLoop
from easyCore.Objects.Base import BaseObj, Descriptor, Parameter
from easyCore.Utils.classTools import addProp, removeProp
from abc import abstractmethod

_AVAILABLE_ISO_TYPES = {
    'Uani': 'Anisotropic',
    'Uiso': 'Isotropic',
    # 'Uovl': 'Overall',
    # 'Umpe': 'MultipoleExpansion',
    'Bani': 'AnisotropicBij',
    'Biso': 'IsotropicB',
    # 'Bovl': 'OverallB'
}

_ANIO_DETAILS = {
    'adp_type': {
        'description': "A standard code used to describe the type of atomic displacement parameters used for the site.",
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_adp_type.html',
        'value':       'Uani'
    },
    'Uani':     {
        'description': 'Isotropic atomic displacement parameter, or equivalent isotropic atomic  displacement '
                       'parameter, U(equiv), in angstroms squared, calculated from anisotropic atomic displacement  '
                       'parameters.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_aniso_U_.html',
        'value':       0.0,
        'units':       'angstrom^2',
        'fixed':       True,
    },
    'Uiso':     {
        'description': 'The standard anisotropic atomic displacement components in angstroms squared which appear in '
                       'the structure-factor term.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_U_iso_or_equiv.html',
        'value':       0.0,
        'min':         0,
        'max':         np.inf,
        'units':       'angstrom^2',
        'fixed':       True,
    },
    'Bani':     {
        'description': 'The standard anisotropic atomic displacement components in angstroms squared which appear in '
                       'the structure-factor term.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_aniso_B_.html',
        'value':       0.0,
        'units':       'angstrom^2',
        'fixed':       True,
    },
    'Biso':     {
        'description': 'Isotropic atomic displacement parameter, or equivalent isotropic atomic displacement '
                       'parameter, B(equiv), in angstroms squared, calculated from anisotropic displacement '
                       'components.',
        'url':         'https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_B_iso_or_equiv.html',
        'value':       0.0,
        'min':         0,
        'max':         np.inf,
        'units':       'angstrom^2',
        'fixed':       True,
    }
}


class AtomicDisplacement(BaseObj):

    def __init__(self, adp_type: Descriptor, interface=None, **kwargs):
        adp_class_name = adp_type.raw_value
        if adp_class_name in _AVAILABLE_ISO_TYPES.keys():
            adp_class = globals()[_AVAILABLE_ISO_TYPES[adp_class_name]]
            if kwargs:
                if 'adp_class' in kwargs.keys():
                    adp_class = kwargs['adp_class']
                else:
                    adp_class: BaseObj = adp_class.from_pars(interface=interface, **kwargs)
            else:
                adp_class: BaseObj = adp_class.default(interface=interface)
        else:
            raise AttributeError
        super(AtomicDisplacement, self).__init__('adp', adp_type=adp_type, adp_class=adp_class)
        for par in adp_class.get_parameters():
            addProp(self, par.name, fget=self.__a_getter(par.name), fset=self.__a_setter(par.name))
        self.interface = interface

    def switch_type(self, adp_string: str, **kwargs):
        if adp_string in _AVAILABLE_ISO_TYPES.keys():
            adp_class = globals()[_AVAILABLE_ISO_TYPES[adp_string]]
            if kwargs:
                adp_class: AdpBase = adp_class.from_pars(interface=self.interface, **kwargs)
            else:
                adp_class: AdpBase = adp_class.default(interface=self.interface)
        else:
            raise AttributeError
        for par in self.adp_class.get_parameters():
            removeProp(self, par.name)
        self._kwargs['adp_class'] = adp_class
        for par in adp_class.get_parameters():
            addProp(self, par.name, fget=self.__a_getter(par.name), fset=self.__a_setter(par.name))

    @classmethod
    def from_pars(cls, adp_type: str, interface=None, **kwargs):
        return cls(Descriptor('adp_type',
                              value=adp_type,
                              **{k: _ANIO_DETAILS['adp_type'][k] for k in _ANIO_DETAILS['adp_type'].keys() if
                                 k != 'value'}),
                   interface=interface, **kwargs)

    @classmethod
    def default(cls, interface=None):
        return cls(Descriptor('adp_type', **_ANIO_DETAILS['adp_type']), interface=interface)

    @classmethod
    def from_string(cls, in_string: Union[str, StarLoop]) -> Tuple[List[str], List['AtomicDisplacement']]:
        # We assume the in_string is a loop
        from easyCore.Elements.Basic.Site import Site
        if isinstance(in_string, StarLoop):
            loop = in_string
        else:
            loop = StarLoop.from_string(in_string)
        sections = loop.to_StarSections()
        atom_labels = []
        adp = []
        for section in sections:
            entries = section.to_StarEntries()
            site_name_idx = section.labels.index(Site._CIF_CONVERSIONS[0][1])
            atom_labels.append(entries[site_name_idx].value)
            adp_type_idx = section.labels.index(cls._CIF_CONVERSIONS[0][1])
            adp_type = entries[adp_type_idx].value
            if adp_type not in _AVAILABLE_ISO_TYPES:
                raise AttributeError
            adp_class = globals()[_AVAILABLE_ISO_TYPES[adp_type]]
            pars = [par[1] for par in adp_class._CIF_CONVERSIONS]
            par_dict = {}
            idx_list = []
            name_list = []
            for idx, par in enumerate(pars):
                idx_list.append(section.labels.index(par))
                name_list.append(adp_class._CIF_CONVERSIONS[idx][0])
                par_dict[name_list[-1]] = entries[idx_list[-1]].value
            obj = cls.from_pars(adp_type, **par_dict)
            for idx2, idx in enumerate(idx_list):
                if hasattr(entries[idx], 'fixed') and entries[idx].fixed is not None:
                    entry = getattr(obj, name_list[idx2])
                    entry.fixed = entries[idx].fixed
                if hasattr(entries[idx], 'error') and entries[idx].error is not None:
                    entry = getattr(obj, name_list[idx2])
                    entry.error = entries[idx].error
            adp.append(obj)
        return atom_labels, adp

    @property
    def available_types(self) -> List[str]:
        return [name for name in _AVAILABLE_ISO_TYPES.keys()]

    def to_star(self, atom_label: Descriptor) -> StarEntry:
        s = [StarEntry(atom_label, 'label'),
             StarEntry(self.adp_type),
             *[StarEntry(par) for par in self.adp_class.get_parameters()]
             ]
        return StarSection.from_StarEntries(s)

    @staticmethod
    def __a_getter(key: str):

        def getter(obj):
            return obj.adp_class._kwargs[key]

        return getter

    @staticmethod
    def __a_setter(key):
        def setter(obj, value):
            obj.adp_class._kwargs[key].value = value

        return setter


class AdpBase(BaseObj):

    def __init__(self, *args, **kwargs):
        super(AdpBase, self).__init__(*args, **kwargs)

    @property
    def matrix(self) -> np.ndarray:
        matrix = np.zeros([3, 3])
        pars = self.get_parameters()
        if len(pars) == 1:
            np.fill_diagonal(matrix, pars[0].raw_value)
        elif len(pars) == 6:
            matrix[0, 0] = pars[0].raw_value
            matrix[0, 1] = pars[1].raw_value
            matrix[0, 2] = pars[2].raw_value
            matrix[1, 1] = pars[3].raw_value
            matrix[1, 2] = pars[4].raw_value
            matrix[2, 2] = pars[5].raw_value
        return matrix

    @abstractmethod
    def default(cls, interface=None):
        pass

    @abstractmethod
    def from_pars(cls, interface=None, **kwargs):
        pass


class Anisotropic(AdpBase):

    def __init__(self,
                 U_11: Parameter, U_12: Parameter, U_13: Parameter,
                 U_22: Parameter, U_23: Parameter, U_33: Parameter,
                 interface=None):
        super(Anisotropic, self).__init__('anisoU',
                                          U_11=U_11, U_12=U_12, U_13=U_13,
                                          U_22=U_22, U_23=U_23, U_33=U_33)
        self.interface = interface

    @classmethod
    def default(cls, interface=None):
        return cls(*[Parameter(name, **_ANIO_DETAILS['Uani']) for name in ['U_11', 'U_12', 'U_13',
                                                                           'U_22', 'U_23', 'U_33']],
                   interface=interface)

    @classmethod
    def from_pars(cls,
                  U_11: float = _ANIO_DETAILS['Uani']['value'], U_12: float = _ANIO_DETAILS['Uani']['value'],
                  U_13: float = _ANIO_DETAILS['Uani']['value'], U_22: float = _ANIO_DETAILS['Uani']['value'],
                  U_23: float = _ANIO_DETAILS['Uani']['value'], U_33: float = _ANIO_DETAILS['Uani']['value'],
                  interface=None):
        u = {k: _ANIO_DETAILS['Uani'][k] for k in _ANIO_DETAILS['Uani'].keys() if k != 'value'}
        return cls(Parameter('U_11', value=U_11, **u), Parameter('U_12', value=U_12, **u),
                   Parameter('U_13', value=U_13, **u), Parameter('U_22', value=U_22, **u),
                   Parameter('U_23', value=U_23, **u), Parameter('U_33', value=U_33, **u),
                   interface=interface)


class Isotropic(AdpBase):

    def __init__(self, Uiso: Parameter, interface=None):
        super(Isotropic, self).__init__('Uiso', Uiso=Uiso)
        self.interface = interface

    @classmethod
    def default(cls, interface=None):
        return cls(Parameter('Uiso', **_ANIO_DETAILS['Uiso']), interface=interface)

    @classmethod
    def from_pars(cls, Uiso: float = _ANIO_DETAILS['Uiso']['value'], interface=None):
        u = {k: _ANIO_DETAILS['Uiso'][k] for k in _ANIO_DETAILS['Uiso'].keys() if k != 'value'}
        return cls(Parameter('Uiso', value=Uiso, **u), interface=interface)


class AnisotropicBij(AdpBase):

    def __init__(self,
                 B_11: Parameter, B_12: Parameter, B_13: Parameter,
                 B_22: Parameter, B_23: Parameter, B_33: Parameter,
                 interface=None):
        super(AnisotropicBij, self).__init__('anisoB',
                                             B_11=B_11, B_12=B_12, B_13=B_13,
                                             B_22=B_22, B_23=B_23, B_33=B_33)
        self.interface = interface

    @classmethod
    def default(cls, interface=None):
        return cls(*[Parameter(name, **_ANIO_DETAILS['Bani']) for name in ['B_11', 'B_12', 'B_13',
                                                                           'B_22', 'B_23', 'B_33']],
                   interface=interface)

    @classmethod
    def from_pars(cls,
                  B_11: float = _ANIO_DETAILS['Bani']['value'], B_12: float = _ANIO_DETAILS['Bani']['value'],
                  B_13: float = _ANIO_DETAILS['Bani']['value'], B_22: float = _ANIO_DETAILS['Bani']['value'],
                  B_23: float = _ANIO_DETAILS['Bani']['value'], B_33: float = _ANIO_DETAILS['Bani']['value'],
                  interface=None):
        b = {k: _ANIO_DETAILS['Bani'][k] for k in _ANIO_DETAILS['Bani'].keys() if k != 'value'}
        return cls(Parameter('B_11', value=B_11, **b), Parameter('B_12', value=B_12, **b),
                   Parameter('B_13', value=B_13, **b), Parameter('B_22', value=B_22, **b),
                   Parameter('B_23', value=B_23, **b), Parameter('B_33', value=B_33, **b),
                   interface=interface)


class IsotropicB(AdpBase):

    def __init__(self, Biso: Parameter, interface=None):
        super(IsotropicB, self).__init__('Biso', Biso=Biso)
        self.interface = interface

    @classmethod
    def default(cls, interface=None):
        return cls(Parameter('Biso', **_ANIO_DETAILS['Biso']), interface=interface)

    @classmethod
    def from_pars(cls, Biso: float = _ANIO_DETAILS['Biso']['value'], interface=None):
        u = {k: _ANIO_DETAILS['Biso'][k] for k in _ANIO_DETAILS['Biso'].keys() if k != 'value'}
        return cls(Parameter('Biso', value=Biso, **u), interface=interface)
