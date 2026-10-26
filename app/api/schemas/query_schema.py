from pydantic import BaseModel

# 负责定义查询接口请求体结构
class QuerySchema(BaseModel):
    query:str