__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from typing import Union, List

from easyCore.Objects.Base import Descriptor, Parameter, BaseObj
from easyCore.Objects.Groups import BaseCollection


class Element:
    pass


class Specie(BaseObj):

    def __init__(self, specie: Descriptor, interface=None):
        super(Specie, self).__init__('specie', specie=specie)
        self.interface = interface
        if self.interface is not None:
            self.interface.generate_bindings(self)

    @classmethod
    def from_str(cls, specie_str):
        return cls(Descriptor('specie', specie_str))

    def __repr__(self) -> str:
        return self.specie.raw_value

    def __str__(self) -> str:
        return self.specie.raw_value


class Composition(BaseCollection):
    class Container(BaseObj):
        def __init__(self, specie: Specie, occupation: Parameter, interface=None):
            super(Composition.Container, self).__init__(specie.specie.raw_value, specie_type=specie,
                                                        occupation=occupation, interface=interface)
            self.interface = interface
            if self.interface is not None:
                self.interface.generate_bindings(self)

        def __repr__(self) -> str:
            return f'{self.occupation.raw_value}{self.name}'

        def __str__(self):
            return f'{self.occupation.raw_value}{self.name}'

    # def __init__(self, species: Union[Specie, List[Specie]], occupation: Union[float, List[Parameter]] = 1):
    #     if not isinstance(species, list):
    #         species = [species]
    #     if not isinstance(occupation, list):
    #         occupation = [Parameter('occupation', occupation)]
    #     composition_in = [self.Container(specie, occupation) for specie, occupation in zip(species, occupation)]
    #     super(Composition, self).__init__('composition', *composition_in)
