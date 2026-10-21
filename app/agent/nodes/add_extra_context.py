from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from loguru import logger


async def add_extra_context(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("添加额外信息")

    try:
        # 处理
        return {}
    except Exception as e:
        logger.error("添加额外信息错误")
        raise