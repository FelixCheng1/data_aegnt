from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from loguru import logger


async def generate_sql(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("生成sql")

    try:
        # 处理
        return {}
    except Exception as e:
        logger.error("生成sql错误")
        raise