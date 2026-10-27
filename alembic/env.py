
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from app.db.database import Base, engine
from app.db import models  # noqa: F401，确保 MessageRecord 注册到 Base.metadata


# 读取 alembic.ini 中的日志配置
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 告诉 Alembic：项目的数据表定义来自 Base.metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """不建立实时连接，按数据库 URL 生成迁移 SQL。"""
    context.configure(
        url=engine.url.render_as_string(hide_password=True),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """使用项目已配置的 SQLAlchemy Engine 执行迁移。"""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
