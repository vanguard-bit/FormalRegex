# tests/test_translator.py
from core.parser import Parser
from core.translator_regex import ast_to_regex
import re


def compile_pattern(pat):
    ast = Parser(pat).parse()
    preg = ast_to_regex(ast)
    # ensure it compiles in Python's re
    re.compile(preg)


def test_compile_examples():
    examples = ["a", "ab", "a+b", "(a+b)*", "a{2,4}", "(ab){3}", "(a+b){2,4}"]
    for e in examples:
        compile_pattern(e)
