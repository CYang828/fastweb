# coding:utf8

"""
A parser for Thrift IDL files.

Parser
------

Adapted from ``thriftpy.parser``.

.. autoclass:: Parser
    :members:

AST
---

.. autoclass:: Program

Headers
~~~~~~~

.. autoclass:: Include

.. autoclass:: Namespace

Definitions
~~~~~~~~~~~

.. autoclass:: Const

.. autoclass:: Typedef

.. autoclass:: Enum

.. autoclass:: EnumItem

.. autoclass:: Struct

.. autoclass:: Union

.. autoclass:: Exc

.. autoclass:: Service

.. autoclass:: ServiceReference

.. autoclass:: Function

.. autoclass:: Field

Types
~~~~~

.. autoclass:: PrimitiveType

.. autoclass:: MapType

.. autoclass:: SetType

.. autoclass:: ListType

.. autoclass:: DefinedType

Constants
~~~~~~~~~

.. autoclass:: ConstPrimitiveValue

.. autoclass:: ConstReference

Annotations
~~~~~~~~~~~

.. autoclass:: Annotation
"""
from __future__ import absolute_import, unicode_literals, print_function

from fastweb.spec.idl.parser import Parser
from fastweb.spec.idl.ast import (
    Program,
    Include,
    Namespace,
    Const,
    Typedef,
    Enum,
    EnumItem,
    Struct,
    Union,
    Exc,
    Service,
    ServiceReference,
    Function,
    Field,
    PrimitiveType,
    MapType,
    SetType,
    ListType,
    DefinedType,
    ConstValue,
    ConstPrimitiveValue,
    ConstReference,
    Annotation,
)


__all__ = [
    # Parser
    'Parser',

    # AST
    'Program',
    'Include',
    'Namespace',
    'Const',
    'Typedef',
    'Enum',
    'EnumItem',
    'Struct',
    'Union',
    'Exc',
    'Service',
    'ServiceReference',
    'Function',
    'Field',
    'PrimitiveType',
    'MapType',
    'SetType',
    'ListType',
    'DefinedType',
    'ConstValue',
    'ConstPrimitiveValue',
    'ConstReference',
    'Annotation',
]
