__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import lmfit
import numpy as np
from typing import Callable
from functools import cached_property


class Descriptor:
    def __init__(self, name: str = '', value=None, description=None, url: str='',
                 callback: property = None):
        self.name: str = name
        self._value = None
        self.unit = None
        self.description: str = description
        self.display_name: str = ''
        self.url: str = url
        self._callback: Callable = callback
        self._additional: dict = {}
        self.value = value

    @property
    def value(self):
        # Cached property?
        return self._value

    @value.setter
    def value(self, value):
        # Cached property?
        self._value = value


class Parameter(Descriptor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min: float = -np.Inf
        self.max: float = np.Inf
        self.fixed: bool = False
        self.constraints: dict = {
            'user': [],
            'physical': [],
            'builtin': [lambda x: x > self.min,
                        lambda x: x < self.max]
        }
        self._validator: Callable = None
