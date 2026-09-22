"""
Controlled calculation tool.

Deliberately avoids unrestricted `eval`/`exec` of LLM-generated code. Only a
whitelisted set of arithmetic operators and math functions are permitted, via
Python's `ast` module walking a parsed expression tree.
"""
from __future__ import annotations

import ast
import math
import operator

from langchain_core.tools import tool

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_ALLOWED_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "mean": lambda *a: sum(a) / len(a),
}


class UnsafeExpressionError(ValueError):
    pass


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise UnsafeExpressionError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
            raise UnsafeExpressionError("Only whitelisted math functions are allowed")
        args = [_eval_node(a) for a in node.args]
        return _ALLOWED_FUNCS[node.func.id](*args)
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval_node(e) for e in node.elts]  # type: ignore[return-value]
    raise UnsafeExpressionError(f"Unsupported expression: {ast.dump(node)}")


def safe_calculate(expression: str) -> float:
    """Safely evaluate an arithmetic expression. Raises UnsafeExpressionError
    for anything outside the whitelisted grammar (no attribute access, no
    names/imports, no arbitrary code execution)."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"Could not parse expression: {exc}") from exc
    return _eval_node(tree)


def percentage_change(old: float, new: float) -> float:
    if old == 0:
        raise UnsafeExpressionError("Cannot compute percentage change from zero")
    return round((new - old) / old * 100, 4)


def cagr(begin_value: float, end_value: float, years: float) -> float:
    if begin_value <= 0 or years <= 0:
        raise UnsafeExpressionError("CAGR requires positive begin_value and years")
    return round(((end_value / begin_value) ** (1 / years) - 1) * 100, 4)


@tool
def calculator(expression: str) -> str:
    """Evaluate a safe arithmetic expression (percentages, averages, ratios,
    financial math). Supports +, -, *, /, //, %, **, abs, round, min, max,
    sum, sqrt, log, log10, mean. Does NOT execute arbitrary Python code."""
    try:
        result = safe_calculate(expression)
        return f"{result}"
    except UnsafeExpressionError as exc:
        return f"Calculation error: {exc}"
