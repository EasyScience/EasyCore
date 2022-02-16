#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import jax

import numpy as np
import jax.numpy as jnp
from easyCore.Objects.jax.Variable import Parameter, PrimalValue
from easyCore.Objects.ObjectClasses import BaseObj
from easyCore.Objects.jax.ObjectClasses import cls_converter
from jax.tree_util import Partial

def init_mlp_params(layer_widths):
  params = []
  for n_in, n_out in zip(layer_widths[:-1], layer_widths[1:]):
    params.append(
        dict(weights=np.random.normal(size=(n_in, n_out)) * np.sqrt(2/n_in),
             biases=np.ones(shape=(n_out,))
            )
    )
  return params


params = init_mlp_params([1, 128, 128, 1])
jax.tree_map(lambda x: x.shape, params)

def forward(params, x):
  *hidden, last = params
  for layer in hidden:
    x = jax.nn.relu(x @ layer['weights'] + layer['biases'])
  return x @ last['weights'] + last['biases']

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
  return jax.tree_multimap(
      lambda p, g: p - LEARNING_RATE * g, params, grads
  )


class _COS(BaseObj):
    def __init__(self, name, amplitude, phase, period):
        super(_COS, self).__init__(name, amplitude=amplitude, phase=phase, period=period)

    def __call__(self, x):
        return self._calculate((self.amplitude.raw_value,
                                self.phase.raw_value,
                                self.period.raw_value), x)

    @staticmethod
    @jax.jit
    def _calculate(theta, x):
        amp, phase, period = theta
        return amp * jnp.cos(phase+ x / period)

    def __repr__(self):
        return f"<Cosine: amp={self.amplitude.raw_value}, period={self.period.raw_value}, phase={self.phase.raw_value}>"

    @classmethod
    def from_pars(cls, amp, phase, period):
        return cls('cosine', PrimalValue('amplitude', amp), PrimalValue('phase', phase), PrimalValue('period', period))

    @classmethod
    def default(cls):
        return cls.from_pars(1., 0., 1.)

    @Partial(jax.jit, static_argnums=(0,))
    def model(self, theta, x):
        self.amplitude.value = theta[0]
        self.phase.value = theta[1]
        self.period.value = theta[2]
        return self(x)

COS = cls_converter(_COS)
cos = COS.default()

import matplotlib.pyplot as plt

xs = np.random.normal(size=(1280, 1))
ys = cos(xs)

for _ in range(1000):
  params = update(params, xs, ys)

plt.scatter(xs, ys)
plt.scatter(xs, forward(params, xs), label='Model prediction')
plt.legend()
plt.show()

def loss_fn(theta, x, y):
  prediction = cos.model(theta, x)
  return jnp.mean((prediction-y)**2)

def update(theta, x, y, lr=0.1):
  return theta - lr * jax.grad(loss_fn)(theta, x, y)

theta = jnp.array([1.3, 1.6, 1.7])

theta_prev = (np.inf, np.inf, np.inf)
for _ in range(1000):
  theta = update(theta, xs, ys)

print(theta)
xnp = xs.__array__().reshape(-1)
idx = np.argsort(xnp)
ynp = cos.model(theta, xs).__array__().reshape(-1)
plt.plot(xnp[idx], ynp[idx], label='Model prediction')
plt.scatter(xs, ys, label='cos(x)')
plt.legend()
plt.show()

Jacobian = jax.jit(lambda xx, th: jax.vmap(lambda _x: jax.jacfwd(lambda _theta: cos.model(_theta, _x))(th))(xx))
jac = Jacobian(xs, theta)
this_jac = jac.__array__().reshape(-1,len(theta))
plt.plot(xnp[idx], this_jac[idx, 0], label='J_amp')
plt.plot(xnp[idx], this_jac[idx, 1], label='J_ph')
plt.plot(xnp[idx], this_jac[idx, 2], label='J_per')
plt.legend()
plt.show()