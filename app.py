# app.py
import re
from flask import Flask, render_template, request

from core.parser import Parser
from core.translator_regex import ast_to_regex
from core.highlighter import highlight_text, check_full_match_per_line

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

# Large upper bound for constraints like "n > 0"
VERY_LARGE = 10**12

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")


# -------------------------------------------------------------------
# Constraint Helpers
# -------------------------------------------------------------------

def find_vars_in_pattern(pattern):
    """Find variable names appearing in ^n or {n}, {n,}, etc."""
    vars_found = set()
    for m in re.finditer(r'\^([A-Za-z_]\w*)\b', pattern):
        vars_found.add(m.group(1))
    for m in re.finditer(r'\{([A-Za-z_]\w*)(?:[,}])', pattern):
        vars_found.add(m.group(1))
    return vars_found


def parse_constraint_line(line):
    """
    Returns (var, expr).
    Supports:
      n >= 5
      n: 1 <= n <= 5
      1 < n <= 10
      10 >= n > 2
    """
    if not line:
        return None, None

    line = line.strip()

    if ":" in line:
        var, expr = line.split(":", 1)
        return var.strip(), expr.strip()

    m = re.search(r'\b([A-Za-z_]\w*)\b', line)
    if not m:
        return None, None
    return m.group(1), line


def to_int(x):
    try:
        return int(x)
    except:
        return None


# ---------------------------
# Interpret Bound Helpers
# ---------------------------

def interpret_left_number_op_var(A, op):
    """A op var  → returns (lower_bound, upper_bound)."""
    if op == "<=":
        return A, None  # var >= A
    if op == "<":
        return A + 1, None
    if op == ">=":
        return None, A  # var <= A
    if op == ">":
        return None, A - 1
    raise ValueError(f"Unknown operator {op}")


def interpret_var_op_right_number(op, B):
    """var op B → returns (lower_bound, upper_bound)."""
    if op == "<=":
        return None, B
    if op == "<":
        return None, B - 1
    if op == ">=":
        return B, None
    if op == ">":
        return B + 1, None
    raise ValueError(f"Unknown operator {op}")


# ---------------------------
# Parse Single Constraint
# ---------------------------

def resolve_single_constraint(expr, var):
    """
    Return (lower, upper) bounds for variable.
    Supports:
      1 <= n <= 3
      10 > n > 1
      n >= 5
      2 < n
      n = 4
      5 == n
    """
    s = expr.strip()

    # Three-part chain: NUMBER op var op NUMBER
    chain = re.compile(
        rf'^\s*(\d+)\s*(<=|<|>=|>)\s*{var}\s*(<=|<|>=|>)\s*(\d+)\s*$'
    )
    m = chain.match(s)
    if m:
        A, op1, op2, B = m.groups()
        A = int(A); B = int(B)
        lo1, hi1 = interpret_left_number_op_var(A, op1)
        lo2, hi2 = interpret_var_op_right_number(op2, B)

        lowers = [x for x in (lo1, lo2) if x is not None]
        uppers = [x for x in (hi1, hi2) if x is not None]

        lower = max(lowers) if lowers else None
        upper = min(uppers) if uppers else None

        if lower is not None and upper is not None and lower > upper:
            raise ValueError(f"No integer satisfies {expr}")
        return lower, upper

    # Two-part constraints
    two = re.compile(r'^\s*([A-Za-z_]\w*|\d+)\s*(<=|<|>=|>|==|=)\s*([A-Za-z_]\w*|\d+)\s*$')
    m = two.match(s)
    if m:
        L, op, R = m.groups()
        if op == "=":
            op = "=="

        # var OP num
        if L == var and to_int(R) is not None:
            Rv = int(R)
            if op == "==": return Rv, Rv
            if op == ">=": return Rv, None
            if op == ">": return Rv + 1, None
            if op == "<=": return None, Rv
            if op == "<": return None, Rv - 1

        # num OP var
        if R == var and to_int(L) is not None:
            Lv = int(L)
            if op == "==": return Lv, Lv
            if op == "<=": return Lv, None
            if op == "<": return Lv + 1, None
            if op == ">=": return None, Lv
            if op == ">": return None, Lv - 1

    # equality fallback
    m = re.search(rf'\b{var}\s*(==|=)\s*(\d+)\b', s)
    if m:
        val = int(m.group(2))
        return val, val
    m = re.search(rf'\b(\d+)\s*(==|=)\s*{var}\b', s)
    if m:
        val = int(m.group(1))
        return val, val

    raise ValueError(f"Cannot parse constraint '{expr}' for variable '{var}'")


# ---------------------------
# Combine constraints
# ---------------------------

def resolve_constraints(constraints_text, pattern):
    """
    Produces var -> (lower, upper) bounds.
    Missing upper bounds become VERY_LARGE.
    Missing lower bounds → default 0.
    """
    vars_needed = find_vars_in_pattern(pattern)
    bounds = {v: {"lower": None, "upper": None} for v in vars_needed}

    # Read each line
    if constraints_text:
        for raw in constraints_text.splitlines():
            line = raw.strip()
            if not line:
                continue

            var, expr = parse_constraint_line(line)
            if not var or not expr:
                raise ValueError(f"Invalid constraint line '{line}'")

            # Allow constraints for variables that don't appear in the pattern
            if var not in bounds:
                bounds[var] = {"lower": None, "upper": None}

            lo, up = resolve_single_constraint(expr, var)

            # Combine with existing bounds
            if lo is not None:
                if bounds[var]["lower"] is None:
                    bounds[var]["lower"] = lo
                else:
                    bounds[var]["lower"] = max(bounds[var]["lower"], lo)

            if up is not None:
                if bounds[var]["upper"] is None:
                    bounds[var]["upper"] = up
                else:
                    bounds[var]["upper"] = min(bounds[var]["upper"], up)

    # Finalize each variable to (lo, up) with defaults
    var_bounds = {}
    for var, b in bounds.items():
        lo = b["lower"]
        up = b["upper"]

        # Default lower bound is 0
        if lo is None:
            lo = 0

        # If no upper bound → VERY_LARGE
        if up is None:
            up = VERY_LARGE

        if lo > up:
            raise ValueError(f"Contradictory constraints for '{var}'")

        var_bounds[var] = (lo, up)

    return var_bounds


# ---------------------------
# Substitute resolved vars into pattern (produce brace quantifiers)
# ---------------------------

def substitute_vars(pattern, var_bounds):
    """
    Replace ^var and {var} and {var, ...} occurrences with:
      - {lo,}   when up >= VERY_LARGE (open-ended)
      - {lo}    when lo == up
      - {lo,up} otherwise
    """
    out = pattern
    for var, (lo, up) in var_bounds.items():
        if up >= VERY_LARGE:
            repl = "{" + str(lo) + "," + "}"
        elif lo == up:
            repl = "{" + str(lo) + "}"
        else:
            repl = "{" + str(lo) + "," + str(up) + "}"

        # ^var -> {lo,}  (we intentionally replace the exponent syntax with brace quantifier)
        out = re.sub(r'\^' + re.escape(var) + r'\b', repl, out)
        # {var} -> {lo} or {lo,} etc.
        out = re.sub(r'\{' + re.escape(var) + r'\}', repl, out)
        # {var,  (start of existing brace) -> {lo,
        out = re.sub(r'\{' + re.escape(var) + r',', '{' + str(lo) + ',', out)

    return out


# -------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html",
                           translated=None,
                           highlighted=None,
                           error=None,
                           pattern="",
                           text="",
                           constraints="",
                           accepted=[]
                           )


@app.route("/run", methods=["POST"])
def run():
    pattern = request.form.get("pattern", "")
    text = request.form.get("text", "")
    constraints = request.form.get("constraints", "")

    accepted = []

    try:
        # Resolve numeric bounds for symbolic exponents
        var_bounds = resolve_constraints(constraints, pattern)
        parsed_pattern = substitute_vars(pattern, var_bounds)

        # Parse educational RE
        ast = Parser(parsed_pattern).parse()

        # Translate to Python regex
        py_regex = ast_to_regex(ast)

        # Highlight and accept-check
        highlighted = highlight_text(py_regex, text)
        accepted = check_full_match_per_line(py_regex, text)

        return render_template(
            "index.html",
            translated=py_regex,
            highlighted=highlighted,
            error=None,
            pattern=pattern,
            text=text,
            constraints=constraints,
            accepted=accepted
        )

    except Exception as e:
        return render_template(
            "index.html",
            translated=None,
            highlighted=None,
            error=str(e),
            pattern=pattern,
            text=text,
            constraints=constraints,
            accepted=accepted
        )


if __name__ == "__main__":
    app.run(debug=True)

