"""
共享模型模块
包含基类模型、响应模型等通用数据结构
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional, Any
from sqlmodel import SQLModel, Field, Column, DateTime
from pydantic import BaseModel

from .utils import generate_ulid, utc_now


# 泛型类型变量
T = TypeVar('T')


class BaseMixin(SQLModel):
    """
    基础混入类
    包含所有通用字段：id、created_at、updated_at
    所有表模型都应继承此类
    """
    id: str = Field(
        default_factory=generate_ulid,
        primary_key=True,
        description="主键ID，使用ULID格式"
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        description="更新时间"
    )

class BaseResponse(BaseModel, Generic[T]):
    """
    API响应基类模型
    提供统一的响应格式
    成功时返回 data 和 message
    失败时由全局异常处理器生成响应，data 为 null，可选包含 error_code 和 hint
    """

    data: Optional[T] = Field(default=None, description="响应数据")
    message: str = Field(description="响应消息")
    error_code: Optional[str] = Field(default=None, description="结构化错误码（仅错误时返回）")
    hint: Optional[str] = Field(default=None, description="AI 可读的修复建议（仅错误时返回）")
    

class PaginationParams(BaseModel):
    """分页参数模型"""
    
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    
    items: list[T] = Field(description="数据项列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse[T]":
        """创建分页响应"""
        pages = (total + size - 1) // size  # 向上取整
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )