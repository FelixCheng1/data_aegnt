from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

"""
用于操作dw库的持久层
"""

class DwMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 查询指定表的所有字段类型
    async def get_cloumn_types(self, table_name:str) -> dict[str, str]:
        sql = f"SHOW COLUMNS FROM {table_name}"
        result = await self.session.execute(text(sql))
        return {item.Field:item.Type for item in result.all()}

    # 查询指定表中的指定字段的指定数量的字段数，默认10个
    async def get_cloumn_values(self, table_name: str, column_name: str, limit=10) -> list:
        sql = f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().all()

    async def get_db_info(self) -> dict[str, str]:
        result = await self.session.execute(text("select version()"))
        version = result.scalar()
        dialect = self.session.get_bind().dialect.name
        return {"version":version, "dialect":dialect}

    async def validate_sql(self, sql:str):
        await self.session.execute(text(f"explain {sql}"))

    async def execute_sql(self, sql:str):
        # 执行一条查询sql
        result = await self.session.execute(text(sql))
        # return result.mappings().all() # [rowMapping对象] 不能直接序列化
        return [dict(row) for row in result.mappings().all()]
    
if __name__ == "__main__":
    import asyncio
    from app.clients.mysql_client_manager import dw_mysql_client_manager

    async def test():
        
        dw_mysql_client_manager.init_client()
        async with dw_mysql_client_manager.session_factory() as session:
            repo = DwMysqlRepository(session)
            column_types = await repo.get_cloumn_types("dim_customer")
            print(column_types)
            column_values = await repo.get_cloumn_values("dim_customer", "customer_name")
            print(column_values)


    asyncio.run(test())