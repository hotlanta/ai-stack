#!/usr/bin/env python3
# =============================================================================
# mcp-qwed.py — QWED MCP server (MCP streamable-http protocol)
# Exposes qwed_verify as a proper MCP tool, compatible with mcpo + Open WebUI
#
# Requires: pip install fastmcp
# Run:      python /home/gem/mcp-qwed.py
# Access:   http://aio-sandbox:8091/mcp
# =============================================================================

from fastmcp import FastMCP
from qwed_verify import auto_verify, verify_math, verify_sql, verify_code

mcp = FastMCP("QWED Verification")

@mcp.tool()
def qwed_verify(llm_output: str) -> dict:
    """
    Deterministically verify any LLM output.
    Auto-detects output type and applies the right engine:
    - SQL queries → SQLGlot parser
    - Python code → AST syntax check
    - Math expressions → SymPy symbolic solver
    - Other → passes through with engine: NONE
    Returns a dict with keys: verified (bool|None), result (str), engine (str).
    """
    return auto_verify(llm_output)

@mcp.tool()
def verify_math_expression(expression: str) -> dict:
    """
    Verify a math expression or calculation using SymPy.
    Handles percentages, arithmetic, and algebraic expressions.
    Example: '15% of 240' returns verified: True, result: '36.0'
    """
    return verify_math(expression)

@mcp.tool()
def verify_sql_query(sql_query: str) -> dict:
    """
    Verify SQL query syntax using SQLGlot.
    Returns verified: True if the SQL is valid, False with error details if not.
    Example: 'SELECT * FROM docs WHERE id = 1' returns verified: True
    """
    return verify_sql(sql_query)

@mcp.tool()
def verify_python_code(code: str) -> dict:
    """
    Verify Python code syntax using the built-in AST parser.
    Returns verified: True if the code parses correctly, False with the SyntaxError if not.
    Example: 'def add(a, b):\\n    return a + b' returns verified: True
    """
    return verify_code(code)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8095, path="/mcp")