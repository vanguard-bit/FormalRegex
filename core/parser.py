# core/parser.py
from .ast_nodes import Symbol, Concat, Union, Repeat, Group


class Parser:
    """
    Recursive-descent parser for the formal RE grammar:
      Expr     := Term ('+' Term)*
      Term     := Factor*
      Factor   := Base ( '*' | '+' | '?' | '{m}', '{m,n}', '{m,}' )*
      Base     := SYMBOL | '(' Expr ')'
    Notes:
      - '+' used as union (infix) AND as postfix quantifier (like regex) — parser
        disambiguates: postfix '+' is only accepted when it is truly postfix.
      - Symbols are single alphanumeric characters and a few punctuation (._-).
    """

    def __init__(self, text: str):
        self.text = text.replace(" ", "")
        self.i = 0

    def peek(self):
        return self.text[self.i] if self.i < len(self.text) else None

    def consume(self, ch=None):
        if self.i >= len(self.text):
            raise ValueError("Unexpected end")
        c = self.text[self.i]
        if ch and c != ch:
            raise ValueError(f"Expected {ch!r} got {c!r} at {self.i}")
        self.i += 1
        return c

    def parse(self):
        node = self.parse_expr()
        if self.peek() is not None:
            raise ValueError(f"Trailing characters at {self.i}: {self.text[self.i :]}")
        return node

    def parse_expr(self):
        terms = [self.parse_term()]
        while self.peek() == "+":
            self.consume("+")
            terms.append(self.parse_term())
        return terms[0] if len(terms) == 1 else Union(terms)

    def parse_term(self):
        parts = []
        while True:
            c = self.peek()
            if c and c not in ")+":
                parts.append(self.parse_factor())
            else:
                break
        if not parts:
            return Symbol("")
        return parts[0] if len(parts) == 1 else Concat(parts)

    def parse_factor(self):
        # First parse the base expression
        node = self.parse_base()

        if self.peek() == "^":
            self.consume("^")
            num = self.parse_number()
            node = Repeat(node, num, num)
        while True:
            c = self.peek()
            if c == "*":
                self.consume("*")
                node = Repeat(node, 0, None)
            elif c == "?":
                self.consume("?")
                node = Repeat(node, 0, 1)
            elif c == "{":
                node = self.parse_braces(node)
            elif c == "+":
                nxt = self.text[self.i + 1] if self.i + 1 < len(self.text) else None
                if nxt and (nxt.isalnum() or nxt == "("):
                    break
                self.consume("+")
                node = Repeat(node, 1, None)
            else:
                break

        return node

    def parse_base(self):
        c = self.peek()
        if c is None:
            raise ValueError("Unexpected end in base")
        if c == "(":
            self.consume("(")
            inner = self.parse_expr()
            if self.peek() != ")":
                raise ValueError("Expected ')'")
            self.consume(")")
            return Group(inner)
        if c.isalnum() or c in "._-":
            self.consume()
            return Symbol(c)
        raise ValueError(f"Unexpected character in base: {c!r} at {self.i}")

    def parse_braces(self, node):
        # handles {m} or {m,n} or {m,}
        self.consume("{")
        num = self.parse_number()
        minrep = num
        maxrep = num
        if self.peek() == ",":
            self.consume(",")
            if self.peek() == "}":
                maxrep = None
            else:
                maxrep = self.parse_number()
        if self.peek() != "}":
            raise ValueError("Expected '}'")
        self.consume("}")
        return Repeat(node, minrep, maxrep)

    def parse_number(self):
        start = self.i
        if not (self.peek() and self.peek().isdigit()):
            raise ValueError("Expected number")
        while self.peek() and self.peek().isdigit():
            self.consume()
        return int(self.text[start : self.i])
