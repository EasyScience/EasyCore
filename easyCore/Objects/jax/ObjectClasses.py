#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import abc
import functools
import inspect
import warnings

from easyCore.Objects.jax.Variable import BaseTree, Parameter, Descriptor, \
    PrimalValue, ParameterBase, DescriptorBase, PrimalValueBase
from jax.tree_util import register_pytree_node_class

jaxed = [Parameter, Descriptor, PrimalValue]
unjaxed = [ParameterBase, DescriptorBase, PrimalValueBase]
jax_conv = [(a, b) for a, b in zip(jaxed, unjaxed)]


def tree_flatten(self):
    children = tuple(self._kwargs.values())
    aux_data = {'name': self.name, 'keys': tuple(self._kwargs.keys())}
    return (children, aux_data)


def tree_unflatten(cls, aux_data, children):
    if 'name' in inspect.signature(cls).parameters.keys():
        return cls(name=aux_data['name'], **dict(zip(aux_data['keys'], children)))
    else:
        return cls(**dict(zip(aux_data['keys'], children)))


def new_repr(self):
    return f"<Jax{self.__base_cls__.__base_repr__(self)[1:]}"


def cls_converter(cls):
    def generate_init(fn):
        @functools.wraps(fn)
        def init(self, *args, **kwargs):
            new_args = []
            for arg in args:
                if not issubclass(arg.__class__, BaseTree):
                    warnings.warn(f"Argument {arg} is not a BaseTree")
                    is_in = [ujax for ujax in unjaxed if isinstance(arg, ujax)]
                    if is_in:
                        new_args.append(jaxed[unjaxed.index(is_in[0])](arg.name, arg.raw_value))
                    else:
                        new_args.append(arg)
                else:
                    new_args.append(arg)
            new_kwargs = {}
            for key, arg in kwargs.items():
                if not issubclass(arg.__class__, BaseTree):
                    warnings.warn(f"Argument {arg} is not a BaseTree")
                    is_in = [ujax for ujax in unjaxed if isinstance(arg, ujax)]
                    if is_in:
                        new_kwargs[key] = jaxed[unjaxed.index(is_in[0])](arg.name, arg.raw_value)
                    else:
                        new_kwargs[key] = arg
                else:
                    new_kwargs[key] = arg
            fn(self, *new_args, **new_kwargs)
            try:
                register_pytree_node_class(self.__class__)
            except ValueError:
                pass
        return init
    setattr(cls, '__base_cls__', cls)
    setattr(cls, '__init__', generate_init(cls.__init__))
    setattr(cls, 'tree_flatten', tree_flatten)
    setattr(cls, 'tree_unflatten', classmethod(tree_unflatten))
    setattr(cls, '__base_repr__', cls.__repr__)
    setattr(cls, '__repr__', new_repr)
    return cls
