#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import jax
import numpy as np
import jax.numpy as jnp
from easyCore.Objects.Variable import Parameter
from easyCore.Objects.ObjectClasses import BaseObj

# from easyCore.Objects.jax.ObjectClasses import cls_converter
import matplotlib.pyplot as plt


def init_mlp_params(layer_widths):
    params = []
    for n_in, n_out in zip(layer_widths[:-1], layer_widths[1:]):
        params.append(
            dict(
                weights=np.random.normal(size=(n_in, n_out)) * np.sqrt(2 / n_in),
                biases=np.ones(shape=(n_out,)),
            )
        )
    return params


params = init_mlp_params([1, 128, 128, 1])
jax.tree_map(lambda x: x.shape, params)


def forward(params, x):
    *hidden, last = params
    for layer in hidden:
        x = jax.nn.relu(x @ layer["weights"] + layer["biases"])
    return x @ last["weights"] + last["biases"]


def loss_fn(params, x, y):
    return jnp.mean((forward(params, x) - y) ** 2)


LEARNING_RATE = 0.0001


@jax.jit
def update(params, x, y):
    grads = jax.grad(loss_fn)(params, x, y)
    # Note that `grads` is a pytree with the same structure as `params`.
    # `jax.grad` is one of the many JAX functions that has
    # built-in support for pytrees.

    # This is handy, because we can apply the SGD update using tree utils:
    return jax.tree_multimap(lambda p, g: p - LEARNING_RATE * g, params, grads)


# @cls_converter
class COS(BaseObj):
    def __init__(self, name, amplitude, phase, period, offset):
        super(COS, self).__init__(
            name, amplitude=amplitude, phase=phase, period=period, offset=offset
        )

    def __call__(self, x):
        return self._calculate(
            (
                self.amplitude.raw_value,
                self.phase.raw_value,
                self.period.raw_value,
                self.offset.raw_value,
            ),
            x,
        )

    @staticmethod
    @jax.jit
    def _calculate(theta, x):
        amp, phase, period, offset = theta
        return amp * jnp.cos(phase + x / period) + offset

    def __repr__(self):
        return f"<Cosine: amp={self.amplitude.raw_value}, period={self.period.raw_value}, phase={self.phase.raw_value}>"

    @classmethod
    def from_pars(cls, amp, phase, period, offset):
        return cls(
            "cosine",
            Parameter("amplitude", amp),
            Parameter("phase", phase),
            Parameter("period", period),
            Parameter("offset", offset),
        )

    @classmethod
    def default(cls):
        return cls.from_pars(1.0, 0.0, 1.0, 1.0)

    def model(self, theta, x):
        return self._calculate(theta, x)


cos = COS.default()

xs = np.random.normal(size=(1280, 1))
ys = cos(xs)

for _ in range(1000):
    params = update(params, xs, ys)

plt.scatter(xs, ys)
plt.scatter(xs, forward(params, xs), label="Model prediction")
plt.legend()
plt.show()


def loss_fn(theta, x, y):
    prediction = theta(x)
    return jnp.mean((prediction - y) ** 2)


@jax.jit
def update(theta, x, y, LEARNING_RATE=1e-3):
    grad = jax.grad(loss_fn)(theta, x, y)
    tH = jax.tree_multimap(lambda param, g: param - g * LEARNING_RATE, theta, grad)
    return tH


l = 1280
xs = np.linspace(-2 * np.pi, 2 * np.pi, l)
rng = jax.random.PRNGKey(42)
noise = jax.random.normal(rng, (l,)) * 0.15

ys = cos(xs) + noise
sp = (1.3, 0.5, 0.8, 1.5)
cos2 = COS.from_pars(*sp)
cos3 = COS.from_pars(*sp)

for _ in range(1000):
    cos2 = update(cos2, xs, ys)

print(cos2)
xnp = xs.__array__().reshape(-1)
ynp = cos2(xs).__array__().reshape(-1)
ysp = cos3(xs).__array__().reshape(-1)
plt.plot(xnp, ynp, label="Model Prediction")
plt.plot(xnp, ysp, label="Model Starting point")
plt.plot(xs, ys, ".", label="Model Data")
plt.legend()
plt.show()

theta = np.array(
    [cos2.amplitude.value, cos2.phase.value, cos2.period.value, cos2.offset.value]
)
Jacobian = jax.jit(
    lambda xx, th: jax.vmap(
        lambda _x: jax.jacfwd(lambda _theta: cos2.model(_theta, _x))(th)
    )(xx)
)
jac = Jacobian(xs, theta)
this_jac = jac.__array__().reshape(-1, len(theta))
plt.plot(xnp, this_jac[:, 0], label="J_amp")
plt.plot(xnp, this_jac[:, 1], label="J_ph")
plt.plot(xnp, this_jac[:, 2], label="J_per")
plt.legend()
plt.show()
