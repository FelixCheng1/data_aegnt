from jieba.analyse import extract_tags
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(state:DataAgentState, runtime: Runtime[DataAgentContext]):
    # 自定义输出
    runtime.stream_writer({"stage":"提取关键词"})

    try:
        # 处理

        query = state["query"]
        # 定义返回指定词性的元组
        allow_pos = (
            "n",  # 名词: 数据、服务器、表格
            "nr",  # 人名: 张三、李四
            "ns",  # 地名: 北京、上海
            "nt",  # 机构团体名: 政府、学校、某公司
            "nz",  # 其他专有名词: Unicode、哈希算法、诺贝尔奖
            "v",  # 动词: 运行、开发
            "vn",  # 名动词: 工作、研究
            "a",  # 形容词: 美丽、快速
            "an",  # 名形词: 难度、合法性、复杂度
            "eng",  # 英文
            "i",  # 成语
            "l",  # 常用固定短语
        )
         # 使用jieba从用户的查询信息中提取关键，基于TF-IDF算法实现   
        keywords:list[str]=extract_tags(query,topK=5, allowPOS=allow_pos)
        logger.info(f"提取的关键词：{keywords}")
        # 将原始query也加入keyword中，去重的同时保留原有顺序，防止query就在keyword中
        keywords = list(set(keywords + [query]))
        logger.info(f"抽取提示词完成：{keywords}")

        return {"keywords":keywords}
    except Exception as e:
        logger.error(f"提取关键词错误：{str(e)}")
        raise