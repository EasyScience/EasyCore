#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from jax import numpy as np, scipy as sp, grad, jit, vmap, random, jacfwd, jacrev
import matplotlib.pyplot as plt
from easyCore.models.jax.polynomial import Line
from easyCore.models.jax.distributions import Gaussian
from easyCore.optimization.model import EasyModel, CompositeModel, Model

# Setup reference data
line = EasyModel(Line.from_pars(1.1, 3.0))
gauss = EasyModel(Gaussian.from_pars(15, 6.0, 0.8))
C = line + gauss

x_min, x_max = 1, 9
x = np.linspace(x_min, x_max, 201)

kernel = Model(lambda x: Gaussian.from_pars(1.0, x_min + (x_max - x_min) / 2, 0.4)(x))
C2 = CompositeModel(C, kernel, sp.signal.convolve, fn_kwargs={"mode": "same"})

key = random.PRNGKey(42)
y = C2(x) + 4 * random.normal(key, shape=x.shape)
_ = C2(x, m=1.6, c=0.65, amplitude=5.0, mean=4.1, cov_matrix=0.5)


Jacobian = jit(lambda x_, theta: jacrev(C2(x, *theta)))
Hessian = jit(lambda x_, theta: jacfwd(Jacobian(x, *theta)))

J = jit(lambda x_, theta: lambda xx: vmap(Jacobian(xx, theta))(x_))
H = jit(lambda x_, theta: lambda xx: vmap(Hessian(xx, theta))(x_))


def minHessian(x, theta):
    return x - 0.1 * np.linalg.inv(H(x, theta)) @ J(x, theta)


vfuncHS = lambda _x, th: lambda xx: vmap(minHessian(xx, th))(_x)

domain = [1.6, 0.65, 5.0, 4.1, 0.5]
for epoch in range(150):
    domain = vfuncHS(x, domain)


plt.plot(x, y, label="test data")
plt.plot(x, C2(x), label="test model")
plt.plot(x, C2(x, *domain), label="optim model")
plt.legend()
plt.show()
