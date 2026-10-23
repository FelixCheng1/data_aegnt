from qdrant_client import AsyncQdrantClient, models

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant


"""
对于Column信息用于操作Qdrant的持久层
"""


class ColumnQdrantRepository:
    collection_name = "data-agent-column_collection2"
    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def _create_collection(self):
        client = self.client
    # 创建集合，如果集合已存在，先删除集合再创建
        if await client.collection_exists(self.collection_name):
            await client.delete_collection(self.collection_name)
        await client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=1024,
                distance=models.Distance.COSINE
            )
        )

    # 批量插入多个字段信息的向量列表
    async def insert_column_vectors(self, ids:list[str], payloads:list[ColumnInfoQdrant], vectors:list[list[float]]):
        # 创建集合
        await self._create_collection()

        # 分批处理
        batch_size = 20
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_payloads = payloads[i:i+batch_size]
            batch_vectors = vectors[i:i+batch_size]

            # 插入向量
            await self.client.upsert(
                collection_name=self.collection_name,
                points = [
                    models.PointStruct(
                        id=batch_ids[i],
                        payload=batch_payloads[i],
                        vector=batch_vectors[i],
                    ) for i in range(len(batch_ids))
                ]
            )
    # 搜索
    async def search(self, keywords_vector:list[float]) -> list[ColumnInfoQdrant]:
        # 查询匹配
        result = await self.client.query_points(
                    collection_name=self.collection_name,
                    query=keywords_vector,
                    score_threshold=0.6 # 向量相似度阈值，需要反复测试来得到
                )
        return [ColumnInfoQdrant(**point.payload) for point in result.points]