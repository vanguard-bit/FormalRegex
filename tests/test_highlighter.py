# tests/test_highlighter.py
from core.highlighter import highlight_text
from core.parser import Parser
from core.translator_regex import ast_to_regex


def test_highlight_basic():
    pat = "(a+b)*abb"
    ast = Parser(pat).parse()
    preg = ast_to_regex(ast)
    out = highlight_text(preg, "xabb aababb ababb")
    assert "<mark>" in out
