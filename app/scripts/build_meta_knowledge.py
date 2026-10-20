import asyncio

from app.core.log import logger

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService

from sqlalchemy.ext.asyncio import AsyncSession
"""
1. 初始化所有客户端管理器
2. 创建构建的业务对象，要准备
    创建依赖的所有持久层对象，传入依赖的session和client
    用来生成向量的客户端
3. 调用业务对象的构建方法来构建知识库
4. 如果成功了，提交事务
5. 如果失败了，回滚事务
6. 最终都要关闭客户端
"""


async def start_build():

    logger.info("启动元数据库构建")

    try:
        # 初始化客户端
        embedding_client_manager.init_client()
        qdrant_client_manager.init_client()
        es_client_manager.init_client()
        dw_mysql_client_manager.init_client()
        meta_mysql_client_manager.init_client()
        async with(
            dw_mysql_client_manager.session_factory() as dw_session,
            meta_mysql_client_manager.session_factory() as meta_session
        ):
            dw_session: AsyncSession
            meta_session: AsyncSession
            # 创建业务层对象
            service = MetaKnowledgeService(
                dw_mysql_repo =  DwMysqlRepository(dw_session),
                meta_mysql_repo =  MetaMysqlRepository(meta_session),
                value_es_repo =  ValueESRepository(es_client_manager.client),
                column_qdrant_repo =  ColumnQdrantRepository(qdrant_client_manager.client),
                metric_qdrant_repo = MetricQdrantRepository(qdrant_client_manager.client),
                embedding_client = embedding_client_manager.client,
            )

            # 调用它的构建的业务方法
            await service.build()

            # 处理完成，提交事务
            # await dw_session.commit() dw库只查询，不需要事务
            await meta_session.commit()
            logger.info("构建知识库成功")
    except Exception as e:
        logger.error(f"构建知识库失败：{str(e)}")
        # 处理失败，回滚业务
        await meta_session.rollback()

        raise # 抛出异常
    finally:
        # 无论成功还是失败，都关闭客户端
        await qdrant_client_manager.close()
        await es_client_manager.close()
        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()

if __name__ == "__main__":
    asyncio.run(start_build())