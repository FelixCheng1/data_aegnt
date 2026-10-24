from langgraph.runtime import Runtime
import yaml
from app.agent.llm import llm
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.prompt.prompt_loader import load_prompt
# 利用大模型来生成，要交给大模型数据：
async def generate_sql(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("生成sql")

    try:
        query = state["query"]
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        date_info = state["date_info"]
        db_info = state["db_info"]

        prompt_template = PromptTemplate(
            template=load_prompt("generate_sql"),
            input_variables=["query","table_infos","metric_infos", "metric_infos", "date_info", "db_info"]
        )
        chain = prompt_template | llm | StrOutputParser()

        sql = await chain.ainvoke({
            "query":query, 
            "table_infos":yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos":yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "date_info":yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info":yaml.dump(db_info, allow_unicode=True, sort_keys=False)
        })
        logger.info(f"生成SQL完成：{sql}")
        return {"sql":sql}
    except Exception as e:
        logger.error(f"生成sql错误：str{e}")
        raise