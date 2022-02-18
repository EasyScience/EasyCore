#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import jax
from jax import numpy as np
from jax.tree_util import tree_unflatten, tree_flatten, register_pytree_node_class
from jax import jit, grad, vmap

from easyCore.Objects.Variable import Descriptor, Parameter
from easyCore.Objects.ObjectClasses import BaseObj

clss = [Descriptor, Parameter]
x = np.linspace(0, 10, 11)


def show_example(structured):
    flat, tree = tree_flatten(structured)
    unflattened = tree_unflatten(tree, flat)
    print(
        "structured={}\n  flat={}\n  tree={}\n  unflattened={}".format(
            structured, flat, tree, unflattened
        )
    )


@register_pytree_node_class
class TEST(BaseObj):
    def __init__(self, a, b):
        super(TEST, self).__init__("TEST2", a=a, b=b)

    def __call__(self, x):
        return self.a.raw_value * x ** 2 + self.b.raw_value

    def tree_flatten(self):
        children = (self.a, self.b)
        aux_data = None
        return (children, aux_data)

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        return cls(*children)


def do_test(cls, test_cls):
    print(f"CLS: {cls.__name__}\n-----------------")

    item1 = cls("a", 4.0)
    item2 = cls("b", 5.0)
    # show_example(item1)

    T = test_cls(item1, item2)
    show_example(T)
    g = jit(grad(T))
    vg = jit(vmap(g))
    print("g(x) = {}".format(g(x[4])))
    print("vg(x) = {}".format(vg(x)))
    print(f"\n-----------------")


for cls in clss:
    do_test(cls, TEST)


def cls_converter(cls):
    def tree_flatten(self):
        children = tuple(self._kwargs.values())
        aux_data = {"name": self.name, "keys": tuple(self._kwargs.keys())}
        return (children, aux_data)

    def tree_unflatten(cls, aux_data, children):
        return cls(name=aux_data["name"], **dict(zip(aux_data["keys"], children)))

    def re_repr(self):
        return f"<Jax{self.__old_repr__()[1:]}"

    options = {
        "tree_flatten": tree_flatten,
        "tree_unflatten": classmethod(tree_unflatten),
        "__repr__": re_repr,
        "__old_repr__": cls.__repr__,
    }
    return register_pytree_node_class(type(cls.__name__, (cls,), options))


class _TEST2(BaseObj):
    def __init__(self, kd, sdgs, name="TEST2"):
        super(_TEST2, self).__init__(name, kd=kd, sdgs=sdgs)

    def __call__(self, x):
        return self.kd.raw_value * x ** 2 + self.sdgs.raw_value


TEST2 = cls_converter(_TEST2)
do_test(Parameter, TEST2)

import matplotlib.pyplot as plt


class COS(BaseObj):
    def __init__(self, name, amplitude, phase, period):
        super(COS, self).__init__(name, amplitude=amplitude, phase=phase, period=period)

    def __call__(self, x):
        return self.amplitude.raw_value * np.cos(
            x / self.period.raw_value - self.phase.raw_value
        )

    def __repr__(self):
        return f"<Cosine: amp={self.amplitude.raw_value}, period={self.period.raw_value}, phase={self.phase.raw_value}>"

    @classmethod
    def from_pars(cls, amp, phase, period):
        return cls(
            "cosine",
            Parameter("amplitude", amp),
            Parameter("phase", phase),
            Parameter("period", period),
        )

    @classmethod
    def default(cls):
        return cls.from_pars(1.0, 0.0, 1.0)


cos = COS.default()
sin = vmap(grad(cos))
x = np.linspace(-np.pi, np.pi, 100000)
plt.plot(x / (2 * np.pi), cos(x), label="cos(x)")
plt.plot(x / (2 * np.pi), -sin(x), label="sin(x)")
plt.legend()
plt.show()
