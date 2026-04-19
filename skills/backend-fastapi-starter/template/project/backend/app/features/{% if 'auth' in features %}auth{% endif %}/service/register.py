"""
用户注册模块
提供用户注册相关的业务逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from loguru import logger

from ..models import UserCreate, UserResponse
from ..dependencies import password_manager
from ..tasks import verify_verification_code, delete_verification_code
from .crud import get_user_by_email, get_user_by_username, create_user


async def register_user(user_data: UserCreate, db: AsyncSession) -> UserResponse:
    """
    用户注册业务逻辑
    
    流程：
    1. 验证邮箱验证码（不删除）
    2. 检查邮箱和用户名唯一性
    3. 创建新用户
    4. 删除验证码（完成业务后）
    
    Args:
        user_data: 用户注册数据
        db: 数据库会话
        
    Returns:
        注册成功的用户信息
        
    Raises:
        HTTPException: 注册失败时抛出异常
    """
    # 验证验证码（验证成功但不删除，等业务完成后再删除）
    is_code_valid = await verify_verification_code(
        user_data.email, 
        user_data.verification_code, 
        "register",
        delete_on_success=False  # 不立即删除
    )
    
    if not is_code_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    # 检查邮箱是否已存在
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 检查用户名是否已存在
    existing_username = await get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # 创建新用户（密码加密）
    hashed_password = password_manager.hash_password(user_data.password)
    new_user = await create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        email_verified=True,  # 通过验证码验证后直接设为已验证
        is_active=True
    )
    
    # 用户创建成功后删除验证码（防止重复使用）
    await delete_verification_code(user_data.email, "register")
    
    logger.info(f"用户注册成功: {new_user.email} - {new_user.id}")
    
    return UserResponse.model_validate(new_user)
