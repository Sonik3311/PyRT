from dataclasses import dataclass
from enum import Enum, auto
import re

class TokenType(Enum):
    MATERIAL = auto()
    GROUP = auto()
    CONST = auto()

    NUMBER = auto()
    WORD = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    L_BRACKET = auto()
    R_BRACKET = auto()
    COMMA = auto()
    COLON = auto()
    EQUALS = auto()

    COMMENT = auto()

    NEWLINE = auto()
    EOF = auto()


@dataclass(repr=True)
class Token:
    type: TokenType
    source: str
    span: tuple[int, int]
    line_no: int


TOKEN_TO_TOKEN_TYPE = {
    r"\(": TokenType.L_BRACKET,
    r"\)": TokenType.R_BRACKET,
    r"\,": TokenType.COMMA,
    r":": TokenType.COLON,
    r"=": TokenType.EQUALS,
    r"\+": TokenType.PLUS,
    r"-": TokenType.MINUS,
    r"\*": TokenType.STAR,
    r"/": TokenType.SLASH,

    r"#.*$": TokenType.COMMENT,
    r"-?\d+(\.\d*)?": TokenType.NUMBER,

    r"\$material": TokenType.MATERIAL,
    r"\$group": TokenType.GROUP,
    r"\$const": TokenType.CONST,
    r"[_a-zA-Z][_a-zA-Z0-9]*": TokenType.WORD,

    r"<RESERVED_NEWLINE>": TokenType.NEWLINE,
    r"<RESERVED_EOF>": TokenType.EOF,
}

TOKEN_TYPE_TO_TOKEN = {v: k for k, v in TOKEN_TO_TOKEN_TYPE.items()}

if set(TokenType) != set(TOKEN_TO_TOKEN_TYPE.values()):
    raise Exception(f"Number of token types is not the same to size of 'TOKEN_TO_TOKEN_TYPE', "
                    f"difference: {', '.join(map(str, set(TokenType).difference(TOKEN_TO_TOKEN_TYPE.values())))}")

class Lexer:
    def __init__(self):
        pattern = '|'.join(map(lambda x: f"({x})", TOKEN_TO_TOKEN_TYPE))
        #print(pattern)
        self._re = re.compile(pattern)
        self._src_lines: list[str] = []
        self._line_no = 0
        self._symbol_no = 0

    def clear(self):
        self._line_no = 0
        self._symbol_no = 0

    def set_src(self, s: str):
        self._src_lines = s.split("\n")

    @staticmethod
    def _token_to_token_type(t: str):
        if (tp := TOKEN_TO_TOKEN_TYPE.get(t)) is not None:
            return tp
        for i in TOKEN_TO_TOKEN_TYPE.keys():
            if re.match(i, t):
                return TOKEN_TO_TOKEN_TYPE[i]

    def token_iter(self):
        while True:
            yield (t := self.next_token())  # Don't remove brackets
            if t.type == TokenType.EOF:
                break

    # see token
    def see_next_token(self):
        if self._line_no >= len(self._src_lines):
            return Token(TokenType.EOF, "", (0, 0), self._line_no)
        curr_line = self._src_lines[self._line_no][self._symbol_no:]

        def do_if_empty():
            line_no = self._line_no
            sym_no = self._symbol_no

            self._line_no += 1
            self._symbol_no = 0
            return Token(TokenType.NEWLINE, "\n", (sym_no, sym_no + 1), line_no)

        if curr_line == "":
            return do_if_empty()

        while curr_line and curr_line[0] in (" ", "\t"):
            self._symbol_no += 1
            curr_line = curr_line[1:]

        if curr_line == "":
            return do_if_empty()

        result = self._re.match(curr_line)
        size = result.span()[1]

        if size == 0:
            raise ValueError(f"bad token at '{curr_line}'")

        token = result.group()
        token_type = self._token_to_token_type(token)

        r = Token(token_type, token, (self._symbol_no, self._symbol_no + size), self._line_no)

        return r

    def next_token(self):
        if self._line_no >= len(self._src_lines):
            return Token(TokenType.EOF, "", (0, 0), self._line_no)
        curr_line = self._src_lines[self._line_no][self._symbol_no:]

        def do_if_empty():
            line_no = self._line_no
            sym_no = self._symbol_no

            self._line_no += 1
            self._symbol_no = 0
            return Token(TokenType.NEWLINE, "\n", (sym_no, sym_no + 1), line_no)

        if curr_line == "":
            return do_if_empty()

        while curr_line and curr_line[0] in (" ", "\t"):
            self._symbol_no += 1
            curr_line = curr_line[1:]

        if curr_line == "":
            return do_if_empty()

        result = self._re.match(curr_line)
        size = result.span()[1]

        if size == 0:
            raise ValueError(f"bad token at '{curr_line}'")

        token = result.group()
        token_type = self._token_to_token_type(token)

        r = Token(token_type, token, (self._symbol_no, self._symbol_no + size), self._line_no)

        self._symbol_no += size
        return r