"""
密码管理模块
提供密码修改、重置、令牌刷新相关的业务逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from loguru import logger

from app.core.config import settings
from app.core.redis import redis_manager
from ..models import PasswordChange, PasswordReset, TokenResponse, User
from ..dependencies import password_manager, jwt_manager
from ..tasks import verify_verification_code, delete_verification_code
from .crud import get_user_by_id, get_user_by_email, update_user_field


async def change_password(
    user_id: str, 
    password_data: PasswordChange, 
    db: AsyncSession
) -> dict:
    """
    修改密码业务逻辑
    
    流程：
    1. 查找用户
    2. 验证旧密码
    3. 验证验证码
    4. 更新密码
    5. 清除用户缓存
    
    Args:
        user_id: 用户ID
        password_data: 密码修改数据
        db: 数据库会话
        
    Returns:
        修改结果
        
    Raises:
        HTTPException: 修改失败时抛出异常
    """
    # 查找用户
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 验证旧密码
    if not password_manager.verify_password(
        password_data.old_password, 
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    # 验证验证码（验证成功但不删除，等密码更新完成后再删除）
    is_code_valid = await verify_verification_code(
        user.email, 
        password_data.verification_code, 
        "password_change",
        delete_on_success=False  # 不立即删除
    )
    
    if not is_code_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    # 更新密码
    new_hashed_password = password_manager.hash_password(password_data.new_password)
    await update_user_field(db, user_id, hashed_password=new_hashed_password)
    
    # 密码更新成功后删除验证码（防止重复使用）
    await delete_verification_code(user.email, "password_change")
    
    # 清除用户缓存（密码变更后强制重新加载）
    try:
        redis_client = await redis_manager.get_client()
        cache_key = f"{settings.app_name.lower()}:user:info:{user_id}"
        await redis_client.delete(cache_key)
        logger.debug(f"已清除用户缓存: {user_id}")
    except Exception as cache_error:
        logger.warning(f"清除用户缓存失败: {str(cache_error)}")
    
    logger.info(f"密码修改成功: {user.email} - {user.id}")
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


async def reset_password(reset_data: PasswordReset, db: AsyncSession) -> dict:
    """
    重置密码业务逻辑
    
    流程：
    1. 验证验证码（不删除）
    2. 查找用户
    3. 更新密码
    4. 删除验证码
    5. 清除用户缓存
    
    Args:
        reset_data: 密码重置数据
        db: 数据库会话
        
    Returns:
        重置结果
        
    Raises:
        HTTPException: 重置失败时抛出异常
    """
    # 验证验证码（验证成功但不删除，等密码重置完成后再删除）
    is_code_valid = await verify_verification_code(
        reset_data.email, 
        reset_data.verification_code, 
        "password_reset",
        delete_on_success=False  # 不立即删除
    )
    
    if not is_code_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    # 查找用户
    user = await get_user_by_email(db, reset_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 更新密码
    new_hashed_password = password_manager.hash_password(reset_data.new_password)
    await update_user_field(db, user.id, hashed_password=new_hashed_password)
    
    # 密码重置成功后删除验证码（防止重复使用）
    await delete_verification_code(reset_data.email, "password_reset")
    
    # 清除用户缓存
    try:
        redis_client = await redis_manager.get_client()
        cache_key = f"{settings.app_name.lower()}:user:info:{user.id}"
        await redis_client.delete(cache_key)
        logger.debug(f"已清除用户缓存: {user.id}")
    except Exception as cache_error:
        logger.warning(f"清除用户缓存失败: {str(cache_error)}")
    
    logger.info(f"密码重置成功: {user.email} - {user.id}")
    
    return {
        "success": True,
        "message": "Password reset successfully"
    }


async def refresh_token(refresh_token: str, db: AsyncSession) -> TokenResponse:
    """
    刷新访问令牌业务逻辑
    
    流程：
    1. 解码刷新令牌
    2. 验证令牌类型
    3. 查找用户
    4. 生成新的访问令牌和刷新令牌
    
    Args:
        refresh_token: 刷新令牌
        db: 数据库会话
        
    Returns:
        新的JWT令牌信息
        
    Raises:
        HTTPException: 刷新失败时抛出异常
    """
    # 解码刷新令牌
    token_payload = jwt_manager.decode_token(refresh_token)
    
    # 验证令牌类型
    if token_payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # 查找用户
    user = await get_user_by_id(db, token_payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # 生成新的令牌
    new_access_token = jwt_manager.create_access_token(user)
    new_refresh_token = jwt_manager.create_refresh_token(user)
    
    logger.info(f"令牌刷新成功: {user.email} - {user.id}")
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )
