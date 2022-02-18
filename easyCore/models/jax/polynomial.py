#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from jax import jit, numpy as jnp
from typing import TYPE_CHECKING, Union, List, Tuple
from ..polynomial import Polynomial as PolynomialBase, Line as LineBase

if TYPE_CHECKING:
    import jaxlib.xla_extension.DeviceArray as DeviceArray


class Polynomial(PolynomialBase):
    def __call__(
        self, x: Union[jnp.ndarray, DeviceArray], *args, **kwargs
    ) -> DeviceArray:
        v = jnp.array([c.raw_value for c in self.coefficients])
        return self._calculate(x, v)

    @staticmethod
    @jit
    def _calculate(
        x: Union[jnp.ndarray, DeviceArray], values: DeviceArray
    ) -> DeviceArray:
        return jnp.polyval(values, x)

    @jit
    def model(
        self,
        theta: Union[List, Tuple, jnp.ndarray, DeviceArray],
        x: Union[jnp.ndarray, DeviceArray],
    ):
        for ind in enumerate(theta):
            self.coefficients[ind].value = theta[ind]
        return self._calculate(x, theta)


class Line(LineBase):
    def __call__(
        self, x: Union[jnp.ndarray, DeviceArray], *args, **kwargs
    ) -> DeviceArray:
        return self._calculate(x, self.m.raw_value, self.c.raw_value)

    @staticmethod
    @jit
    def _calculate(
        x: Union[jnp.ndarray, DeviceArray], m: float, c: float
    ) -> DeviceArray:
        return m * x + c

    @jit
    def model(
        self,
        theta: Union[List, Tuple, jnp.ndarray, DeviceArray],
        x: Union[jnp.ndarray, DeviceArray],
    ):
        self.m = theta[0]
        self.c = theta[1]
        return self._calculate(x, *theta)
