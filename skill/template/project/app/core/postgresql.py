"""
PostgreSQL异步数据库连接模块
提供SQLAlchemy异步引擎和会话管理
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool
from loguru import logger

from .config import settings


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    def create_engine(self) -> AsyncEngine:
        """创建异步数据库引擎"""
        if self._engine is None:
            self._engine = create_async_engine(
                settings.database_url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_pre_ping=True,  # 连接前验证
                echo=settings.debug,  # 开发环境显示SQL
                # 生产环境使用NullPool避免连接池问题
                poolclass=NullPool if settings.is_production else None,
            )
            logger.info(f"数据库引擎已创建: {settings.database_url}")
        return self._engine
    
    async def create_session_factory(self):
        """创建会话工厂"""
        if self._session_factory is None:
            if self._engine is None:
                self.create_engine()
            
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            logger.info("数据库会话工厂已创建")
        return self._session_factory
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        session_factory = await self.create_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"数据库会话错误: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self):
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            logger.info("数据库引擎已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的便捷函数
    用作FastAPI路由的依赖注入
    """
    async for session in db_manager.get_session():
        yield session


# 同步数据库连接（供Celery任务使用）
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class SyncDatabaseManager:
    """同步数据库管理器（供Celery使用）"""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
    
    def create_engine(self):
        """创建同步数据库引擎"""
        if self._engine is None:
            # 将异步URL转换为同步URL
            sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
            self._engine = create_engine(
                sync_url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_pre_ping=True,
                echo=settings.debug,
            )
            logger.info(f"同步数据库引擎已创建: {sync_url}")
        return self._engine
    
    def create_session_factory(self):
        """创建同步会话工厂"""
        if self._session_factory is None:
            if self._engine is None:
                self.create_engine()
            
            self._session_factory = sessionmaker(
                bind=self._engine,
                class_=Session,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            logger.info("同步数据库会话工厂已创建")
        return self._session_factory
    
    def get_session(self) -> Session:
        """获取同步数据库会话"""
        session_factory = self.create_session_factory()
        return session_factory()


# 全局同步数据库管理器实例
sync_db_manager = SyncDatabaseManager()


def get_sync_db() -> Session:
    """
    获取同步数据库会话的便捷函数
    用于Celery任务中的数据库操作
    """
    return sync_db_manager.get_session()