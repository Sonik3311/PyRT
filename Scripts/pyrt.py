from math import pi
from typing import Callable

from pyrt_interpreter import Interpreter
from pyrt_lexer import Lexer
from pyrt_parser import Parser
from util import VectorN


class PYRTManager:
    def __init__(self, shape_handler, group_handler, material_handler):
        self.parser = Parser()
        self.interpreter = Interpreter()
        self.interpreter.shape_handler = shape_handler
        self.interpreter.group_handler = group_handler
        self.interpreter.material_handler = material_handler

        self.interpreter.env_functions = {
            "deg2rad": lambda x: x / 180 * pi,
        }

    def readFile(self, file):
        lexer = Lexer()
        try:
            with open(file, 'r') as file:
                lexer.set_src(file.read())
        except FileNotFoundError:
            assert "FileNotFound", "FileNotFound"
        
        self.parser.set_lexer(lexer)
        parsed = self.parser.parse()
        self.interpreter.interpret(parsed)
        self.parser.clear()

a = 1
b = a or 0
print(b)