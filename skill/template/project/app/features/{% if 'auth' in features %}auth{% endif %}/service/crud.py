"""
用户CRUD操作模块
提供用户表的标准数据库增删改查操作
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from loguru import logger

from ..models import User


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    根据ID查询用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        用户对象或None
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    根据邮箱查询用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        
    Returns:
        用户对象或None
    """
    result = await db.execute(
        select(User).where(User.email == email, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    根据用户名查询用户
    
    Args:
        db: 数据库会话
        username: 用户名
        
    Returns:
        用户对象或None
    """
    result = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    hashed_password: str,
    email_verified: bool = False,
    is_active: bool = True
) -> User:
    """
    创建新用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        username: 用户名
        hashed_password: 加密后的密码
        email_verified: 邮箱是否已验证
        is_active: 用户是否激活
        
    Returns:
        创建的用户对象
        
    Raises:
        HTTPException: 创建失败时抛出异常
    """
    try:
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            email_verified=email_verified,
            is_active=is_active
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"用户创建成功: {email} - {new_user.id}")
        return new_user
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"用户创建失败-数据库约束错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"用户创建失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


async def update_user_field(
    db: AsyncSession,
    user_id: str,
    **update_values
) -> User:
    """
    更新用户字段
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        **update_values: 要更新的字段和值
        
    Returns:
        更新后的用户对象
        
    Raises:
        HTTPException: 更新失败时抛出异常
    """
    try:
        # 执行更新
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_values)
        )
        await db.commit()
        
        # 获取更新后的用户对象
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found after update"
            )
        
        logger.info(f"用户字段更新成功: {user_id} - {list(update_values.keys())}")
        return user
        
    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"用户更新失败-数据库约束错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed due to constraint violation"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"用户更新失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


async def delete_user(db: AsyncSession, user_id: str) -> bool:
    """
    删除用户（软删除：设置is_active=False）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        是否删除成功
        
    Raises:
        HTTPException: 删除失败时抛出异常
    """
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 软删除：设置is_active为False
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await db.commit()
        
        logger.info(f"用户删除成功（软删除）: {user_id}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"用户删除失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
