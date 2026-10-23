from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from loguru import logger


async def execute_sql(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("执行sql")

    try:
        # 处理
        return {}
    except Exception as e:
        logger.error(f"执行sql错误：{str(e)}")
        raise