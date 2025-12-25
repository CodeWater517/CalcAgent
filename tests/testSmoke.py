"""CalcAgent 冒烟脚本：运行一次完整的多智能体流程。"""

import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph import build_calc_graph


def main() -> None:
    expr = "1+2*3+(3-1)*4/2"
    graph = build_calc_graph()
    final_state = graph.invoke({"expression": expr})

    steps = final_state.get("expression", [])
    result = steps[-1] if steps else None
    error = final_state.get("error")

    print(f"input: {expr}")
    print(f"steps: {steps}")
    print(f"result: {result}")
    if error:
        print(f"error: {error}")


if __name__ == "__main__":
    main()
