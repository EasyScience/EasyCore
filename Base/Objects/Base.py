__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import numpy as np
from lmfit import Parameter as lmfitPar
from Base.Objects.Borg import Borg

borg = Borg()

class Descriptor:
    def __init__(self, name: str, value=None, description=None, url: str='',
                 callback: property = None, parent=None):
        self.name: str = name
        self._val = value
        self.unit = None
        self.description: str = description
        self.display_name: str = ''
        self.url: str = url
        self._callback: property = callback
        self.user_data: dict = {}
        self._type = type(value)
        self._parent = parent

    @property
    def value(self):
        # Cached property?
        return self._val

    @value.setter
    def value(self, value):
        # There should be a callback to the base module which has a Borg, with
        # if self._parent is not None and hasattr(self._parent, '_history'):
        #     self._parent._history[self._parent.__hash__()].append(self, 'value_change', value)
        # Cached property?
        self._val = value

    def _validator(self, value):
        assert isinstance(value, self._type)


class Parameter(Descriptor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min: float = -np.Inf
        self.max: float = np.Inf
        self.fixed: bool = False
        self.initial_value = self.value
        self.constraints: dict = {
            'user': [],
            'physical': [],
            'builtin': [Constraint(lambda x: x < self.min, self.min),
                        Constraint(lambda x: x > self.max, self.max)]
        }
        self.__previous_set = self.__class__.value.fset
        setattr(self.__class__, 'value', property(fget=self.__class__.value.fget,
                                                  fset=lambda obj, val: self.__previous_set(obj, obj._validate(val)),
                                                  fdel=self.__class__.value.fdel))

    def for_fit(self):
        return lmfitPar(self.name, value=self.value, vary=~self.fixed, min=self.min, max=self.max,
                 expr=None, brute_step=None, user_data=self.user_data)

    def _validate(self, value):
        new_value = value
        for constraint in self.constraints.values():
            for test in constraint:
                if test(value):
                    new_value = test.value()
        return new_value


class Constraint:
    def __init__(self, validator, fail_value):
        self._validator = validator
        self._fail_value = fail_value

    def __call__(self, *args, **kwargs):
        return self._validator(*args, **kwargs)

    def value(self):
        return self._fail_value
