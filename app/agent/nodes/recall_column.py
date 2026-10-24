from langgraph.runtime import Runtime
from app.agent.llm import llm
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.prompt_loader import load_prompt
"""
1.将用户提问交给LLM来提取语义化的关键词列表，并于原关键词列表去重合并
2.对keywords进行批量向量化 ——> keyword_vectors
3.遍历每个keyword_vectors，去Qdrant中搜索匹配的字段信息列表 ：list[ColumnInfoQdrant]
4.对得到的所有字段信息列表进行去重合并 ——> recall_columns:list[ColumnInfoQdrant]
5.返回recall_columns
"""

async def recall_column(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer("召回字段信息")

    try:
        query = state["query"]
        keywords = state["keywords"]
        embedding_client = runtime.context["embedding_client"]
        column_qdrant_repo = runtime.context["column_qdrant_repo"]
        # 1.将用户提问交给LLM来提取语义化的关键词列表，并于原关键词列表去重合并
        prompt_template = PromptTemplate(
            template=load_prompt("extend_keywords_for_column_recall"),
            input_variables=["query"]
        )
        chain = prompt_template | llm | JsonOutputParser()
        result:list[str] = await chain.ainvoke({"query":query})
        logger.info(f"recall-column llm keywords={result}")
        keywords = list(set(keywords + result))

        # 2.对keywords进行批量向量化 ——> keyword_vectors
        keywords_vectors:list[list[float]] = await embedding_client.aembed_documents(keywords)

        # 3.遍历每个keyword_vectors，去Qdrant中搜索匹配的字段信息列表 ：list[ColumnInfoQdrant]
        column_infos_dict:dict[str, ColumnInfoQdrant] = {}
        for keywords_vector in keywords_vectors:
            column_infos:list[ColumnInfoQdrant] = await column_qdrant_repo.search(keywords_vector)
            for column_info in column_infos:
                column_infos_dict[column_info["id"]] = column_info  # 如果重复则覆盖

        # 生成列表
        recall_columns = list(column_infos_dict.values())

        logger.info(f"字段召回完成：{recall_columns}")
        # 返回
        return {"recall_columns":recall_columns}
    except Exception as e:
        logger.error(f"召回字段信息错误：{str(e)}")
        raise