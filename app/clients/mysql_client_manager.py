import asyncio
from typing import Optional

from sqlalchemy import Select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from app.conf.app_config import app_config, DBConfig
from app.models.mysql.table_info_mysql import TableInfoMySQL


class MysqlClientManager:
    def __init__(self, config: DBConfig):
        self.config = config
        self.client: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

    def _get_url(self):
        # 获取连接字符串
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}/{self.config.database}?charset=utf8mb4"

    def init_client(self):
        #初始化
        self.client = create_async_engine(
            self._get_url(),
            pool_size = 10,     # 连接池大小
            max_overflow = 5,   # 临时连接个数
        )
        self.session_factory = async_sessionmaker(
            self.client,
            autoflush = False,  # 查询看不见前面未提交的修改
            autobegin = True,   # 自动开启事务
        )
    
    async def close(self):
        # 释放资源
        await self.client.dispose()

# 创建针对dw库的客户端管理器
dw_mysql_client_manager = MysqlClientManager(app_config.db_dw)
# 创建针对meta库的客户端管理器
meta_mysql_client_manager = MysqlClientManager(app_config.db_meta)

if __name__ == "__main__":

    async def test():
        # 初始化dw客户端对象
        dw_mysql_client_manager.init_client()

        # 创建异步会话
        async with dw_mysql_client_manager.session_factory() as session:
            session: AsyncSession   # 声明类型方便后续使用

            # 执行查询sql
            sql = "select * from dim_customer limit 2"
            result = await session.execute(text(sql))

            # 读取数据
            rows = result.scalars().all()
            for row in rows:
                print(row)

        # 释放资源
        await dw_mysql_client_manager.close()

    # 测试orm的添加和查询
    async def test_orm():
        # 初始化meta客户端对象
        meta_mysql_client_manager.init_client()

        # 创建异步会话
        async with meta_mysql_client_manager.session_factory() as session:
            session: AsyncSession   # 声明类型方便后续使用

            # 添加一条数据
            info1 = TableInfoMySQL(
                id="dim_customer1",
                name="dim_customer1",
                role="dim",
                description="客户信息维度表1"
            )
            
            # 再添加一条数据
            info2 = TableInfoMySQL(
                id="dim_customer2",
                name="dim_customer2",
                role="dim",
                description="客户信息维度表2"
            )
            session.add_all([info1,info2])

            # 提交事务
            await session.commit()

            # 查询一条记录
            table_info = await session.get(TableInfoMySQL, "dim_customer2")
            print(table_info.description)

            # 查询多条记录
            result = await session.execute(Select(TableInfoMySQL).limit(2))
            rows: list[TableInfoMySQL] = result.scalars().all()
            print(rows)
            print(rows[0].description)

            # 看是否可以在提交事务后读取ORM对象属性
            print(info1.name)

        # 释放资源
        await meta_mysql_client_manager.close()

    # 测试ORM的更新和删除
    async def test_orm2():
        # 初始化meta客户端对象
        meta_mysql_client_manager.init_client()
    
        # 创建异步会话
        async with meta_mysql_client_manager.session_factory() as session:
            session: AsyncSession   # 声明类型方便后续使用

            # 更行一条语句
            table_info = await session.get(TableInfoMySQL, "dim_customer1")
            print(table_info)
            table_info.description = "aaa"

            # 删除一条数据
            await session.delete(table_info) 

            # 提交事务
            await session.commit()
            
        # 释放资源
        await meta_mysql_client_manager.close()

    asyncio.run(test_orm2())