from typing import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from app.core.config import settings

# 1.构造postgreSQL连接地址
# 使用URL.create()
DATABASE_URL=URL.create(
    drivername="postgresql+psycopg",
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    database=settings.POSTGRES_DB
)

# 2.创建SQLAlchemy Engine
# Engine负责数据库连接池
engine=create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)
#3.创建数据库Session工厂
# 每请求通过SessionLocal（）获取独立的session
SessionLocal=sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=True
)

# 4.ORM模型的公共基类
# 继承Base
class Base(DeclarativeBase):
    pass

#5.FastAPI数据库依赖
# 每个请求获取自己的Session,请求结束后关闭Session
# Session关闭≠整个Engine，连接由连接池管理
class Session:
    pass


def get_db()->Generator[Session,None,None]:
    """向请求提供数据库会话，并在请求结束后释放会话资源"""
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

#6.
def init_db()->None:
    """开发或临时测试时创还能不存在的数据表"""
    from app.db import models  # 确保模型已注册到 Base.metadata

    Base.metadata.create_all(bind=engine)
