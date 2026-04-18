"""
认证模块依赖注入
包含JWT认证、密码加密、用户获取、限流等依赖
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from collections import defaultdict
from threading import Lock

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.postgresql import get_db
try:
    from app.core.redis import get_redis
except ImportError:
    get_redis = None
from .models import User, TokenPayload


# OAuth2 密码模式认证方案（用于 Swagger UI 账户密码登录）
# 说明：
# - 将原来的 HTTP Bearer 改为 OAuth2 的 password flow，以便在 Swagger UI 的 “Authorize” 中使用账户密码直接获取令牌。
# - tokenUrl 指向 /api/auth/token，该端点将按照 OAuth2 规范接收表单数据（username、password）并返回 access_token。
# - 这样不会改变实际业务的令牌校验逻辑，依旧使用 Bearer Token 进行资源访问，只是增加了获取令牌的方式。
security = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
# 可选认证方案：关闭自动错误抛出，以便在某些端点中允许未登录访问
security_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

# 内存限流器（生产环境建议使用Redis）
class RateLimiter:
    """简单的内存限流器"""
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        检查是否允许请求
        
        Args:
            key: 限流键（通常是用户ID）
            limit: 限制次数
            window: 时间窗口（秒）
        
        Returns:
            是否允许请求
        """
        now = time.time()
        
        with self._lock:
            # 清理过期请求
            self._requests[key] = [
                req_time for req_time in self._requests[key]
                if now - req_time < window
            ]
            
            # 检查是否超过限制
            if len(self._requests[key]) >= limit:
                return False
            
            # 记录当前请求
            self._requests[key].append(now)
            return True


async def rate_limit_dependency() -> None:
    """
    限流依赖函数
    每分钟最多100次认证请求
    """
    # 这里可以实现更复杂的限流逻辑
    # 目前作为占位符，实际限流在get_current_user_with_rate_limit中实现
    pass


class PasswordManager:
    """密码管理器"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed_password: 加密后的密码
            
        Returns:
            密码是否正确
        """
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )


class JWTManager:
    """JWT令牌管理器"""
    
    @staticmethod
    def create_access_token(user: User) -> str:
        """
        创建访问令牌
        
        Args:
            user: 用户对象
            
        Returns:
            JWT访问令牌
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        
        payload = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def create_refresh_token(user: User) -> str:
        """
        创建刷新令牌
        
        Args:
            user: 用户对象
            
        Returns:
            JWT刷新令牌
        """
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        
        payload = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        """
        解码JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            令牌载荷
            
        Raises:
            HTTPException: 令牌无效或过期
        """
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            
            return TokenPayload(
                sub=payload.get("sub"),
                email=payload.get("email"),
                username=payload.get("username", ""),
                is_admin=payload.get("is_admin", False),
                type=payload.get("type", "access"),
                exp=payload.get("exp"),
                iat=payload.get("iat")
            )
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            ) from e


# 全局实例
rate_limiter = RateLimiter()
password_manager = PasswordManager()
jwt_manager = JWTManager()


async def get_current_user_from_token(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis) if get_redis else None,
) -> User:
    """
    从JWT令牌获取当前用户（兼容 OAuth2 密码模式）
    
    Args:
        token: Bearer 令牌字符串（由 OAuth2PasswordBearer 提取）
        db: 数据库会话
        redis: Redis客户端
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败
    """
    # 解码令牌
    # 这里直接使用 OAuth2PasswordBearer 提取到的 Bearer Token 字符串进行解码
    token_payload = jwt_manager.decode_token(token)
    
    # 验证令牌类型
    if token_payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = token_payload.sub

    # 尝试从Redis缓存获取用户信息（仅当redis可用时）
    if redis is not None:
        try:
            cache_key = f"{settings.app_name.lower()}:user:info:{user_id}"
            cached_user = await redis.get(cache_key)

            if cached_user:
                # 解析缓存的用户数据
                import ast
                user_dict = ast.literal_eval(cached_user)

                # 创建User对象（仅用于返回，不包含敏感信息）
                return User(
                    id=user_dict["id"],
                    email=user_dict["email"],
                    username=user_dict["username"],
                    is_active=user_dict["is_active"],
                    is_admin=user_dict["is_admin"],
                    email_verified=user_dict["email_verified"],
                    created_at=datetime.fromisoformat(user_dict["created_at"]) if user_dict.get("created_at") else None,
                    updated_at=datetime.fromisoformat(user_dict["updated_at"]) if user_dict.get("updated_at") else None,
                    last_login=datetime.fromisoformat(user_dict["last_login"]) if user_dict.get("last_login") else None,
                    hashed_password=""  # 不返回密码
                )

        except Exception as cache_error:
            # 缓存失败不影响认证流程
            pass
    
    # 从数据库获取用户信息
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


async def get_current_user_with_rate_limit(
    user: User = Depends(get_current_user_from_token)
) -> User:
    """
    获取当前用户并应用限流
    
    Args:
        user: 当前用户
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 超过限流限制
    """
    # 应用限流：每分钟最多100次请求
    if not rate_limiter.is_allowed(user.id, 100, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    
    return user


async def get_current_admin_user(
    user: User = Depends(get_current_user_with_rate_limit)
) -> User:
    """
    获取当前管理员用户
    
    Args:
        user: 当前用户
        
    Returns:
        管理员用户对象
        
    Raises:
        HTTPException: 非管理员用户
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


async def get_optional_current_user(
    token: Optional[str] = Depends(security_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    获取可选的当前用户（用于可选认证的端点）
    
    Args:
        token: Bearer 令牌字符串（可选）
        db: 数据库会话
        
    Returns:
        当前用户对象或None
    """
    if not token:
        return None
    
    try:
        return await get_current_user_from_token(token, db)
    except HTTPException:
        return None


# 导出常用依赖
get_current_user = get_current_user_with_rate_limit
get_current_admin = get_current_admin_user