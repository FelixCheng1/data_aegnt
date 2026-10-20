from elasticsearch import AsyncElasticsearch

"""
用于操作ES的持久层
"""

class ValueESRepository:
    def __init__(self, client: AsyncElasticsearch):
        self.clinet = client