"""
用户认证模块数据模型
包含用户表模型、认证请求/响应模型等
使用BaseMixin模式最大化代码复用
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String, Boolean, DateTime
from pydantic import BaseModel, EmailStr, field_validator
from app.shared.models import BaseMixin
from app.shared.utils import utc_now


# ==================== 业务字段Mixin ====================

class UserBase(SQLModel):
    """
    用户业务字段基类
    包含所有用户相关的业务字段
    """
    email: str = Field(
        description="用户邮箱，孤一标识"
    )
    username: str = Field(
        min_length=3,
        max_length=50,
        description="用户名，孤一标识"
    )
    hashed_password: str = Field(
        description="加密后的密码"
    )
    is_active: bool = Field(
        default=True,
        description="用户是否激活"
    )
    is_admin: bool = Field(
        default=False,
        description="是否为管理员"
    )
    email_verified: bool = Field(
        default=False,
        description="邮箱是否已验证"
    )
    last_login: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="最后登录时间"
    )


# ==================== 表模型 ====================

class User(UserBase, BaseMixin, table=True):
    """用户表模型"""
    __tablename__ = "users"
    
    # 覆盖BaseMixin的updated_at字段，添加onupdate功能以支持自动更新
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=utc_now),
        description="更新时间"
    )


# 用户创建模型
class UserCreate(BaseModel):
    """用户注册请求模型"""
    email: EmailStr = Field(description="用户邮箱")
    username: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=8, max_length=128, description="密码")
    verification_code: str = Field(min_length=6, max_length=6, description="邮箱验证码")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


# 用户登录模型
class UserLogin(BaseModel):
    """用户登录请求模型"""
    email: EmailStr = Field(description="用户邮箱")
    password: str = Field(description="密码")


# 用户更新模型
class UserUpdate(BaseModel):
    """用户信息更新模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """验证用户名格式"""
        if v is not None:
            if not v.replace("_", "").replace("-", "").isalnum():
                raise ValueError("用户名只能包含字母、数字、下划线和连字符")
            return v.lower()
        return v


# 密码修改模型
class PasswordChange(BaseModel):
    """密码修改请求模型"""
    old_password: str = Field(description="旧密码")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")
    verification_code: str = Field(min_length=6, max_length=6, description="邮箱验证码")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


# 密码重置模型
class PasswordReset(BaseModel):
    """密码重置请求模型"""
    email: EmailStr = Field(description="用户邮箱")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")
    verification_code: str = Field(min_length=6, max_length=6, description="邮箱验证码")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


# 验证码请求模型
class VerificationCodeRequest(BaseModel):
    """验证码请求模型"""
    email: EmailStr = Field(description="用户邮箱")
    purpose: str = Field(description="验证码用途：register|password_change|password_reset")
    
    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """验证用途"""
        allowed_purposes = ["register", "password_change", "password_reset"]
        if v not in allowed_purposes:
            raise ValueError(f"验证码用途必须是以下之一：{', '.join(allowed_purposes)}")
        return v


# ==================== 请求/响应模型 ====================

class UserResponse(BaseMixin):
    """
    用户信息响应模型
    仅包含可以安全返回给前端的字段，不包含hashed_password等敏感信息
    """
    email: str = Field(description="用户邮箱")
    username: str = Field(description="用户名")
    is_active: bool = Field(description="用户是否激活")
    is_admin: bool = Field(description="是否为管理员")
    email_verified: bool = Field(description="邮箱是否已验证")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")


# 令牌响应模型
class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")


# 令牌刷新模型
class TokenRefresh(BaseModel):
    """令牌刷新请求模型"""
    refresh_token: str = Field(description="刷新令牌")


# JWT载荷模型
class TokenPayload(BaseModel):
    """JWT令牌载荷模型"""
    sub: str = Field(description="用户ID")
    email: str = Field(description="用户邮箱")
    username: str = Field(description="用户名")
    is_admin: bool = Field(description="是否为管理员")
    exp: int = Field(description="过期时间戳")
    iat: int = Field(description="签发时间戳")
    type: str = Field(description="令牌类型：access|refresh")