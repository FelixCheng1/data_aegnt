from qdrant_client import AsyncQdrantClient


"""
对于Metric信息用于操作Qdrant的持久层
"""


class MetricQdrantRepository:
    def __init__(self, client: AsyncQdrantClient):
        self.clinet = client