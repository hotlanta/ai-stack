#!/usr/bin/env python3
# qwed_verify.py — main engine (math now returns 36.0 for "15% of 240")
import ast, re
from sympy import sympify, SympifyError
from z3 import Solver, Bool, sat
import sqlglot

def verify_math(expression: str) -> dict:
    expr = re.sub(r'(\d+)\s*%\s*of\s*(\d+)', r'(\1/100)*\2', expression, flags=re.IGNORECASE)
    expr = expr.replace('%', '/100')
    match = re.search(r'[\d\.\+\-\*\/\^\(\)\s]+', expr)
    if not match: return {"verified": False, "result": "No numeric expression", "engine": "MATH_SYMPY"}
    try:
        result = sympify(match.group(0))
        return {"verified": True, "result": str(result.evalf()), "engine": "MATH_SYMPY"}
    except Exception as e:
        return {"verified": False, "result": str(e), "engine": "MATH_SYMPY"}

def verify_sql(sql_query: str, dialect: str = "postgres") -> dict:
    try:
        parsed = sqlglot.parse(sql_query, dialect=dialect, error_level=sqlglot.ErrorLevel.RAISE)
        return {"verified": True, "result": f"Valid SQL ({len(parsed)} statements)", "engine": "SQL_SQLGLOT"}
    except sqlglot.errors.ParseError as e:
        return {"verified": False, "result": str(e), "engine": "SQL_SQLGLOT"}

def verify_code(code: str) -> dict:
    try:
        tree = ast.parse(code)
        return {"verified": True, "result": f"Valid Python ({len(list(ast.walk(tree)))} nodes)", "engine": "CODE_AST"}
    except SyntaxError as e:
        return {"verified": False, "result": f"SyntaxError: {e.msg}", "engine": "CODE_AST"}

def auto_verify(llm_output: str) -> dict:
    stripped = llm_output.strip()
    if any(stripped.upper().startswith(kw) for kw in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "WITH"]):
        return verify_sql(stripped)
    if any(kw in stripped for kw in ["def ", "class ", "import ", "for ", "while ", "if ", "return "]):
        return verify_code(stripped)
    if any(x in stripped.lower() for x in ["%", "+", "-", "*", "/", "of"]):
        return verify_math(stripped)
    return {"verified": None, "result": "Could not auto-detect type", "engine": "NONE"}

# Convenience one-liner for agents
qwed_verify = auto_verify
