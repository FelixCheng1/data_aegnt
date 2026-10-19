
# 创建一个用来存取请求id的context_var对象
import asyncio
from contextvars import ContextVar, Token


_req_context_var = ContextVar("req_id", default="")

# 保存请求id
def set_req_id(req_id: str) ->Token:
    return _req_context_var.set(req_id)

# 获取请求id
def get_req_id() -> str:
    return _req_context_var.get()

# 重置请求id
def reset_req_id(token: Token):
    _req_context_var.reset(token)

if __name__ == "__main__":
    async def req1():
        print(f"1---req1 req—id：{get_req_id()}")
        token = set_req_id("111")
        await asyncio.sleep(1)  # 模拟处理一段时间
        print(f"2---req1 req—id：{get_req_id()}")
        reset_req_id(token)
        print(f"3---req1 req—id：{get_req_id()}")

    async def req2():
        print(f"1---req2 req—id：{get_req_id()}")
        token = set_req_id("222")
        await asyncio.sleep(1)  # 模拟处理一段时间
        print(f"2---req2 req—id：{get_req_id()}")
        reset_req_id(token)
        print(f"3---req2 req—id：{get_req_id()}")

    async def test():
        await asyncio.gather(req1(), req2())

    asyncio.run(test())