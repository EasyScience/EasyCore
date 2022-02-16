#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from jax import numpy as np
import matplotlib.pyplot as plt
from easyCore.models.jax.polynomial import Line
from easyCore.models.jax.distributions import Gaussian
from easyCore.optimization.model import EasyModel, CompositeModel, Model

line = EasyModel(Line.from_pars(1.1, 3.))
gauss = EasyModel(Gaussian.from_pars(20, 5., 0.8))
C = line + gauss

x_min, x_max = 1, 9
x = np.linspace(x_min, x_max, 201)

kernel = Model(lambda x: Gaussian.from_pars(1., (x_max-x_min)/2, 0.4)(x))

C2 = CompositeModel(C, kernel, np.convolve, fn_kwargs={'mode': 'same'})

plt.plot(x, C(x))
plt.plot(x, kernel(x))
plt.show()

plt.plot(x, C2(x))
plt.show()

from jax import grad, jit, vmap

C._function = np.add
GC = vmap(grad(C2))(x)

plt.plot(x, GC)
plt.show()

