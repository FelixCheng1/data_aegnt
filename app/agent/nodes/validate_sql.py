from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

MAX_FAIL_COUNT = 5

async def validate_sql(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer({"stage":"校验sql"})

    fail_count = state["fail_count"]

    try:
        # 判断如果失败次数已经达到最大值，抛出错误，结束
        if fail_count == MAX_FAIL_COUNT:
            raise Exception("校正失败")

        sql = state["sql"]
        dw_mysql_repo = runtime.context["dw_mysql_repo"]
        # 对SQL语法进行校验
        await dw_mysql_repo.validate_sql(sql)

        logger.info("校验SQL完成")

        return {"error": None} # 自动跳转到execute_sql节点
    except Exception as e:
        # 如果已经达到最大次数，将错误抛出
        if fail_count == MAX_FAIL_COUNT:
            raise e
        
        # 如果没有达到最大次数，返回错误信息跳转到校正节点去
        logger.error(f"校验sql错误:{str(e)}")
        return {"error": f"校验SQL失败：{str(e)}", "fail_count":fail_count+1}   # 自动跳转到correct_sql节点
        