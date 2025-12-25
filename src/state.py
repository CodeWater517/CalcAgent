"""
State 定义模块
定义 CalcAgent 多智能体系统的共享状态结构
"""

from typing import TypedDict, Optional, List, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class CalcState(TypedDict, total=False):
    """
    计算智能体的共享状态结构
    
    字段说明:
    - expression: 列表，按时间顺序保存表达式的演化历史
    - messages: 消息列表，用于 LLM 和 ToolNode 交互
    - operator: 运算符 (+, -, *, /)
    - lhs: 左操作数
    - rhs: 右操作数
    - span: 子表达式在原表达式中的位置 [start, end]
    - tool: 对应的工具名 (add, sub, mul, div)
    - error: 计算阶段产生的错误信息（如除零）
    """
    expression: List[str]
    messages: Annotated[List[BaseMessage], add_messages]
    operator: Optional[str]
    lhs: Optional[str]
    rhs: Optional[str]
    span: Optional[List[int]]
    tool: Optional[str]
    error: Optional[str]
