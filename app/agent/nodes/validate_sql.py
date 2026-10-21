from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from loguru import logger


async def validate_sql(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("校验sql")

    try:
        # 处理
        return {}
    except Exception as e:
        logger.error("校验sql错误")
        raise