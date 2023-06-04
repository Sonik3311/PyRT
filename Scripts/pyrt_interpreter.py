from pyrt_ast_nodes import *
from util import VectorN


class Interpreter:
    def __init__(self):
        self.env_functions = {}
        # first 3 params: line, parent_group, name are required
        self.shape_handler = None
        # group and material handlers must return group/material
        self.group_handler = None
        self.material_handler = None
        self.constants = {}

    def _clear(self):
        self.constants = {}

    @staticmethod
    def to_func_params(args: list[NamedArgument | Expression]) -> (list, dict):
        a = []
        kwa = {}
        for i in args:
            if isinstance(i, NamedArgument):
                kwa[i.name] = i.expr
            else:
                a.append(i)
        return a, kwa

    @staticmethod
    def get_const_name(c: EConstant | ConstDeclaration | Material | Group):
        return ':'.join([i for i in c.path] + [c.name])

    class Switcher(object):
        @classmethod
        def BVVector(cls, i, v):
            vls = cls.eval_list(i, v)
            assert all(map(lambda x: isinstance(x, float), vls))
            return VectorN(vls)

        @classmethod
        def BVNumber(cls, i, n):
            return float(n)

        @classmethod
        def EUnary(cls, i, e: EUnary):
            match e.op:
                case TokenType.MINUS:
                    return -cls.eval(i, e.expr)
                case _:
                    raise NotImplementedError

        @classmethod
        def EBinary(cls, i, e: EBinary):
            match e.op:
                case TokenType.PLUS:
                    return cls.eval(i, e.expr1) + cls.eval(i, e.expr2)
                case TokenType.MINUS:
                    return cls.eval(i, e.expr1) - cls.eval(i, e.expr2)
                case TokenType.STAR:
                    return cls.eval(i, e.expr1) * cls.eval(i, e.expr2)
                case TokenType.SLASH:
                    return cls.eval(i, e.expr1) / cls.eval(i, e.expr2)
                case _:
                    raise NotImplementedError

        @classmethod
        def EConstant(cls, i: 'Interpreter', e: EConstant):
            return i.constants[i.get_const_name(e)]

        @classmethod
        def ECall(cls, i: 'Interpreter', e: ECall):
            args, kwargs = Interpreter.to_func_params(e.args)
            args, kwargs = cls.eval_list(i, args), cls.eval_dict(i, kwargs)

            return i.env_functions[e.name](*args, **kwargs)

        @classmethod
        def Shape(cls, i: 'Interpreter', u: Shape):
            args, kwargs = Interpreter.to_func_params(u.args)
            args, kwargs = cls.eval_list(i, args), cls.eval_dict(i, kwargs)
            i.shape_handler(u.span.p1.line, tuple(u.path), u.name, *args, **kwargs)

        @classmethod
        def Group(cls, i: 'Interpreter', g: Group):
            args, kwargs = Interpreter.to_func_params(g.args)
            args, kwargs = cls.eval_list(i, args), cls.eval_dict(i, kwargs)

            parent_name = ':'.join(g.path)
            parent = i.constants[parent_name] if parent_name else None

            name = i.get_const_name(g)
            group = i.group_handler(g.span.p1.line, parent, g.name, *args, **kwargs)
            if name in i.constants:
                raise Exception(f"group '{name}' redefinition")
            else:
                i.constants[name] = group

        @classmethod
        def Material(cls, i: 'Interpreter', m: Material):
            args, kwargs = Interpreter.to_func_params(m.args)
            args, kwargs = cls.eval_list(i, args), cls.eval_dict(i, kwargs)

            parent_name = ':'.join(m.path)
            parent = i.constants[parent_name] if parent_name else None

            name = i.get_const_name(m)
            material = i.material_handler(m.span.p1.line, parent, m.name, *args, **kwargs)
            if name in i.constants:
                raise Exception(f"material '{name}' redefinition")
            else:
                i.constants[name] = material


        @classmethod
        def ConstDeclaration(cls, i: 'Interpreter', c: ConstDeclaration):
            name = i.get_const_name(c)
            if name in i.constants:
                raise Exception(f"constant '{name}' redefinition")
            else:
                i.constants[name] = cls.eval(i, c.expr)

        @classmethod
        def do(cls, i: 'Interpreter', unit: Unit):
            getattr(cls, unit.__class__.__name__)(i, unit)

        @classmethod
        def eval(cls, i: 'Interpreter', expr: Expression):
            return getattr(cls, expr.__class__.__name__)(i, expr)

        @classmethod
        def eval_list(cls, i: 'Interpreter', l: list[Expression]):
            return [cls.eval(i, e) for e in l]

        @classmethod
        def eval_dict(cls, i: 'Interpreter', d: dict[str, Expression]):
            return {k: cls.eval(i, d[k]) for k in d}

    def interpret(self, f: File):
        self._clear()
        do = Interpreter.Switcher.do
        for u in f.units:
            do(self, u)
