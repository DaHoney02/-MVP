from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1.路径处理：定位项目根目录，吧sqlite db放在项目data文件夹
PROJECT_ROOT=Path(__file__).resolve().parents[2]
DATA_DIR=PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True,exist_ok=True)
# 连接数据库   as_posix（）---把windows反斜杠\转成/,sqlit必用\
DATABASE_URL=f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"

# 2.数据库引擎:负责底层连接
engine=create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False}
    #connect_args：传给底层启动的参数，SQLite专属
    # check_same_thread：fastAPI为多线程处理请求，需关闭
)

# 3.会话工厂:用于生成数据库会话对象
SessionLocal=sessionmaker(
    bind=engine,  #绑定引擎
    autoflush=False,  #False惯例，每次查询前自动刷新
    autocommit=False   #默认False->手动db.commit()才写入库中，True->每步操作自动提交事务
)

# 4.ORM模型基类:所有表模型都要继承它
class Base(DeclarativeBase):
    pass

# 5.依赖函数:被fastAPI依赖注入使用,每次请求拿到db会话，自动关闭
def get_db():
    """为异常请求提供数据库会话，并在结束后关闭"""
    db=SessionLocal()
    try:
        yield db  #yield->生成器函数，fastAPI depends专用
    finally:
        db.close()  #会话一完，就close（）

# 6.初始化建表函数
def init_db():
    """创建不存在的数据表"""
    # 导入模型，让SQLAlchemy知道需要创建哪些表科目
    from app.db import models

    Base.metadata.create_all(bind=engine)