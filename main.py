from uuid import uuid4

from fastapi import FastAPI, Request
import uvicorn

from app.api.routers.query_router import query_router
from app.core.context import set_req_id
from app.core.lifespan import lifespan

# 创建app应用，并绑定生命周期函数
app = FastAPI(lifespan=lifespan)

# 添加中间件，在每个请求中生成唯一的request_id
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # 调用路径函数前，创建request_id并保存
    set_req_id(uuid4())

    # 调用路由函数
    reponse = await call_next(request)

    # 调用路由函数后
    return reponse

# 添加路由器
app.include_router(query_router)


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
