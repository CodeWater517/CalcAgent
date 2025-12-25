"""
CalcAgent - 多智能体算式计算系统

基于 LangGraph 构建的循环计算流程，逐步化简算式直到得到最终数值。

使用示例:
    from src import calculate
    result = calculate("1+2*3")
    print(result["result"])  # 输出: 7
"""

from .state import CalcState
from .tools import add, sub, mul, div, CALC_TOOLS, TOOL_MAP
from .graph import build_calc_graph
from .ustils import is_single_number, replace_span, format_number

__all__ = [
    # State
    "CalcState",
    
    # Tools
    "add",
    "sub", 
    "mul",
    "div",
    "CALC_TOOLS",
    "TOOL_MAP",
    
    # Graph
    "build_calc_graph",
    "calculate",
    
    # Utils
    "is_single_number",
    "replace_span",
    "format_number",
]
