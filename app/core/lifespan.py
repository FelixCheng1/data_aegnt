from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    managers = (
        dw_mysql_client_manager,
        meta_mysql_client_manager,
        es_client_manager,
        qdrant_client_manager,
        embedding_client_manager,
    )

    async with AsyncExitStack() as stack:
         # ① 启动阶段：初始化客户端，登记关闭方法
        for manager in managers:
            manager.init_client()
            stack.push_async_callback(manager.close)

        # ② 暂停生命周期函数，FastAPI 开始处理请求
        yield

        # ③ 应用关闭时，从这里恢复执行

    # ④ 退出 async with，自动调用登记的所有关闭方法