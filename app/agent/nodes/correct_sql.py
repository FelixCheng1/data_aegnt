from langgraph.runtime import Runtime
import yaml
from app.agent.llm import llm
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.prompt.prompt_loader import load_prompt


async def correct_sql(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("校正sql")

    try:
        query = state["query"]
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]

        sql = state["sql"]
        error = state["error"]

        prompt_template = PromptTemplate(
            template=load_prompt("generate_sql"),
            input_variables=["query","table_infos","metric_infos", "metric_infos", "date_info", "db_info", "sql", "error"]
        )
        chain = prompt_template | llm | StrOutputParser()

        sql = await chain.ainvoke({
            "query":query, 
            "table_infos":yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos":yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "date_info":yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info":yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "sql":yaml.dump(sql, allow_unicode=True, sort_keys=False),
            "error":yaml.dump(error, allow_unicode=True, sort_keys=False)
        })
        logger.info(f"校正sql成功：{sql}")
        return {"sql":sql}
    except Exception as e:
        logger.error(f"校正sql错误：{str(e)}")
        raise