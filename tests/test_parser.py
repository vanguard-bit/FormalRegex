# tests/test_parser.py
from core.parser import Parser

def test_simple_symbols():
    assert repr(Parser("a").parse()) == "Symbol('a')"

def test_concat_and_union():
    assert "Concat" in repr(Parser("ab").parse())
    assert "Union" in repr(Parser("a+b").parse())

def test_group_and_repeat():
    assert "Repeat" in repr(Parser("(a+b)*").parse())

def test_exponent_basic():
    ast = Parser("(a+b)^5").parse()
    assert "Repeat" in repr(ast)

def test_exponent_symbol():
    ast = Parser("a^3").parse()
    assert "min=3" in repr(ast)

def test_exponent_concat():
    ast = Parser("(ab)^4").parse()
    assert "4" in repr(ast)

