#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from typing import ClassVar, Iterable

from easyCore import np
from easyCore.Objects.Variable import Parameter
from easyCore.Objects.ObjectClasses import BaseObj
from easyCore.Objects.Groups import BaseCollection
import scipy.stats as sc_stats


class Gaussian(BaseObj):
    amplitude: ClassVar[Parameter]
    mean: ClassVar[BaseCollection]
    cov_matrix: ClassVar[BaseCollection]

    def __init__(self, amplitude, mean, cov_matrix, name=None):
        if not isinstance(mean, BaseCollection):
            if isinstance(mean, Parameter):
                mean = [mean]
            mean = BaseCollection("mean", *mean)
        if not isinstance(cov_matrix, BaseCollection):
            if isinstance(cov_matrix, Parameter):
                cov_matrix = [cov_matrix]
            cov_matrix = BaseCollection("cov_matrix", *cov_matrix)
        if name is None:
            name = f"{len(mean)}D_Gaussian"

        super(Gaussian, self).__init__(
            name, amplitude=amplitude, mean=mean, cov_matrix=cov_matrix
        )

    @classmethod
    def from_pars(cls, amplitude, mean, cov_matrix):
        amplitude = Parameter("amplitude", amplitude)
        if isinstance(mean, Iterable):
            mean = BaseCollection(
                "mean",
                *[Parameter(f"mean_{ind}", mean_i) for ind, mean_i in enumerate(mean)],
            )
        else:
            mean = Parameter("mean", mean)
        if isinstance(cov_matrix, Iterable):
            cov_matrix = np.array(cov_matrix)
            cov_matrix = BaseCollection(
                "cov_matrix",
                *[
                    Parameter(
                        f"cov_{'_'.join([str(i) for  i in idx])}", cov_matrix[idx]
                    )
                    for idx in np.ndindex(cov_matrix.shape)
                ],
            )
        else:
            cov_matrix = Parameter("cov_matrix", cov_matrix)
        return cls(amplitude, mean, cov_matrix)

    @property
    def dimensionality(self) -> int:
        return len(self.mean)

    @property
    def covariance(self) -> np.ndarray:
        return np.array([cov.raw_value for cov in self.cov_matrix]).reshape(
            [self.dimensionality] * self.dimensionality
        )

    def __call__(self, x, *args, **kwargs):

        return self.amplitude.raw_value * sc_stats.multivariate_normal.pdf(
            x, mean=[mean.raw_value for mean in self.mean], cov=self.covariance
        )
