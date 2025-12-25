"""
配置模块
CalcAgent 系统的配置参数
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class CalcAgentConfig:
    """CalcAgent 配置类"""
    
    # LLM 配置
    LLM_API_KEY: str = os.getenv("LONGCAT_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LONGCAT_BASE_URL", "")
    LLM_MODEL: str = "LongCat-Flash-Chat"
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    
    # LangChain 配置
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_TRACING_V2: bool = True
    
    # 最大计算步骤数（防止无限循环）
    MAX_STEPS: int = 100
    
    # 是否启用调试模式
    DEBUG: bool = False
    
    # 数值精度（小数点后位数）
    PRECISION: int = 10
    
    # 是否允许科学计数法输出
    ALLOW_SCIENTIFIC_NOTATION: bool = True


# 默认配置实例
config = CalcAgentConfig()
