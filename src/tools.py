"""
工具定义模块
定义计算工具（可用于 LLM tool_bind 或直接调用）
"""

from typing import Dict, Any
from langchain_core.tools import tool


# ==================== 计算工具 ====================

@tool
def add(lhs: float, rhs: float) -> Dict[str, Any]:
    """加法运算：返回 lhs + rhs"""
    return {"value": lhs + rhs}


@tool
def sub(lhs: float, rhs: float) -> Dict[str, Any]:
    """减法运算：返回 lhs - rhs"""
    return {"value": lhs - rhs}


@tool
def mul(lhs: float, rhs: float) -> Dict[str, Any]:
    """乘法运算：返回 lhs * rhs"""
    return {"value": lhs * rhs}


@tool
def div(lhs: float, rhs: float) -> Dict[str, Any]:
    """除法运算：返回 lhs / rhs，除数为零时返回错误"""
    if rhs == 0:
        return {"error": "division by zero"}
    return {"value": lhs / rhs}


# ==================== 工具集合 ====================

CALC_TOOLS = [add, sub, mul, div]

TOOL_MAP = {
    "+": add,
    "-": sub,
    "*": mul,
    "/": div
}
