from qdrant_client import AsyncQdrantClient


"""
对于Column信息用于操作Qdrant的持久层
"""


class ColumnQdrantRepository:
    def __init__(self, client: AsyncQdrantClient):
        self.clinet = client