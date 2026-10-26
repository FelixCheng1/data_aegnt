from fastapi import Depends
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.query_service import QueryService

# 定义返回dw_session对象的函数
async def get_dw_session():
    async with dw_mysql_client_manager.session_factory() as session:
        yield session

# 定义返回meta_session对象的函数
async def get_meta_session():
    async with meta_mysql_client_manager.session_factory() as session:
        yield session

def get_query_service(
    dw_session=Depends(get_dw_session),
    meta_session=Depends(get_meta_session),
):
    return QueryService(
        dw_mysql_repo =  DwMysqlRepository(dw_session),
        meta_mysql_repo = MetaMysqlRepository(meta_session),
        value_es_repo = ValueESRepository(es_client_manager.client),
        column_qdrant_repo = ColumnQdrantRepository(qdrant_client_manager.client),
        metric_qdrant_repo = MetricQdrantRepository(qdrant_client_manager.client),
        embedding_client = embedding_client_manager.client
    )