from langgraph.runtime import Runtime
import yaml
from app.agent.llm import llm
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.prompt.prompt_loader import load_prompt

"""
1. 利用大模型对指标信息进行过滤返回包含需要的指标名组成的数据
    ["指标1", "指标2", "..."]
2. 对metric_infos过滤掉不需要的指标信息
3. 返回过滤后metric_infos
"""

async def filter_metric(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer({"stage":"过滤指标"})

    try:
        query = state["query"]
        metric_infos = state["metric_infos"]

        # 1. 利用大模型对指标信息进行过滤返回包含需要的指标名组成的数据
        # 1.利用大模型对表和字段信息进行过滤，返回包含需要的表名和字段组成的字典
        prompt_template = PromptTemplate(
            template=load_prompt("filter_metric_info"),
            input_variables=["query","metric_infos"]
        )
        chain = prompt_template | llm | JsonOutputParser()
        metric_infos_yaml = yaml.dump(
            metric_infos,
            allow_unicode=True, # 保留中文原文
            sort_keys=False, # 不要对数据中的字典中的属性进行排序
        )

        result:dict[str, list[str]] = await chain.ainvoke({"query":query, "metric_infos":metric_infos_yaml})

        # 2. 对metric_infos过滤掉不需要的指标信息
        for metric_info in metric_infos[:]:
            metric_name = metric_info["name"]
            if metric_name not in result:
                metric_infos.remove(metric_info) # 过滤指标信息
        logger.info(f"指标过滤完成：{metric_infos}")

        # 3. 返回过滤后metric_infos
        return {"metric_infos":metric_infos}
    except Exception as e:
        logger.error(f"过滤指标错误：{str(e)}")
        raise