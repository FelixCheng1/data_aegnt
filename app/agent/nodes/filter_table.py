from langgraph.runtime import Runtime
import yaml
from app.agent.llm import llm
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from loguru import logger
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.prompt.prompt_loader import load_prompt

"""
1.利用大模型对表和字段信息进行过滤，返回包含需要的表名和字段组成的字典
    {
        "表名1":["字段1", "字段2", "..."],
        "表名2":["字段1", "字段2", "..."]
    }
2.对table_infos过滤掉不需要的表信息和字段信息
3.返回过滤后的table_infos
"""


async def filter_table(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("过滤表")

    try:
        query = state["query"]
        table_infos = state["table_infos"]

        # 1.利用大模型对表和字段信息进行过滤，返回包含需要的表名和字段组成的字典
        prompt_template = PromptTemplate(
            template=load_prompt("filter_table_info"),
            input_variables=["query","table_infos"]
        )
        chain = prompt_template | llm | JsonOutputParser()
        table_infos_yaml = yaml.dump(
            table_infos,
            allow_unicode=True, # 保留中文原文
            sort_keys=False, # 不要对数据中的字典中的属性进行排序
        )
        # print(table_infos_yaml)
        result:dict[str, list[str]] = await chain.ainvoke({"query":query, "table_infos":table_infos_yaml})

        # 2.对table_infos过滤掉不需要的表信息和字段信息
        # 问题：遍历数组时删除数据元素可能会落掉被删除的下一个元素
        # 解决: 遍历浅拷贝的数组，删除原数组
        for table_info in table_infos[:]:
            table_name = table_info["name"]
            if table_name not in result:
                table_infos.remove(table_info) # 过滤表信息
            else:   # 留下表信息，下面过滤字段信息
                for column in table_info["columns"][:]:
                    column_name = column["name"]
                    if column_name not in result[table_name]:
                        table_info["columns"].remove(column)    # 过滤字段信息
        logger.info(f"表和字段过滤完成：{table_infos}")

        # 3.返回过滤后的table_infos
        return {"table_infos":table_infos}
    except Exception as e:
        logger.error(f"过滤表错误:{str(e)}")
        raise