#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from jax import numpy as np, scipy as sp
import matplotlib.pyplot as plt
from easyCore.models.jax.polynomial import Line
from easyCore.models.jax.distributions import Gaussian
from easyCore.optimization.models import EasyModel, CompositeModel, Model

line = EasyModel(Line.from_pars(1.1, 3.0))
gauss = EasyModel(Gaussian.from_pars(15, 6.0, 0.8))
C = line + gauss

x_min, x_max = 1, 9
x = np.linspace(x_min, x_max, 201)

kernel = Model(lambda x: Gaussian.from_pars(1.0, x_min + (x_max - x_min) / 2, 0.4)(x))


plt.plot(x, C(x), label="Model")
plt.plot(x, line(x), "--")
plt.plot(x, gauss(x), "--")
plt.plot(x, kernel(x), label="Kernel")
plt.legend()
plt.show()

from jax import grad, jit, vmap

C2 = CompositeModel(C, kernel, sp.signal.convolve, fn_kwargs={"mode": "same"})

# C2._function = jit(C2._function)
grad_C2 = jit(vmap(grad(C2)))
plt.plot(x, C2(x), label="Convoluted Model")
plt.plot(x, grad_C2(x), label="Autodiff")
plt.legend()
plt.show()
