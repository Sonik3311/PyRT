from dataclasses import dataclass as dt
from enum import Enum as enum_Enum
from enum import auto
from typing import Iterable, Optional

from pyrt_lexer import TokenType


@dt
class SpanPos:
    line: int
    pos: int


@dt
class Span:
    p1: SpanPos
    p2: SpanPos

    def __init__(self, l1: int, p1: int, l2: int, p2: int):
        self.p1 = SpanPos(l1, p1)
        self.p2 = SpanPos(l2, p2)


@dt
class File:
    units: list['Unit']


@dt
class Unit:
    span: Span


class Path(Unit, tuple):
    def __new__(cls, span: Span, path: Iterable[str]):
        return super(Path, cls).__new__(cls, path)

    def __init__(self, span: Span, path: Iterable[str]):
        self.span = span

    def get_beginning(self):
        # TODO: change span
        return Path(self.span, self[:-1])

    def get_last(self):
        return self[-1]

    def __repr__(self):
        return f"{self.__class__.__name__}(span={self.span}, {':'.join(self)})"

ArgType = 'NamedArgument | Expression'

@dt
class Expression(Unit):
    pass


@dt
class NamedArgument(Unit):
    name: str
    expr: Expression


@dt
class EBinary(Expression):
    expr1: Expression
    op: TokenType
    expr2: Expression

@dt
class EUnary(Expression):
    expr: Expression
    op: TokenType


@dt
class EConstant(Expression):
    path: Path
    name: str

@dt
class ECall(Expression):
    name: str
    args: list[ArgType]


class BVVector(Expression, tuple):
    def __new__(cls, values: Iterable):
        return super(BVVector, cls).__new__(cls, values)

    def __repr__(self):
        f = lambda x: float.__repr__(x) if isinstance(x, float) else "NOT NUMBER"
        return f"{self.__class__.__name__}(span={self.span}, <{', '.join(map(f, self))}>)"


class BVNumber(Expression, float):
    def __repr__(self):
        return f"{self.__class__.__name__}(span={self.span}, {float.__repr__(self)})"

@dt
class Shape(Unit):
    path: Path
    name: str
    args: list[ArgType]


@dt
class Material(Unit):
    path: Path
    name: str
    args: list[ArgType]


@dt
class Group(Unit):
    path: Path
    name: str
    args: list[ArgType]


@dt
class ConstDeclaration(Unit):
    path: Path
    name: str
    expr: Expression
