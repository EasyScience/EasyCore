#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from easyCore import np
from easyCore.Objects.Variable import Descriptor, Parameter
from easyCore.Objects.Base import BaseObj
from easyCore.Objects.Groups import BaseCollection

from typing import ClassVar, Tuple, Optional


class Interp1D(BaseObj):

    _dependents: ClassVar[BaseCollection]

    def __init__(self, name: str, independent: np.ndarray, dependents: BaseCollection):
        super(Interp1D, self).__init__(name, _dependents=dependents)
        self._independent = independent
        self._update_cache()

    @classmethod
    def default(cls):
        independent = np.array([])
        dependents = BaseCollection('intensity')
        return cls('interp', independent, dependents)

    @classmethod
    def from_pars(cls, x: np.ndarray, y: np.ndarray):
        items = cls('interp', x, BaseCollection('intensity', *[Parameter(f'Pt@{x_v}', y_v) for x_v, y_v in zip(x, y)]))
        for item in items._dependents:
            item.callback = property(fset=lambda myself, value: items._update_cache(update=(myself, value)))
        return items

    def add_point(self, x: float, y: float):
        self._independent = np.append(self._independent, x)
        dependent = Parameter(f'Pt@{x}', y,
                              callback=property(fset=lambda myself, value: self._update_cache(update=(myself, value))))
        self._dependents.append(dependent)
        self._update_cache()

    def __call__(self, x: np.ndarray, *args, **kwargs) -> np.ndarray:
        dependent = [data.raw_value for data in self._dependents.data]
        return np.interp(x, self._independent, dependent)

    def _update_cache(self, update: Optional[Tuple[Parameter, float]] = None):
        idx = np.argsort(self._independent)
        if not np.all(self._independent[idx] == self._independent):
            items = list(self._dependents._kwargs.items())
            self._independent = self._independent[idx]
            self._dependents._kwargs.reorder(**{items[i][0]: items[i][1] for i in idx})
        if update is not None:
            (myself, value) = update
            ind = self._dependents.index(myself)
            myself.name = f'Pt@{self._independent[ind]}'
        
    @property
    def x(self):
        return self._independent
    
    @property
    def y(self):
        return self._dependents.data
