"""
自定义日志模块
配置loguru日志格式，开发环境彩色输出，生产环境JSON结构化日志
拦截所有Python logging到loguru，统一日志输出格式
"""

import sys
import logging
from loguru import logger
from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    拦截Python标准logging并重定向到loguru
    用于统一FastAPI、SQLAlchemy、Uvicorn等库的日志格式
    """
    
    def emit(self, record):
        """
        将logging记录转换为loguru记录
        保持原有的日志级别和消息内容
        """
        # 获取对应的loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找调用者的帧信息，跳过logging和拦截器的帧
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename in [logging.__file__, __file__]:
            frame = frame.f_back
            depth += 1

        # 使用loguru记录日志，避免重复输出
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger():
    """
    配置loguru日志格式
    提供彩色输出和结构化日志
    拦截所有Python标准logging到loguru
    """
    # 移除默认处理器
    logger.remove()
    
    # 完全禁用Python标准logging的根记录器
    logging.getLogger().handlers.clear()
    
    # 拦截Python标准logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # 需要拦截的记录器列表及其日志级别配置
    loggers_config = {
        "": logging.DEBUG if settings.debug else logging.INFO,  # 根记录器
        "uvicorn": logging.INFO,  # 保留访问日志
        "uvicorn.error": logging.INFO,
        "uvicorn.access": logging.INFO,
        "fastapi": logging.INFO,
        # 完全禁用SQLAlchemy相关日志
        "sqlalchemy": logging.CRITICAL,
        "sqlalchemy.engine": logging.CRITICAL,
        "sqlalchemy.engine.Engine": logging.CRITICAL,
        "sqlalchemy.pool": logging.CRITICAL,
        "sqlalchemy.log": logging.CRITICAL,
        "sqlalchemy.orm": logging.CRITICAL,
        "alembic": logging.INFO,
        "celery": logging.INFO,
        "redis": logging.WARNING,  # 只显示警告和错误
        "boto3": logging.WARNING,  # 只显示警告和错误
        "botocore": logging.WARNING,  # 只显示警告和错误
        "urllib3": logging.WARNING,  # 只显示警告和错误
        "urllib3.connectionpool": logging.WARNING,
    }
    
    # 为每个记录器设置拦截处理器和日志级别
    for logger_name, log_level in loggers_config.items():
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers.clear()  # 清除现有处理器
        logging_logger.addHandler(InterceptHandler())
        logging_logger.setLevel(log_level)
        logging_logger.propagate = False
    
    # 额外禁用一些特定的SQLAlchemy日志记录器
    sqlalchemy_loggers = [
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool.impl.QueuePool",
        "sqlalchemy.pool.base",
        "sqlalchemy.dialects",
        "sqlalchemy.orm.mapper",
        "sqlalchemy.orm.unitofwork",
        "sqlalchemy.orm.strategies",
    ]
    
    for logger_name in sqlalchemy_loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers.clear()
        logging_logger.setLevel(logging.CRITICAL)
        logging_logger.propagate = False
        logging_logger.disabled = True  # 完全禁用这些记录器
    
    # 开发环境：彩色控制台输出
    if settings.debug:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level="DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # 开发环境文件日志
        logger.add(
            "logs/app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            colorize=False
        )
        
    else:
        # 生产环境：结构化JSON日志
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO",
            colorize=False,
            serialize=False  # 生产环境可以考虑启用JSON序列化
        )
        
        # 生产环境文件日志
        logger.add(
            "logs/app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO",
            rotation="50 MB",
            retention="30 days",
            compression="zip",
            colorize=False
        )
        
        # 生产环境错误日志
        logger.add(
            "logs/error.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="50 MB",
            retention="30 days",
            compression="zip",
            colorize=False
        )
    
    logger.info(f"日志已配置为 {settings.environment} 环境")


def get_logger(name: str = None):
    """
    获取logger实例
    
    Args:
        name: logger名称，默认为None使用根logger
    
    Returns:
        logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger