"""
辅助函数模块
提供表达式解析、数值判断等辅助功能
"""

import re
from typing import List, Dict, Any, Optional, Tuple


# 运算符优先级
OPERATOR_PRIORITY = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2
}

# 运算符到工具名的映射
OPERATOR_TO_TOOL = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "div"
}


def is_single_number(expr: str) -> bool:
    """
    判断表达式是否为单一数值字符串
    
    支持:
    - 整数: 7, -3, +5
    - 浮点数: 3.14, -2.5, +1.0
    - 科学计数法: 1e10, 2.5E-3
    
    Args:
        expr: 表达式字符串
    
    Returns:
        True 如果是单一数值，否则 False
    """
    expr = expr.strip()
    if not expr:
        return False
    
    # 匹配数值的正则表达式
    # 支持: 整数、浮点数、科学计数法、正负号
    number_pattern = r'^[+-]?(\d+\.?\d*|\d*\.?\d+)([eE][+-]?\d+)?$'
    
    return bool(re.match(number_pattern, expr))


def parse_expression(expr: str) -> List[Dict[str, Any]]:
    """
    将表达式字符串解析为 token 列表
    
    Args:
        expr: 表达式字符串，如 "1+2*3"
    
    Returns:
        Token 列表，每个 token 包含:
        - type: "number" 或 "operator"
        - value: 数值或运算符
        - start: 在原表达式中的起始位置
        - end: 在原表达式中的结束位置
    
    示例:
        parse_expression("1+2*3") -> [
            {"type": "number", "value": "1", "start": 0, "end": 1},
            {"type": "operator", "value": "+", "start": 1, "end": 2},
            {"type": "number", "value": "2", "start": 2, "end": 3},
            {"type": "operator", "value": "*", "start": 3, "end": 4},
            {"type": "number", "value": "3", "start": 4, "end": 5}
        ]
    """
    tokens = []
    i = 0
    expr = expr.strip()
    
    while i < len(expr):
        # 跳过空白
        if expr[i].isspace():
            i += 1
            continue
        
        # 检查是否是运算符
        if expr[i] in "+-*/" and tokens and tokens[-1]["type"] == "number":
            tokens.append({
                "type": "operator",
                "value": expr[i],
                "start": i,
                "end": i + 1
            })
            i += 1
            continue
        
        # 解析数字（包括可能的正负号）
        if expr[i].isdigit() or expr[i] in "+-" or expr[i] == ".":
            start = i
            
            # 处理正负号
            if expr[i] in "+-":
                i += 1
            
            # 解析整数部分
            while i < len(expr) and expr[i].isdigit():
                i += 1
            
            # 解析小数部分
            if i < len(expr) and expr[i] == ".":
                i += 1
                while i < len(expr) and expr[i].isdigit():
                    i += 1
            
            # 解析科学计数法部分
            if i < len(expr) and expr[i] in "eE":
                i += 1
                if i < len(expr) and expr[i] in "+-":
                    i += 1
                while i < len(expr) and expr[i].isdigit():
                    i += 1
            
            tokens.append({
                "type": "number",
                "value": expr[start:i],
                "start": start,
                "end": i
            })
            continue
        
        # 处理括号（暂时跳过）
        if expr[i] in "()":
            i += 1
            continue
        
        # 未知字符，跳过
        i += 1
    
    return tokens


def find_next_operation(tokens: List[Dict[str, Any]], original_expr: str) -> Optional[Dict[str, Any]]:
    """
    根据运算符优先级找到下一步需要计算的操作
    
    规则:
    - 先乘除后加减
    - 同优先级从左到右
    
    Args:
        tokens: parse_expression 返回的 token 列表
        original_expr: 原始表达式字符串
    
    Returns:
        下一步操作信息:
        {
            "operator": "*",
            "lhs": "2",
            "rhs": "3",
            "span": [2, 5],
            "tool": "mul"
        }
        如果没有操作可执行，返回 None
    """
    if len(tokens) < 3:
        return None
    
    # 找到优先级最高的运算符（同优先级取最左边的）
    best_op_idx = None
    best_priority = -1
    
    for i, token in enumerate(tokens):
        if token["type"] == "operator":
            priority = OPERATOR_PRIORITY.get(token["value"], 0)
            if priority > best_priority:
                best_priority = priority
                best_op_idx = i
    
    if best_op_idx is None:
        return None
    
    # 获取操作符及其左右操作数
    op_token = tokens[best_op_idx]
    lhs_token = tokens[best_op_idx - 1]
    rhs_token = tokens[best_op_idx + 1]
    
    # 计算 span（子表达式在原表达式中的位置）
    span_start = lhs_token["start"]
    span_end = rhs_token["end"]
    
    return {
        "operator": op_token["value"],
        "lhs": lhs_token["value"],
        "rhs": rhs_token["value"],
        "span": [span_start, span_end],
        "tool": OPERATOR_TO_TOOL[op_token["value"]]
    }


def replace_span(expr: str, span: List[int], replacement: str) -> str:
    """
    在表达式中替换指定范围的子串（智能处理括号）
    
    Args:
        expr: 原表达式
        span: [start, end] 位置
        replacement: 替换内容
    
    Returns:
        替换后的新表达式
    """
    start, end = span
    
    # 智能扩展：检查替换区域外围是否有括号包裹
    # 如果有，且括号内只剩这一个运算，则扩展 span 包含括号
    if start > 0 and end < len(expr):
        if expr[start - 1] == '(' and expr[end] == ')':
            # 扩展 span 包含括号
            start -= 1
            end += 1
    
    return expr[:start] + replacement + expr[end:]


def format_number(value: float) -> str:
    """
    格式化数值为字符串
    
    - 如果是整数，返回整数形式
    - 如果是浮点数，保留必要的小数位
    
    Args:
        value: 数值
    
    Returns:
        格式化后的字符串
    """
    if value == int(value):
        return str(int(value))
    else:
        # 移除末尾多余的零
        return f"{value:g}"


def validate_expression(expr: str) -> Tuple[bool, Optional[str]]:
    """
    验证表达式的基本格式（可选使用）
    
    Args:
        expr: 表达式字符串
    
    Returns:
        (is_valid, error_message)
    """
    if not expr or not expr.strip():
        return False, "expression is empty"
    
    # 检查是否包含非法字符
    allowed_chars = set("0123456789+-*/.eE ")
    if not all(c in allowed_chars for c in expr):
        return False, "expression contains invalid characters"
    
    return True, None
