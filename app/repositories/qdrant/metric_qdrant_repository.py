from qdrant_client import AsyncQdrantClient, models

from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


"""
对于Metric信息用于操作Qdrant的持久层
"""


class MetricQdrantRepository:
    collection_name = "data-agent-metric_collection2"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    # 创建集合
    async def _creat_collection(self):
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

    # 批量插入多个指标信息的向量列表
    async def insert_metric_vectors(self, ids: list[str], payloads: list[MetricInfoQdrant], vectors:list[list[float]]):
        client = self.client
        collection_name = self.collection_name
        # 创建集合
        await self._creat_collection()

        # 分批次处理
        batch_size = 20
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_payload = payloads[i:i+batch_size]
            batch_vectors = vectors[i:i+batch_size]

            # 批量插入多个向量
            await client.upsert(
                collection_name=collection_name,
                points = [
                    models.PointStruct(
                        id=batch_ids[i],
                        payload=batch_payload[i],
                        vector=batch_vectors[i],
                    ) for i in range(len(batch_ids))
                ]
            )

