"""
通用工具模块
提供ULID生成、时间处理等工具函数
"""

from datetime import datetime, timezone
from ulid import ULID


def generate_ulid() -> str:
    """
    生成ULID字符串
    ULID具有时间排序特性，适合作为数据库主键
    """
    return str(ULID())


def utc_now() -> datetime:
    """
    获取当前UTC时间
    Python 3.12推荐使用timezone.utc而不是utcnow()
    """
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式化字符串
    
    Returns:
        格式化后的日期时间字符串
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    解析日期时间字符串
    
    Args:
        dt_str: 日期时间字符串
        format_str: 格式化字符串
    
    Returns:
        日期时间对象
    """
    return datetime.strptime(dt_str, format_str).replace(tzinfo=timezone.utc)