
---

# 📘 **Educational Regular Expression Translator & Tester**

A web-based tool that converts **educational (TOC-style) regular expressions** into **real Python regex**, applies them to text, highlights matches, and checks whether each input string is **fully accepted** by the regular language.

This project bridges the gap between **Automata Theory** and **real-world Regex engines**.

---

## ⭐ Features

### ✔ **Educational Regex Parsing (TOC-style grammar)**

Supports classical formal-language syntax:

```
a
ab
(a + b)
(a + b)*abb
(a + b)^5
(a + b){3,5}
```

### ✔ **Fully custom recursive-descent parser**

Implements a grammar based on Theory of Computation:

```
Expr   → Term ('+' Term)*
Term   → Factor*
Factor → Base Quantifier*
Base   → SYMBOL | '(' Expr ')'
Quantifier → * | + | ? | {m} | {m,n} | ^n
```

### ✔ **AST construction**

Each expression is parsed into an **Abstract Syntax Tree** with nodes:

* `Symbol`
* `Concat`
* `Union`
* `Repeat`
* `Group`

### ✔ **Python-regex Translator**

The AST is converted into a real Python regex string:

| Educational RE | Python Regex   |
| -------------- | -------------- |
| `(a + b)^5`    | `(?:[ab]){5}`  |
| `(a+b)*abb`    | `(?:[ab])*abb` |
| `a{2,4}`       | `a{2,4}`       |

### ✔ **Substring Highlighting (regex101-style)**

Matches are highlighted inside your input text.

### ✔ **Line-wise Acceptance Checking**

Shows whether **each line** of input is fully accepted:

```
abc    → ACCEPTED
abb    → REJECTED
bbaa   → ACCEPTED
```

### ✔ **Flask Web Interface**

Simple front-end for testing REs and visualizing matches.

---

## 📂 Project Structure

```
project_root/
│
├── app.py
├── requirements.txt
│
├── core/
│   ├── __init__.py
│   ├── parser.py
│   ├── ast_nodes.py
│   ├── translator_regex.py
│   └── highlighter.py
│
├── web/
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   │   ├── style.css
│   │   └── script.js
│
└── tests/
    ├── test_parser.py
    ├── test_translator.py
    └── test_highlighter.py
```

---

## 🚀 Installation

### 1. Clone the repo

```
git clone <your_repo_url>
cd project_root
```

### 2. Create a virtual environment

```
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Run tests (optional)

```
pytest
```

### 5. Start the server

```
python app.py
```

Open your browser at:

```
http://127.0.0.1:5000
```

---

## 🧪 Example Inputs

### Pattern:

```
(a + b)*abb
```

### Text:

```
xabb
aababb
ababb
hello
```

### Output:

* Highlighted matches
* Accepted/rejected list

---

---

# 📚 Background & Motivation

Regular Expressions (RE) play a crucial role in both **theory** and **practice**, but the two worlds look very different.
This project is designed to bridge that gap.

---

## 🔍 **1. Real-World Applications of Regular Expressions**

In practical computing, regex engines are used everywhere:

### **✔ Log Analysis**

* Extract IP addresses
* Detect suspicious patterns
* Filter error messages

### **✔ Input Validation**

* Email & phone number validation
* Password rules
* Username & ID formats

### **✔ Web Scraping & Text Mining**

* Extract URLs
* Extract product codes
* Detect currency values or dates

### **✔ Data Cleaning**

* Remove unwanted characters
* Normalize whitespace
* Extract structured data

### **✔ Programming Tools**

* Code search and refactoring
* Syntax highlighting
* IDE find/replace with patterns

### **✔ Security and Malware Detection**

* Detect SQL injection attempts
* Match malicious payload signatures

In these real-world systems, REs are compiled and executed using engines like Python’s `re`, PCRE, JavaScript regex, etc., which offer features such as:

* `+`, `*`, `?`, `{m,n}`
* Character classes (`[a-z]`)
* Lookahead/lookbehind
* Groups and backreferences
* Non-capturing groups (`(?:...)`)

---

## 🧮 **2. What We Learn in Theory (TOC / Automata)**

In college-level Theory of Computation (TOC), we learn **mathematical regular expressions**, which follow a much simpler grammar:

```
(a + b)*abb
(0 + 1){8}
(a + bc)(a + b)*
```

The theoretical REs use:

* `+` for union
* concatenation implicitly
* `*` for Kleene closure
* parentheses for grouping
* sometimes `{n}` for exact repetition
* symbols as individual characters

These REs describe **regular languages**, which correspond to **DFA/NFA automata**.

However—they are **not directly usable** in real regex engines.

Example:

```
(a + b)*    # TOC RE
[ab]*       # Python/PCRE regex
```

---

## ⚠️ **3. The Gap Between Theory and Practice**

Students often ask:

* “Why do theoretical REs look so different from real regex?”
* “Where do DFAs/NFAs show up in practical tools?”
* “Why does real regex use ‘|’, ‘(?: )’, ‘+’, ‘{m,n}’, etc.?”

Differences include:

| Theory (TOC)                    | Real Regex                                       |
|----------------------------------|--------------------------------------------------|
| Union uses `+`                   | Union uses `\|`                                  |
| Concatenation implicit           | Explicit grouping required                       |
| `(a + b)`                        | `(?:a|b)` or `[ab]`                              |
| `a{3}`                           | `a{3}`                                           |
| Parentheses only group           | Capturing `()`, non-capturing `(?:)`, lookahead  |
| No escapes                       | Many escapes like `\d`, `\w`, `\s`               |

Because of these mismatches, **students cannot directly test or apply the expressions they learn**.

There has never been a simple tool that lets students **write TOC-style REs and see real matches** in actual text.

---

# 🌉 **4. What This Project Bridges**

This project creates a bridge between **formal regular expressions** and **practical regex engines** by:

### ✔ Parsing TOC-style regular expressions

Using a real **context-free grammar** and a **recursive descent parser**, just like real compilers.

### ✔ Building an AST

Representing expressions using:

* `Symbol`
* `Concat`
* `Union`
* `Repeat`
* `Group`

This mirrors how real language processors work.

### ✔ Translating to Python-Regex

The AST is converted to valid Python regex:

| Input (TOC RE) | Output (Python Regex) |
| -------------- | --------------------- |
| `(a + b)*abb`  | `(?:[ab])*abb`        |
| `(a+b)^5`      | `(?:[ab]){5}`         |
| `a{2,4}`       | `a{2,4}`              |
| `(ab)^3`       | `(?:ab){3}`           |

### ✔ Highlighting matches (regex101-style)

Lets students understand the **pattern matching behavior**.

### ✔ Checking full-string acceptance (Automata-style)

Shows which input strings belong to the regular language.

```
abc   → ACCEPTED
abb   → REJECTED
bbaa  → ACCEPTED
```

---

# 🎯 **Why This Project Matters**

This tool demonstrates:

* **Practical use of grammars**
* **Real-world parsing and AST construction**
* **Connection to regular languages, DFAs, and NFAs**
* **How compilers and interpreters work internally**
* **How theory maps to real applications**
* **Why learning formal languages is useful**

Perfect for:

* TOC / Automata courses
* Compiler design intros
* Educational demos
* Students wanting to understand the link between theory and practice
* Anyone learning regex

---
