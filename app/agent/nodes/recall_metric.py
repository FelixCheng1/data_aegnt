from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.prompt.prompt_loader import load_prompt
from app.agent.llm import llm


async def recall_metric(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("召回指标信息")

    try:
        query = state["query"]
        keywords = state["keywords"]
        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repo = runtime.context["metric_qdrant_repo"]
        # 1.将用户提问交给LLM来提取语义化的关键词列表，并于原关键词列表去重合并
        prompt_template = PromptTemplate(
            template=load_prompt("extend_keywords_for_metric_recall"),
            input_variables=["query"]
        )
        chain = prompt_template | llm | JsonOutputParser()
        result:list[str] = await chain.ainvoke({"query":query})
        logger.info(f"recall-metric llm keywords={result}")
        keywords = list(set(keywords + result))

        # 2.对keywords进行批量向量化 ——> keyword_vectors
        keywords_vectors:list[list[float]] = await embedding_client.aembed_documents(keywords)

        # 3.遍历每个keyword_vectors，去Qdrant中搜索匹配的指标信息列表 ：list[MetricInfoQdrant]
        metric_infos_dict:dict[str, MetricInfoQdrant] = {}
        for keywords_vector in keywords_vectors:
            metric_infos:list[MetricInfoQdrant] = await metric_qdrant_repo.search(keywords_vector)
            for metric_info in metric_infos:
                metric_infos_dict[metric_info["id"]] = metric_info  # 如果重复则覆盖

        # 生成列表
        recall_metrics = list(metric_infos_dict.values())

        logger.info(f"指标召回完成：{recall_metrics}")
        # 返回
        return {"recall_metrics":recall_metrics}
    except Exception as e:
        logger.error(f"召回指标信息错误：{str(e)}")
        raise