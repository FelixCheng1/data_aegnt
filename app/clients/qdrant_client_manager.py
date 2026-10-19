
import asyncio
from random import random
from typing import Optional

from qdrant_client import AsyncQdrantClient, models
from app.conf.app_config import app_config,  QdrantConfig


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client: Optional[AsyncQdrantClient] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init_client(self):
        self.client = AsyncQdrantClient(self._get_url())

    async def close(self):
        await self.client.close()

# 创建向量数据库客户端管理器
qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == "__main__":
    async def test():
        collection_name = "test_collection"
        # 初始化客户端对象
        qdrant_client_manager.init_client()
        client = qdrant_client_manager.client

        # 创建集合，如果集合已存在，先删除集合再创建
        if await client.collection_exists(collection_name):
            await client.delete_collection(collection_name)
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1024,
                distance=models.Distance.COSINE
            )
        )

        # 插入向量
        await client.upsert(
            collection_name=collection_name,
            points = [
                models.PointStruct(
                    id=i,
                    payload={
                        "color": "red" if i % 2 == 0 else "blue"
                    },
                    vector=[random() for _ in range(1024)],
                ) for i in range(10)
            ]
        )

        # 搜索向量
        result = await client.query_points(
                    collection_name=collection_name,
                    query=[random() for _ in range(1024)],
                    limit=5,
                    score_threshold=0.7 # 向量相似度阈值
                )

        print(result.points)
        print(len(result.points))

        for point in result.points:
            print(f"payload = {point.payload}")

        # 释放资源
        await qdrant_client_manager.close()


    asyncio.run(test())