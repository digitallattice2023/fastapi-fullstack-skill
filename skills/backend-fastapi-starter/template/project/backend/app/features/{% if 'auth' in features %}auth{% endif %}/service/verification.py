"""
验证码发送模块
提供邮箱验证码发送和频率限制功能
"""

from fastapi import HTTPException, status
from loguru import logger

from app.core.config import settings
from app.core.redis import redis_manager
from ..tasks import send_verification_email


async def send_code(email: str, purpose: str) -> dict:
    """
    发送验证码到指定邮箱
    
    Args:
        email: 用户邮箱
        purpose: 验证码用途（register/password_change/password_reset）
        
    Returns:
        发送结果（包含任务ID）
        
    Raises:
        HTTPException: 发送失败或频率限制
    """
    try:
        # 检查发送频率限制（防止滥用）
        redis_client = await redis_manager.get_client()
        rate_limit_key = f"{settings.app_name.lower()}:email_rate_limit:{email}"
        
        # 检查是否在冷却期内
        if await redis_client.exists(rate_limit_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another verification code"
            )
        
        # 设置冷却期（60秒）
        await redis_client.setex(rate_limit_key, 60, "1")
        
        # 异步发送邮件任务
        task = send_verification_email.delay(email, purpose)
        
        logger.info(f"验证码发送任务已创建: {email} - {purpose} - 任务ID: {task.id}")
        
        return {
            "success": True,
            "message": "Verification code sent successfully",
            "task_id": task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送验证码失败: {email} - {purpose} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code"
        )
