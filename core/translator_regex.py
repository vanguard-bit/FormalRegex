# core/translator_regex.py
import re
from .ast_nodes import Symbol, Concat, Union, Repeat, Group

def ast_to_regex(node):
    """
    Convert AST (from core/parser.py) into a Python-style regex string.
    - uses non-capturing groups (?:...) where grouping is needed.
    - optimizes simple unions of single characters into character classes like [ab].
    """
    if isinstance(node, Symbol):
        if node.value == "":
            return ""
        return re.escape(node.value)

    if isinstance(node, Group):
        return "(?:" + ast_to_regex(node.node) + ")"

    if isinstance(node, Concat):
        return "".join(ast_to_regex(p) for p in node.parts)

    if isinstance(node, Union):
        # if all options are single Symbols → character class
        simple = True
        chars = []
        for opt in node.options:
            if isinstance(opt, Symbol) and len(opt.value) == 1:
                chars.append(opt.value)
            else:
                simple = False
                break
        if simple and chars:
            esc = "".join(re.escape(c) for c in chars)
            return f"[{esc}]"
        parts = [ast_to_regex(opt) for opt in node.options]
        return "(?:" + "|".join(parts) + ")"

    if isinstance(node, Repeat):
        inner = ast_to_regex(node.node)
        needs_group = not isinstance(node.node, Symbol)
        if needs_group and not (inner.startswith("(?:") and inner.endswith(")")):
            inner = f"(?:{inner})"
        # common quantifiers
        if node.min == 0 and node.max is None:
            return inner + "*"
        if node.min == 1 and node.max is None:
            return inner + "+"
        if node.min == 0 and node.max == 1:
            return inner + "?"
        if node.min is not None and node.max is not None and node.min == node.max:
            return inner + "{" + str(node.min) + "}"
        if node.min is not None and node.max is None:
            return inner + "{" + str(node.min) + ",}"
        if node.min is not None and node.max is not None:
            return inner + "{" + str(node.min) + "," + str(node.max) + "}"
        return inner

    raise ValueError("Unhandled AST node type: " + str(type(node)))

