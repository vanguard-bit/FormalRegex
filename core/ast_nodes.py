# core/ast_nodes.py
class RegexNode: pass

class Symbol(RegexNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Symbol({self.value!r})"

class Concat(RegexNode):
    def __init__(self, parts):
        self.parts = parts
    def __repr__(self):
        return f"Concat({self.parts})"

class Union(RegexNode):
    def __init__(self, options):
        self.options = options
    def __repr__(self):
        return f"Union({self.options})"

class Repeat(RegexNode):
    def __init__(self, node, minrep, maxrep):
        self.node = node
        self.min = minrep
        self.max = maxrep
    def __repr__(self):
        return f"Repeat(node={self.node}, min={self.min}, max={self.max})"

class Group(RegexNode):
    def __init__(self, node):
        self.node = node
    def __repr__(self):
        return f"Group({self.node})"

