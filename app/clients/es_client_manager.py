import asyncio
from typing import Optional
from elasticsearch import AsyncElasticsearch
from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    """
    ES异步客户端管理器：封装ES客户端的初始化、连接，关闭逻辑
    """

    def __init__(self, config: ESConfig):
        self.config = config 
        self.client: Optional[AsyncElasticsearch] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init_client(self):
        self.client = AsyncElasticsearch(
            hosts=[self._get_url()]
        )

    async def close(self):
        await self.client.close()

# 创建ES客户端管理器对象
es_client_manager = ESClientManager(app_config.es)

if __name__ == "__main__":
    async def test():
        # 初始化客户端
        es_client_manager.init_client()
        client = es_client_manager.client
        index_name = "test-index"

        # 测试连接
        is_connected = await es_client_manager.client.ping()
        print(f"ES连接状态: {is_connected}")

        # 创建索引
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
        result = await client.indices.create(
            index=index_name,
            mappings={
                "dynamic": False,
                "properties": {
                    "name": {
                        "type": "text"
                    },
                    "author": {
                        "type": "text"
                    },
                    "release_date": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "page_count": {
                        "type": "integer"
                    }
                }
            }
        )
        print(result)

        # 插入数据
        result1 = await client.bulk(
            operations=[
                {
                    "index": {
                        "_index": index_name
                    }
                },
                {
                    "name": "Revelation Space",
                    "author": "Alastair Reynolds",
                    "release_date": "2000-03-15",
                    "page_count": 585
                },
                {
                    "index": {
                        "_index": index_name
                    }
                },
                {
                    "name": "1984",
                    "author": "George Orwell",
                    "release_date": "1985-06-01",
                    "page_count": 328
                },
                {
                    "index": {
                        "_index": index_name
                    }
                },
                {
                    "name": "Fahrenheit 451",
                    "author": "Ray Bradbury",
                    "release_date": "1953-10-15",
                    "page_count": 227
                },
                {
                    "index": {
                        "_index": index_name
                    }
                },
                {
                    "name": "Brave New World",
                    "author": "Aldous Huxley",
                    "release_date": "1932-06-01",
                    "page_count": 268
                },
                {
                    "index": {
                        "_index": index_name
                    }
                },
                {
                    "name": "The Handmaids Tale",
                    "author": "Margaret Atwood",
                    "release_date": "1985-06-01",
                    "page_count": 311
                }
            ],
        )

        print(result1)

        # 刷新保存索引数据
        await client.indices.refresh(index=index_name)

        # 全文搜索
        result3 = await client.search(
            index=index_name,
            query={
                "match":{
                    "name":"Brave"
                }
            }
        )

        print(result3)
        print(result3["hits"]["hits"])


        # 关闭客户端
        await es_client_manager.close()

    asyncio.run(test())