"""
用户资料管理模块
提供用户资料查询、更新、注销相关的业务逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from loguru import logger

from app.core.config import settings
from app.core.redis import redis_manager
from ..models import UserUpdate, UserResponse
from .crud import get_user_by_id, get_user_by_username, update_user_field


async def get_user_profile(user_id: str, db: AsyncSession) -> UserResponse:
    """
    获取用户资料业务逻辑
    
    优先从缓存读取，缓存未命中则查询数据库
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        用户信息
        
    Raises:
        HTTPException: 获取失败时抛出异常
    """
    # 尝试从缓存读取用户信息
    try:
        redis_client = await redis_manager.get_client()
        cache_key = f"{settings.app_name.lower()}:user:info:{user_id}"
        cached_data = await redis_client.get(cache_key)
        
        if cached_data:
            logger.debug(f"从缓存读取用户资料: {user_id}")
            return UserResponse.model_validate_json(cached_data)
    except Exception as cache_error:
        logger.warning(f"读取用户缓存失败: {str(cache_error)}")
    
    # 缓存未命中，查询数据库
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 将查询结果写入缓存
    try:
        redis_client = await redis_manager.get_client()
        cache_key = f"{settings.app_name.lower()}:user:info:{user_id}"
        user_response = UserResponse.model_validate(user)
        await redis_client.setex(
            cache_key,
            settings.user_cache_expire_minutes * 60,
            user_response.model_dump_json()
        )
        logger.debug(f"用户资料已缓存: {user_id}")
    except Exception as cache_error:
        logger.warning(f"缓存用户资料失败: {str(cache_error)}")
    
    return UserResponse.model_validate(user)


async def update_user_profile(
    user_id: str, 
    update_data: UserUpdate, 
    db: AsyncSession
) -> UserResponse:
    """
    更新用户资料业务逻辑
    
    流程：
    1. 查找用户
    2. 检查用户名唯一性（如果更新用户名）
    3. 更新用户信息
    4. 清除用户缓存
    
    Args:
        user_id: 用户ID
        update_data: 更新数据
        db: 数据库会话
        
    Returns:
        更新后的用户信息
        
    Raises:
        HTTPException: 更新失败时抛出异常
    """
    # 查找用户
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 准备更新数据
    update_values = {}
    
    # 检查用户名是否需要更新
    if update_data.username is not None:
        # 检查用户名是否已被其他用户使用
        existing_user = await get_user_by_username(db, update_data.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        update_values["username"] = update_data.username
    
    # 执行更新
    if update_values:
        updated_user = await update_user_field(db, user_id, **update_values)
        
        # 清除用户缓存（数据已变更）
        try:
            redis_client = await redis_manager.get_client()
            cache_key = f"{settings.app_name.lower()}:user:info:{user_id}"
            await redis_client.delete(cache_key)
            logger.debug(f"已清除用户缓存: {user_id}")
        except Exception as cache_error:
            logger.warning(f"清除用户缓存失败: {str(cache_error)}")
        
        logger.info(f"用户资料更新成功: {updated_user.email} - {user_id}")
        return UserResponse.model_validate(updated_user)
    
    # 无更新内容，返回原用户信息
    return UserResponse.model_validate(user)


async def logout_user(user_id: str) -> dict:
    """
    用户注销业务逻辑
    
    清除用户缓存信息
    
    Args:
        user_id: 用户ID
        
    Returns:
        注销结果
        
    Raises:
        HTTPException: 注销失败时抛出异常
    """
    try:
        # 清除用户缓存
        redis_client = await redis_manager.get_client()
        cache_key = f"{settings.app_name.lower()}:user:info:{user_id}"
        await redis_client.delete(cache_key)
        
        logger.info(f"用户注销成功: {user_id}")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"用户注销失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
