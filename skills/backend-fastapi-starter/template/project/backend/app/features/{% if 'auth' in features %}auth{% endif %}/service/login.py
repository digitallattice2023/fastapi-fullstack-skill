"""
用户登录模块
提供用户登录、令牌生成相关的业务逻辑
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from loguru import logger

from app.core.config import settings
from app.core.redis import redis_manager
from ..models import UserLogin, TokenResponse, UserResponse
from ..dependencies import password_manager, jwt_manager
from .crud import get_user_by_email, update_user_field


async def login_user(login_data: UserLogin, db: AsyncSession) -> TokenResponse:
    """
    用户登录业务逻辑
    
    流程：
    1. 根据邮箱查找用户
    2. 验证密码
    3. 更新最后登录时间
    4. 生成JWT令牌
    5. 缓存用户信息
    
    Args:
        login_data: 登录数据
        db: 数据库会话
        
    Returns:
        JWT令牌信息
        
    Raises:
        HTTPException: 登录失败时抛出异常
    """
    # 查找用户
    user = await get_user_by_email(db, login_data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 验证密码
    if not password_manager.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 更新最后登录时间
    await update_user_field(db, user.id, last_login=datetime.now(timezone.utc))
    
    # 生成JWT令牌
    access_token = jwt_manager.create_access_token(user)
    refresh_token = jwt_manager.create_refresh_token(user)
    
    # 缓存用户信息（提升后续请求性能）
    try:
        redis_client = await redis_manager.get_client()
        cache_key = f"{settings.app_name.lower()}:user:info:{user.id}"
        user_response = UserResponse.model_validate(user)
        await redis_client.setex(
            cache_key,
            settings.user_cache_expire_minutes * 60,
            user_response.model_dump_json()
        )
        logger.debug(f"用户信息已缓存: {user.id}")
    except Exception as cache_error:
        # 缓存失败不影响登录流程
        logger.warning(f"缓存用户信息失败: {str(cache_error)}")
    
    logger.info(f"用户登录成功: {user.email} - {user.id}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )
