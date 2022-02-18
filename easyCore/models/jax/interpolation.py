#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from jax import jit, numpy as jnp
from typing import Tuple, Optional, Union
from ..interpolation import Interp1D as _Interp1DBase


class Interp1D(_Interp1DBase):
    def __call__(self, x: jnp.ndarray, *args, **kwargs) -> jnp.ndarray:
        dependent = jnp.array([data.raw_value for data in self._dependents.data])
        return self._call(x, self._independent, dependent)

    @staticmethod
    @jit
    def _call(x_new, x, y):
        return jnp.interp(x_new, x, y)

    @staticmethod
    @jit
    def _argsort(x: jnp.ndarray) -> jnp.ndarray:
        return jnp.argsort(x)
