
import asyncio
from pathlib import Path
import sys

from loguru import logger

from app.conf.app_config import app_config
from app.core.context import get_req_id, set_req_id

# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 绿色显示日志时间（精确到毫秒）
    "<level>{level: <8}</level> | "  # 按级别颜色显示日志级别（左对齐，占8个字符）
    "<magenta>request_id - {extra[request_id]}</magenta> | "  # 品红色显示request_id（从日志extra中获取）
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "  # 青色显示日志所在文件、函数、行号
    "<level>{message}</level>"  # 按级别颜色显示日志正文
)

# 移除Loguru默认的控制台输出(避免重复输出日志)
logger.remove()

def inject_req_id(record):
    # 获取当前请求id
    req_id = get_req_id()
    # 将req_id 存入日志记录的extra字段，供日志格式中{extra[request_id]}调用
    record["extra"]["request_id"] = req_id

# 给日志打补丁，使其在每条日志前执行inject_req_id函数，注入req_id
logger = logger.patch(inject_req_id)

# 如果配置中开启了控制台日志输出
if app_config.logging.console.enable:
    # 添加控制台日志输出器
    logger.add(
        sink=sys.stdout,
        level=app_config.logging.console.level,
        format=log_format
    )

# 如果配置中开启了文件日志输出
if app_config.logging.file.enable:
    # 解析日志文件存储目录
    path = Path(app_config.logging.file.path)
    # 递归创建日志目录(如果不存在)，已存在则不报错
    path.mkdir(parents=True, exist_ok=True)
    # 添加文件日志输出器
    logger.add(
        sink=path / "app.log",   # 日志文件完整路径
        level=app_config.logging.file.level,    # 文件日志输出级别
        format=log_format,  # 使用自定义的日志格式
        rotation=app_config.logging.file.rotation,  # 日志文件分割规则(如按大小/时间)
        retention=app_config.logging.file.retention,
        encoding="utf-8"
    )

if __name__ == "__main__":
    # logger.trace("这是 TRACE 级别的调试信息")  # 不会输出到控制台（控制台是 INFO），但会输出到文件
    # logger.debug("这是 DEBUG 级别的调试信息")    # 同上
    # logger.info("服务启动成功")                 # 控制台+文件都输出
    # logger.success("数据同步完成")              # Loguru 独有级别
    # logger.warning("内存使用率超过 80%")
    # logger.error("接口调用失败：超时")
    # logger.critical("数据库连接中断，服务停止")

    async def req1():
        token = set_req_id("111")
        print(token)
        # 模拟处理
        await asyncio.sleep(1)
        logger.info(get_req_id())

    async def req2():
        token = set_req_id("222")
        print(token)
        # 模拟处理
        await asyncio.sleep(1)
        logger.info(get_req_id())

    async def test():
        await asyncio.gather(req1(),req2())

    asyncio.run(test())