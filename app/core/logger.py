import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger():
    #创建日志目录
    os.makedirs("logs",exist_ok=True)
    logger=logging.getLogger()
    logger.setLevel(logging.INFO)

    # 日志格式
    formatter=logging.Formatter(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s")

    #控制台输出
    console=logging.StreamHandler()
    console.setFormatter(formatter)

    #文件输出
    file_handler=RotatingFileHandler(
        "logs/app.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger
