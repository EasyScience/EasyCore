#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

from jax import numpy as np, scipy as sp, jit, random, tree_multimap, grad, jacfwd, vmap
import matplotlib.pyplot as plt
from easyCore.models.jax.polynomial import Line
from easyCore.models.jax.distributions import Gaussian
from easyCore.optimization.models import EasyModel, CompositeModel, Model

OPTIM = "grad"
OPTIM = "newton"


# Setup reference data
line = EasyModel(Line.from_pars(1.1, 3.0))
gauss = EasyModel(Gaussian.from_pars(60.0, 6.0, 0.8))
C = line + gauss

x_min, x_max = 1, 15
x = np.linspace(x_min, x_max, 201)

kernel = EasyModel(Gaussian.from_pars(1.0, x_min + (x_max - x_min) / 2, 0.4))
kernel.easy_model.mean[0].fixed = True
kernel.easy_model.amplitude.fixed = True
C2 = CompositeModel(C, kernel, sp.signal.convolve, fn_kwargs={"mode": "same"})

key = random.PRNGKey(42)
y = C2(x) + 4 * random.normal(key, shape=x.shape)

# Set a new starting point
pars = C2.get_fit_parameters()
sp = [1.5, 1.5, 20.0, 5.0, 0.7, 4.0, 0.3]
for p, s in zip(pars, sp):
    p.value = s

model_starting = C2(x)

n_steps = 100


@jit
def lagrangian1(theta, x_, y_):
    prediction = theta(x_)
    return np.mean((prediction - y_) ** 2)


if OPTIM == "grad":

    @jit
    def update(theta, x_, y_, LEARNING_RATE=5e-6):
        gradient = grad(lagrangian1)(theta, x_, y_)
        return tree_multimap(
            lambda param, g: param - g * LEARNING_RATE, theta, gradient
        )


elif OPTIM == "newton":

    @jit
    def update(theta, x_, y_):
        G = grad(lagrangian1)
        gradient = G(theta, x_, y_)
        hessian = jacfwd(lambda l: grad(lagrangian1)(l, x_, y_))(theta)

        return tree_multimap(
            lambda param, g, g2: param - g / g2, theta, gradient, hessian
        )


else:
    ValueError(f"Unknown optimizer {OPTIM}")

for _ in range(n_steps):
    C2 = update(C2, x, y)

plt.plot(x, y, "k-", label="data")
plt.plot(x, model_starting, "r-", label="model (Starting point)")
plt.plot(x, C2(x), "b-", label="model (Optimized)")
plt.legend()
plt.show()
