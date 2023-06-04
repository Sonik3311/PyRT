from dataclasses import dataclass
from typing import Optional

from pyrt_ast_nodes import *
from pyrt_errors_db import *
from pyrt_lexer import Lexer, Token, TokenType

GLOBAL_GROUP_NAME = 'World'

PRIORITIES = {
    TokenType.PLUS: 10,
    TokenType.MINUS: 10,
    TokenType.STAR: 20,
    TokenType.SLASH: 20,
}

class Parser:
    def __init__(self):
        self._lexer: Optional[Lexer] = None
        self._prev_token: Optional[Token] = None
        self._current_token: Optional[Token] = None
        self.errors = []

    @dataclass
    class Error:
        msg: str
        pos: SpanPos

        def __repr__(self):
            return f"{self.msg} at {self.pos.line+1}:{self.pos.pos}"

    def _err(self, msg):
        c = self.current()
        return self.Error(msg, SpanPos(c.line_no, c.span[0]))

    def push_error(self, e: Error):
        self.errors.append(e)
        print("parser error:", e)

    def clear(self):
        if self._lexer:
            self._lexer.clear()
        self._prev_token = None
        self._current_token = None
        self.errors = []

    def set_lexer(self, l: Lexer):
        self._lexer = l

    def parse(self) -> File | None:
        self.clear()
        self.advance()
        units = self.parse_body()
        if self.errors:
            return None
        return File(units)

    def current(self):
        return self._current_token

    def prev(self):
        return self._prev_token

    #def next(self):
    #    return self._lexer.see_next_token()

    def skip_to_next_line(self):
        while not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
            self.advance()
        self.flt_advance()

    def advance(self):
        self._prev_token = self._current_token
        self._current_token = self._lexer.next_token()
        #print(f"parser advanced: {self._current_token}")
        return self._current_token

    def flt_advance(self):
        self.advance()
        while self.check(TokenType.NEWLINE):
            self.advance()

    def check(self, t: TokenType):
        return self.current().type == t

    def match(self, t: TokenType):
        if self.check(t):
            self.advance()
            return True
        return False

    def flt_match(self, t: TokenType):
        if self.check(t):
            self.flt_advance()
            return True
        return False

    def consume(self, t: TokenType, e: Error):
        if self.match(t):
            return True
        self.push_error(e)
        return False

    def flt_consume(self, t: TokenType, e: Error):
        if self.flt_match(t):
            return True
        self.push_error(e)
        return False

    def parse_body(self) -> list[Unit]:
        r = []
        while not self.check(TokenType.EOF):
            if res := self.parse_line():
                r.append(res)
        return r

    def parse_line(self):
        if self.check(TokenType.COMMENT):
            self.advance()
            self.consume(TokenType.NEWLINE, self._err("error cannot be here"))
            return

        if self.check(TokenType.NEWLINE):
            self.advance()
            return

        if self.match(TokenType.MATERIAL):
            return self.parse_r_gmf(Material)
        elif self.match(TokenType.GROUP):
            return self.parse_r_gmf(Group)
        elif self.match(TokenType.CONST):
            return self.parse_r_const()
        elif self.check(TokenType.WORD):
            return self.parse_shape()
        else:
            self.push_error(self._err("wrong token type"))
            self.skip_to_next_line()

    def parse_r_gmf(self, f):
        st = self.prev()
        path = self.parse_path()
        exprs = self.parse_brackets_with_args()
        if path is None or exprs is None:
            return None

        bracket_tok = self.prev()
        span = Span(st.line_no, st.span[0], bracket_tok.line_no, bracket_tok.span[1])
        self.consume(TokenType.NEWLINE, self._err(ERR_EXPECTED_NEWLINE))
        return f(span, path.get_beginning(), path.get_last(), exprs)

    def parse_r_const(self):
        st = self.prev()
        path = self.parse_path()
        if path is None:
            return None
        if not self.consume(TokenType.EQUALS, self._err(ERR_EXPECTED_EQUALS)):
            return None
        expr = self.parse_expression()
        if expr is None:
            return None
        self.consume(TokenType.NEWLINE, self._err(ERR_EXPECTED_NEWLINE))
        span = Span(st.line_no, st.span[0], expr.span.p2.line, expr.span.p2.pos)
        return ConstDeclaration(span, path.get_beginning(), path.get_last(), expr)

    def parse_shape(self):
        path = self.parse_path()
        exprs = self.parse_brackets_with_args()
        if path is None and exprs is None:
            return None

        bracket_tok = self.prev()
        span = Span(path.span.p1.line, path.span.p1.pos, bracket_tok.line_no, bracket_tok.span[1])
        self.consume(TokenType.NEWLINE, self._err(ERR_EXPECTED_NEWLINE))
        return Shape(span, path.get_beginning(), path.get_last(), exprs)

    def parse_path(self) -> Path | None:
        st_tok = self.current()
        l = [st_tok.source]
        self.advance()

        e_tok = st_tok
        while self.match(TokenType.COLON):
            if not self.check(TokenType.WORD):
                self.push_error(self._err(ERR_BAD_GROUP_NAME))
                return None
            e_tok = self.current()
            l.append(e_tok.source)
            self.advance()

        span = Span(st_tok.line_no, st_tok.span[0], e_tok.line_no, e_tok.span[1])
        gp = Path(span, l)
        return gp

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE):
            pass

    def parse_brackets_with_args(self):
        if not self.consume(TokenType.L_BRACKET, self._err(ERR_EXPECTED_L_BRACKET)):
            return None

        self.skip_newlines()

        if self.match(TokenType.R_BRACKET):
            return []

        e = self.parse_argument()
        if e is None:
            return None
        exprs = [e]
        while self.match(TokenType.COMMA):
            self.skip_newlines()
            if self.check(TokenType.R_BRACKET):
                break
            exprs.append(self.parse_argument())

        self.skip_newlines()

        if not self.consume(TokenType.R_BRACKET, self._err(ERR_EXPECTED_R_BRACKET)):
            return None

        return exprs

    def parse_argument(self):
        if self.check(TokenType.WORD):
            p = self.parse_path()
            if self.match(TokenType.EQUALS):
                if len(p) > 1:
                    self.push_error(self._err(ERR_EXPECTED_EQUALS))
                    return None
                name = p[0]
                expr = self.parse_expression()
                if expr is None:
                    return
                s = Span(p.span.p1.line, p.span.p1.pos, expr.span.p2.line, expr.span.p2.pos)
                n = NamedArgument(s, name, expr)
                return n
            else:
                return EConstant(p.span, p.get_beginning(), p.get_last())
        else:
            return self.parse_expression()

    def parse_single_expression(self):
        if self.match(TokenType.MINUS):
            unary_tok = self.prev()
            expr = self.parse_single_expression()
            span = Span(unary_tok.line_no, unary_tok.span[0], expr.span.p2.line, expr.span.p2.pos)
            return EUnary(span, expr, unary_tok.type)
        if self.check(TokenType.NUMBER):
            return self.parse_number()
        if self.match(TokenType.L_BRACKET):
            return self.parse_r_vector_or_brackets()
        if self.check(TokenType.WORD):
            return self.parse_constant_or_call()

        self.push_error(self._err(ERR_UNEXPECTED_TOKEN + " " + str(self.current().type)))
        #raise NotImplementedError(self.current())

    def parse_expression(self):
        TOKS = (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH)
        expr_stack: list[Expression] = []
        op_stack = []

        def make_binary(expr):
            last = expr_stack[-1]
            op = op_stack.pop(-1)
            span = Span(last.span.p1.line, last.span.p1.pos, last.span.p2.line, last.span.p2.pos)
            expr_stack[-1] = EBinary(span, last, op, expr)

        while True:
            e = self.parse_single_expression()
            if e is None:
                return None
            tok = self.current()
            if tok.type not in TOKS:
                expr_stack.append(e)
                break

            if op_stack and PRIORITIES[op_stack[-1]] >= PRIORITIES[tok.type]: # if right assoc change >= to >
                make_binary(e)
            else:
                expr_stack.append(e)

            op_stack.append(tok.type)
            self.advance()

        while op_stack:
            make_binary(expr_stack.pop(-1))

        return expr_stack[-1]

    def parse_r_vector_or_brackets(self):
        l_bracket = self.prev()
        v = self.parse_expression()
        if v is None:
            return None
        nums = [v]
        while self.flt_match(TokenType.COMMA):
            if (n := self.parse_expression()) is not None:
                nums.append(n)
            else:
                return None

        if not self.consume(TokenType.R_BRACKET, self._err(ERR_EXPECTED_R_BRACKET)):
            return None

        if len(nums) == 1:
            return nums[0]

        r_bracket = self.prev()
        v = BVVector(nums)
        v.span = Span(l_bracket.line_no, l_bracket.span[0], r_bracket.line_no, r_bracket.span[1])

        return v

    def parse_number(self):
        if not self.check(TokenType.NUMBER):
            self.push_error(self._err(ERR_EXPECTED_NUMBER))
            return None
        t = self.current()
        n = BVNumber(t.source)
        n.span = Span(t.line_no, t.span[0], t.line_no, t.span[1])
        self.advance()
        return n

    def parse_constant_or_call(self):
        path = self.parse_path()
        if self.check(TokenType.L_BRACKET):
            if len(path) > 1:
                self.push_error(self._err(ERR_UNEXPECTED_TOKEN))
            args = self.parse_brackets_with_args()
            bracket_tok = self.prev()
            span = Span(path.span.p1.line, path.span.p1.pos, bracket_tok.line_no, bracket_tok.span[1])
            return ECall(span, path[0], args)
        return EConstant(path.span, path.get_beginning(), path.get_last())