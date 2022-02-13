#  SPDX-FileCopyrightText: 2022 easyCore contributors  <core@easyscience.software>
#  SPDX-License-Identifier: BSD-3-Clause
#  © 2021-2022 Contributors to the easyCore project <https://github.com/easyScience/easyCore>

from __future__ import annotations

__author__ = "github.com/wardsimon"
__version__ = "0.1.0"

from jax.tree_util import register_pytree_node_class
from typing import (
    List,
    Union,
    Any,
    Iterable,
    Dict,
    Optional,
    Type,
    TYPE_CHECKING,
    Callable, Tuple,
)
from ..Variable import PrimalValue as PrimalValueBase, Descriptor as DescriptorBase, Parameter as ParameterBase


class BaseTree:
    def tree_flatten(self):
        children = (self.raw_value,)
        aux_data = {"name": self.name}
        return (children, aux_data)

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        return cls(aux_data['name'], *children)


@register_pytree_node_class
class PrimalValue(PrimalValueBase, BaseTree):
    def __repr__(self) -> str:
        s = super(PrimalValueBase, self).__repr__()
        return "<Jax" + s[1:]


@register_pytree_node_class
class Descriptor(DescriptorBase, BaseTree):
    def __repr__(self) -> str:
        s = super(DescriptorBase, self).__repr__()
        return "<Jax" + s[1:]


@register_pytree_node_class
class Parameter(ParameterBase, BaseTree):
    def __repr__(self) -> str:
        s = super(ParameterBase, self).__repr__()
        return "<Jax" + s[1:]
