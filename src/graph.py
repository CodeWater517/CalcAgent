"""
LangGraph 多智能体流程图模块
实现算式逐步计算的多智能体系统

职责划分：
- judge_node : 使用 LLM 解析表达式，决定下一步计算（不执行）
- calc_node  : 使用绑定工具的 LLM 生成工具调用
- tool_node  : 使用 ToolNode 执行具体计算
- update_node: 将工具结果写回 expression 历史
- 条件边    : 控制循环与终止
"""

import json
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from .state import CalcState
from .tools import CALC_TOOLS
from .ustils import is_single_number, replace_span, format_number
from .prompts import JUDGE_SYSTEM_PROMPT
from .configuration import config


# =====================================================
# LLM 配置
# =====================================================

# judge_node 使用的 LLM（解析表达式）
judge_llm = ChatOpenAI(
    model=config.LLM_MODEL,
    temperature=config.LLM_TEMPERATURE,
    api_key=config.LLM_API_KEY,
    base_url=config.LLM_BASE_URL
)

# calc_node 使用的 LLM（绑定工具）
calc_llm = ChatOpenAI(
    model=config.LLM_MODEL,
    temperature=0,
    api_key=config.LLM_API_KEY,
    base_url=config.LLM_BASE_URL
).bind_tools(CALC_TOOLS)


# =====================================================
# ToolNode（执行层）
# =====================================================

tool_node_executor = ToolNode(CALC_TOOLS)


# =====================================================
# 节点定义
# =====================================================

def start_node(state: CalcState) -> Dict[str, Any]:
    """
    初始化节点
    - 确保 expression 为 list[str]
    """
    expression = state.get("expression")

    if isinstance(expression, str):
        expression = [expression]
    elif not expression:
        expression = ["0"]

    print(f"\n{'='*50}")
    print(f"[start_node] 初始化表达式: {expression[-1]}")
    print(f"{'='*50}")

    return {"expression": expression}


def judge_node(state: CalcState) -> Dict[str, Any]:
    """
    判断节点（Planner / Decider）

    - 如果表达式已经是单一数值：什么都不返回（由条件边结束）
    - 否则：调用 LLM，返回下一步计算信息
    """
    expression_list = state.get("expression", [])
    if not expression_list:
        return {"error": "expression is empty"}

    cur_expr = expression_list[-1]

    # 已经算完
    if is_single_number(cur_expr):
        print(f"\n[judge_node] 表达式已是单一数值: {cur_expr}，计算完成!")
        return {}

    print(f"\n[judge_node] 解析表达式: {cur_expr}")

    try:
        response = judge_llm.invoke([
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=f"表达式: {cur_expr}")
        ])

        result = json.loads(response.content)

        op = result.get("operator")
        lhs = result.get("lhs")
        rhs = result.get("rhs")
        print(f"   ->  下一步计算: {lhs} {op} {rhs}")

        return {
            "operator": op,
            "lhs": lhs,
            "rhs": rhs,
            "span": result.get("span"),
            "tool": result.get("tool"),
        }

    except Exception as e:
        print(f"   [error] 解析失败: {e}")
        return {"error": f"judge_node failed: {str(e)}"}


def calc_node(state: CalcState) -> Dict[str, Any]:
    """
    计算节点（Tool Caller）
    
    - 根据 judge_node 的结果，构造 prompt
    - 调用绑定了工具的 LLM
    - 返回包含 tool_calls 的消息
    """
    operator = state.get("operator")
    lhs = state.get("lhs")
    rhs = state.get("rhs")
    
    if not operator:
        return {"error": "no operator found"}

    print(f"\n[calc_node] 调用工具计算: {lhs} {operator} {rhs}")
        
    prompt = f"请计算: {lhs} {operator} {rhs}"
    
    # 调用 LLM 生成工具调用
    response = calc_llm.invoke([HumanMessage(content=prompt)])
    
    return {"messages": [response]}


def update_node(state: CalcState) -> Dict[str, Any]:
    """
    更新节点（State Writer）

    - 从 messages 中获取最后的 ToolMessage
    - 解析工具执行结果
    - 替换原表达式中的 span
    - 将新表达式追加到 expression 历史
    """
    messages = state.get("messages", [])
    if not messages:
        return {"error": "no messages found"}
        
    last_msg = messages[-1]
    if not isinstance(last_msg, ToolMessage):
        return {"error": "last message is not a ToolMessage"}
        
    # 解析工具结果
    try:
        # ToolMessage.content 通常是字符串
        tool_result = json.loads(last_msg.content)
    except Exception:
        # 如果不是 JSON，可能直接是结果字符串（取决于工具实现）
        # 但我们的工具返回的是 {"value": ...} 或 {"error": ...} 的 JSON 字符串（由 ToolNode 序列化）
        # 或者 ToolNode 直接返回工具函数的返回值？
        # LangGraph 的 ToolNode 会将工具返回值转为字符串作为 content
        # 我们的工具返回 dict，所以 content 应该是 json 字符串
        return {"error": f"failed to parse tool result: {last_msg.content}"}

    if "error" in tool_result:
        return {"error": tool_result["error"]}
        
    value = tool_result.get("value")
    if value is None:
        return {"error": "tool result missing 'value'"}

    try:
        value_float = float(value)
    except Exception:
        return {"error": f"invalid value: {value}"}

    value_str = format_number(value_float)

    expression_list = state.get("expression", [])
    cur_expr = expression_list[-1]
    span = state.get("span")
    
    try:
        if span:
            new_expr = replace_span(cur_expr, span, value_str)
        else:
            new_expr = value_str
    except Exception as e:
        return {"error": f"expression update failed: {str(e)}"}

    print(f"\n[update_node] 更新表达式: {cur_expr} -> {new_expr}")

    return {
        "expression": expression_list + [new_expr],
        # 清理中间态
        "operator": None,
        "lhs": None,
        "rhs": None,
        "span": None,
        "tool": None,
    }


# =====================================================
# 条件边
# =====================================================

def route_after_judge(state: CalcState) -> Literal["calc_node", "end"]:
    """
    judge_node 之后的路由规则
    """
    if state.get("error"):
        return "end"

    expression_list = state.get("expression", [])
    if expression_list and is_single_number(expression_list[-1]):
        return "end"

    if state.get("operator"):
        return "calc_node"

    return "end"


def route_after_update(state: CalcState) -> Literal["judge_node", "end"]:
    """
    update_node 之后的路由规则
    """
    if state.get("error"):
        return "end"

    return "judge_node"


# =====================================================
# 构建计算图
# =====================================================

def build_calc_graph():
    """
    构建并编译 LangGraph

    执行流程：
    START -> start_node -> judge_node -> calc_node -> tool_node -> update_node -> judge_node ...
    """
    graph = StateGraph(CalcState)

    # 注册节点
    graph.add_node("start_node", start_node)
    graph.add_node("judge_node", judge_node)
    graph.add_node("calc_node", calc_node)
    graph.add_node("tool_node", tool_node_executor)
    graph.add_node("update_node", update_node)

    # 固定边
    graph.add_edge(START, "start_node")
    graph.add_edge("start_node", "judge_node")
    graph.add_edge("calc_node", "tool_node")
    graph.add_edge("tool_node", "update_node")
    graph.add_edge("update_node", "judge_node")

    # 条件边
    graph.add_conditional_edges(
        "judge_node",
        route_after_judge,
        {
            "calc_node": "calc_node",
            "end": END
        }
    )
    
    # update_node 也可以有条件边，或者直接连回 judge_node
    # 这里使用条件边以处理错误情况
    graph.add_conditional_edges(
        "update_node",
        route_after_update,
        {
            "judge_node": "judge_node",
            "end": END
        }
    )

    return graph.compile()

