from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from loguru import logger
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.models.es.value_info_es import ValueInfoES
from app.prompt.prompt_loader import load_prompt
from app.agent.llm import llm


async def recall_value(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("召回字段值")

    try:
        query = state["query"]
        keywords = state["keywords"]
        value_es_repo = runtime.context["value_es_repo"]
        # 1.将用户提问交给LLM来提取语义化的关键词列表，并于原关键词列表去重合并
        prompt_template = PromptTemplate(
            template=load_prompt("extend_keywords_for_value_recall"),
            input_variables=["query"]
        )
        chain = prompt_template | llm | JsonOutputParser()
        result:list[str] = await chain.ainvoke({"query":query})
        logger.info(f"recall-value llm keywords={result}")
        keywords = list(set(keywords + result))


        # 2.遍历每个keywords，去ES中搜索匹配的字段值列表 ：list[ValueInfoES]
        value_infos_dict:dict[str, ValueInfoES] = {}
        for keyword in keywords:
            value_infos:list[ValueInfoES] = await value_es_repo.search(keyword)
            for value_info in value_infos:
                value_infos_dict[value_info["id"]] = value_info  # 如果重复则覆盖

        # 生成列表
        recall_values = list(value_infos_dict.values())

        logger.info(f"字段值召回完成：{recall_values}")
        # 返回
        return {"recall_values":recall_values}
    except Exception as e:
        logger.error(f"召回字段值错误：{str(e)}")
        raise