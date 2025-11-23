# core/highlighter.py
import re, html

def highlight_text(pattern, text):
    """
    Given a Python regex pattern and input text, returns HTML with <mark> around matches.
    Returns a <pre>escaped_text</pre> if no matches.
    On regex compile error, returns a small HTML error message.
    """
    try:
        prog = re.compile(pattern)
    except re.error as e:
        return f"<pre>Error compiling pattern: {html.escape(str(e))}</pre>"

    matches = list(prog.finditer(text))
    if not matches:
        return "<pre>" + html.escape(text) + "</pre>"

    parts = []
    last = 0
    for m in matches:
        s, eidx = m.start(), m.end()
        parts.append(html.escape(text[last:s]))
        parts.append("<mark>" + html.escape(text[s:eidx]) + "</mark>")
        last = eidx
    parts.append(html.escape(text[last:]))
    return "<pre>" + "".join(parts) + "</pre>"

def check_full_match_per_line(pattern, text):
    """
    Returns a list of (line, accepted: bool).
    Uses ^...$ anchoring to test full-string acceptance.
    """
    try:
        prog = re.compile("^" + pattern + "$")   # force full match
    except re.error as e:
        return [("ERROR: " + str(e), False)]

    results = []
    for line in text.splitlines():
        line_stripped = line.rstrip("\n")
        accepted = bool(prog.fullmatch(line_stripped))
        results.append((line_stripped, accepted))

    return results

