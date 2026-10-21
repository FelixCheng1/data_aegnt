from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from loguru import logger


async def recall_column(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("召回字段信息")

    try:
        # 处理
        return {}
    except Exception as e:
        logger.error("召回字段信息错误")
        raise