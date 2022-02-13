#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import jax.scipy as jsp
from jax import numpy as np, jit
from ..distributions import Gaussian as GaussianBase
from easyCore.Objects.jax.ObjectClasses import cls_converter


@cls_converter
class Gaussian(GaussianBase):

    def __call__(self, x):
        amplitude = self.amplitude.raw_value
        mean = np.array([mean.raw_value for mean in self.mean])
        conv = self.covariance.reshape([self.dimensionality]*self.dimensionality)
        if self.dimensionality == 1:
            return self._call1D(x, amplitude, mean, conv)
        return self._callND(x, amplitude, mean, conv)


    @staticmethod
    @jit
    def _call1D(x, amplitude, mean, cov):
        return amplitude*jsp.stats.norm.pdf(x, loc=mean[0], scale=np.sqrt(cov[0]))

    @staticmethod
    @jit
    def _callND(x, amplitude, mean, conv):
        return amplitude * jsp.stats.multivariate_normal.pdf(x, mean=mean, cov=conv)

    @jit
    def model(self, theta, x):
        amplitude = theta[0]
        self.amplitude = theta[0]
        ni = len(theta[1:])  # i^2 + i -n = 0
        n = int((np.sqrt(ni * 4 + 1) - 1)/2)
        for idx in range(1, n + 1):
            self.mean[idx].value = theta[idx]
        mean = np.array(theta[1:n+1])
        for idx, elem in enumerate(theta[n + 1::]):
            self.cov_matrix[idx].value = elem
        cov = theta[n + 1::].reshape(n, n)
        if self.dimensionality == 1:
            return self._call1D(x, amplitude, mean, cov)
        return self._callND(x, amplitude, mean, cov)


