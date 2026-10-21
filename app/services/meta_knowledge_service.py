from uuid import uuid4

from app.core.log import logger

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.conf.meta_config import MetricConfig, TableConfig, meta_config
from app.models.es.value_info_es import ValueInfoES
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

"""
构建元知识库的业务层
"""



class MetaKnowledgeService:
    def __init__(
        self,
        dw_mysql_repo: DwMysqlRepository,
        meta_mysql_repo: MetaMysqlRepository,
        value_es_repo: ValueESRepository,
        column_qdrant_repo: ColumnQdrantRepository,
        metric_qdrant_repo: MetricQdrantRepository,
        embedding_client: HuggingFaceEndpointEmbeddings
    ):
        self.dw_mysql_repo = dw_mysql_repo
        self.meta_mysql_repo = meta_mysql_repo
        self.value_es_repo = value_es_repo
        self.column_qdrant_repo = column_qdrant_repo
        self.metric_qdrant_repo = metric_qdrant_repo
        self.embedding_client = embedding_client
    """
    1. 处理表相关的信息
     1.1 将表的信息和字段信息保存到meta库（tableinfo和column_info表）
     1.2 对所有的字段信息建立向量索引
     1.3 对所有字段取值建立全文索引
    2. 处理指标信息
     2.1 将指标信息保存到meta库中（metric_info和culumn_metric表）
     2.2 对指标信息建立向量索引
    """
    
    async def build(self):
        logger.info("进行元数据知识库的构建处理")

        await self.meta_mysql_repo.clear_meta_data()
        # 1. 处理表相关的信息
        #  1.1 将表的信息和字段信息保存到meta库（tableinfo和column_info表）
        column_infos: list[ColumnInfoMySQL] = await self._save_table_infos_to_meta(meta_config.tables)
        logger.info("将所有表和字段信息添加到meta库完成")

        # 1.2 对所有的字段信息建立向量索引
        await self._save_column_infos_to_qdrant(column_infos)
        logger.info("将字段信息添加到qdrant建立向量索引完成")

        # 1.3 对所有字段取值建立全文索引
        await self._save_value_infos_to_es(column_infos, meta_config.tables)
        logger.info("将字段值信息添加到ES建立全文索引完成")

        # 2. 处理指标信息
        #  2.1 将指标信息保存到meta库中（metric_info和culumn_metric表）
        metric_infos: list[MetricInfoMySQL] = await self._save_metric_infos_to_meta(meta_config.metrics)
        logger.info("将指标信息添加到meta库完成")

        # 2.2 对指标信息建立向量索引
        await self._save_metric_infos_to_qdrant(metric_infos)
        logger.info("将指标信息添加到qdrant建立向量索引完成")

    async def _save_table_infos_to_meta(self, tables:list[TableConfig]) -> list[ColumnInfoMySQL]:
        # 遍历tables 收集表信息的列表与字段信息的列表
        table_infos:list[TableInfoMySQL] = []
        column_infos: list[ColumnInfoMySQL] = []
        for table in tables:
            table_infos.append(TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description
            ))
            # 查询当前表的所有字段类型：dict[字段名：字段类型]
            cloumn_types:dict[str, str] = await self.dw_mysql_repo.get_cloumn_types(table.name)
            for column in table.columns:
                # 查询当前字段的前10个值
                values:list = await self.dw_mysql_repo.get_cloumn_values(table.name, column.name)
                column_infos.append(ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=cloumn_types[column.name], # 需要查询dw库
                    role=column.role,
                    examples=values,    # 需要查询dw库
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name
                ))

        # 保存到meta库
        self.meta_mysql_repo.save_table_infos(table_infos)
        self.meta_mysql_repo.save_column_infos(column_infos)

        # 返回字段信息列表
        return column_infos

    async def _save_column_infos_to_qdrant(self, column_infos: list[ColumnInfoMySQL]):
        # 遍历column-infos收集ids，payloads，texts(name,description,alia)
        temp_list:list[dict] = []
        for column_info in column_infos:
            payload = ColumnInfoQdrant(
                id=column_info.id,
                name=column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
                table_id=column_info.table_id
            )
            # name
            temp_list.append({
                "id":uuid4(),
                "payload":payload,
                "text":column_info.name
            })
            # description
            temp_list.append({
                "id":uuid4(),
                "payload":payload,
                "text":column_info.description
            })
            # alias
            for alia in column_info.alias:
                temp_list.append({
                    "id":uuid4(),
                    "payload":payload,
                    "text":alia
                })

        # 生成ids，payload，text
        ids:list[str] = [item["id"] for item in temp_list]
        payloads:list[ColumnInfoQdrant] = [item["payload"] for item in temp_list]
        texts:list[str] = [item["text"] for item in temp_list]

        batch_size = 16
        vectors:list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_vectors:list[list[float]] = await self.embedding_client.aembed_documents(batch_texts)
            vectors.extend(batch_vectors)

        # 将数据保存到Qdrant
        await self.column_qdrant_repo.insert_column_vectors(ids, payloads, vectors)

    async def _save_value_infos_to_es(self,column_infos:list[ColumnInfoMySQL], tables:list[TableConfig]):
        # 通过tables来收集所有字段是否需要进行ES索引的标识 dict[str,bool]
        column_sync_dict:dict[str,bool] = {}
        for table in tables:
            for column in table.columns:
                column_sync_dict[f"{table.name}.{column.name}"] = column.sync

        # 遍历column-infos来收集字段值信息列表
        value_infos: list[ValueInfoES] = []
        for column_info in column_infos:
            if column_sync_dict[column_info.id]:
                # 查询当前字段的所有值
                values:list = await self.dw_mysql_repo.get_cloumn_values(column_info.table_id, column_info.name, limit=10000)
                for value in values:
                    value_infos.append(ValueInfoES(
                        id=f"{column_info.id}.{value}",
                        value=value,
                        type=column_info.type,
                        column_id=column_info.id,
                        column_name=column_info.name,
                        table_id=column_info.table_id,
                        table_name=column_info.table_id
                    ))

        # 保存到ES库中
        await self.value_es_repo.insert_value_infos(value_infos)

    # 将指标信息添加到meta库
    async def _save_metric_infos_to_meta(self, metrics:list[MetricConfig]) -> list[MetricInfoMySQL]:
        # 1. 遍历metrics来收集指标信息列表与字段指标列表
        metric_infos:list[MetricInfoMySQL] = []
        column_metrics:list[ColumnMetricMySQL] = []
        for metric in metrics:
            metric_infos.append(MetricInfoMySQL(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            ))
            for column_id in metric.relevant_columns:
                column_metrics.append(ColumnMetricMySQL(
                    column_id=column_id,
                    metric_id=metric.name
                ))
        # 保存到meta库
        self.meta_mysql_repo.save_metric_infos(metric_infos)
        self.meta_mysql_repo.save_column_metrics(column_metrics)

        return metric_infos
        
    async def _save_metric_infos_to_qdrant(self, metric_infos: list[MetricInfoMySQL]):
        # 遍历metric_infos收集ids, payloads, texts(name,description,alia)
        temp_list:list[dict] = []
        for metric_info in metric_infos:
            payload = MetricInfoQdrant(
                id=metric_info.id,
                name=metric_info.name,
                description=metric_info.description,
                relevant_columns=metric_info.relevant_columns,
                alias=metric_info.alias,
            )
            # name
            temp_list.append({
                "ids":uuid4(),
                "payload":payload,
                "text":metric_info.name
            })
            # description
            temp_list.append({
                "ids":uuid4(),
                "payload":payload,
                "text":metric_info.description
            })
            # alias
            for alia in metric_info.alias:
                temp_list.append({
                    "ids":uuid4(),
                    "payload":payload,
                    "text":alia
                })
        ids:list[str] = [item['ids'] for item in temp_list]
        payloads:list[MetricInfoQdrant] = [item['payload'] for item in temp_list]
        texts:list[str] = [item['text'] for item in temp_list]

        # 批次生成向量
        batch_size = 16
        vectors:list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_vectors = await self.embedding_client.aembed_documents(batch_texts)
            vectors.extend(batch_vectors)

        # 将数据保存到Qdrant
        await self.metric_qdrant_repo.insert_metric_vectors(ids, payloads, vectors)
