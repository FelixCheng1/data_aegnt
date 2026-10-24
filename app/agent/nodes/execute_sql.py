from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("执行sql")

    try:
        sql = state["sql"]
        dw_mysql_repo = runtime.context["dw_mysql_repo"]

        # 执行sql
        result = await dw_mysql_repo.execute_sql(sql)

        # 将查询结果写给调用者
        runtime.stream_writer({"result":result})
        logger.info(f"执行SQL完成：result={result}")
        return {}
    except Exception as e:
        logger.error(f"执行sql错误：{str(e)}")
        raise