from datetime import datetime

from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DBInfoState, DataAgentState, DateInfoState
from loguru import logger


async def add_extra_context(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("添加额外信息")

    try:
        dw_mysql_repo = runtime.context["dw_mysql_repo"]

        # 生成当前日期数据
        today = datetime.today()
        date = today.strftime("%Y-%m-%d")
        weekday = today.strftime("%A")
        quarter = f"Q{(today.month+2)//3}"
        date_info = DateInfoState(
            date=date,
            weekday=weekday,
            quarter=quarter
        )
        # 得到当前的数据库信息
        db_info_dict = await dw_mysql_repo.get_db_info()
        db_info:DBInfoState = DBInfoState(**db_info_dict)

        logger.info(f"添加额外信息完成 date_info={date_info}，db_info={db_info}")
        
        return {"date_info":date_info, "db_info":db_info}
    except Exception as e:
        logger.error(f"添加额外信息错误：{str(e)}")
        raise