"""
认证模块Celery任务
包含邮件发送、验证码生成/验证等异步任务
"""

import random
import string
import resend
from datetime import datetime, timezone
from typing import Optional

from celery import Celery
from loguru import logger

from app.celery_app import celery_app
from app.core.config import settings
from app.core.redis import get_sync_redis, redis_manager


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        """初始化Resend API密钥"""
        resend.api_key = settings.resend_api_key
    
    @staticmethod
    def _create_verification_email_html(code: str, purpose: str) -> str:
        """创建验证邮件HTML内容"""
        # 说明：purpose_text 的键须与 models.VerificationCodeRequest.validate_purpose 中的允许值保持一致
        # 允许值为：register | password_change | password_reset
        # 若出现不一致将导致这里的文案回退到默认 "Verification"，造成体验不统一
        purpose_text = {
            "register": "Account Registration",
            "password_change": "Password Change",
            "password_reset": "Password Reset"
        }.get(purpose, "Verification")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verification Code</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #333; }}
                .code-container {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
                .code {{ font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">{settings.app_name}</div>
                    <h2>{purpose_text} Verification</h2>
                </div>
                
                <p>Hello,</p>
                <p>Your verification code is:</p>
                
                <div class="code-container">
                    <div class="code">{code}</div>
                </div>
                
                <p>This code will expire in {settings.verification_code_expire_minutes} minutes.</p>
                <p>If you didn't request this verification, please ignore this email.</p>
                
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                    <p>&copy; 2024 {settings.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    

class VerificationCodeService:
    """验证码服务类"""
    
    @staticmethod
    def generate_code(length: int = None) -> str:
        """生成验证码"""
        if length is None:
            length = settings.verification_code_length
        
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def store_code_sync(email: str, code: str, purpose: str) -> bool:
        """同步存储验证码到Redis（用于Celery任务）"""
        try:
            # 使用全局同步Redis客户端
            redis_client = get_sync_redis()
            
            cache_key = f"{settings.app_name.lower()}:verification:{purpose}:{email}"
            
            # 存储验证码，设置过期时间
            redis_client.setex(
                cache_key,
                settings.verification_code_expire_minutes * 60,
                code
            )
            
            logger.info(f"验证码已存储: {email} - {purpose}")
            return True
            
        except Exception as e:
            logger.error(f"存储验证码失败: {str(e)}")
            return False

    
    @staticmethod
    async def verify_code(email: str, code: str, purpose: str, delete_on_success: bool = True) -> bool:
        """
        验证验证码
        
        Args:
            email: 用户邮箱
            code: 验证码
            purpose: 验证码用途
            delete_on_success: 验证成功后是否立即删除验证码（默认True保持向后兼容）
            
        Returns:
            验证是否成功
        """
        try:
            # 获取异步Redis客户端（无需await，因为get_client是同步方法返回异步客户端实例）
            redis_client = redis_manager.get_client()
            cache_key = f"{settings.app_name.lower()}:verification:{purpose}:{email}"
            
            # 获取存储的验证码
            stored_code = await redis_client.get(cache_key)
            
            if not stored_code:
                logger.warning(f"验证码不存在或已过期: {email} - {purpose}")
                return False
            
            # 验证码匹配检查（处理字符串和字节类型）
            stored_code_str = stored_code.decode() if isinstance(stored_code, bytes) else stored_code
            if stored_code_str != code:
                logger.warning(f"验证码不匹配: {email} - {purpose}")
                return False
            
            # 根据参数决定是否立即删除验证码
            if delete_on_success:
                await redis_client.delete(cache_key)
                logger.info(f"验证码验证成功并已删除: {email} - {purpose}")
            else:
                logger.info(f"验证码验证成功（未删除）: {email} - {purpose}")
            
            return True
            
        except Exception as e:
            logger.error(f"验证验证码失败: {str(e)}")
            return False
    
    @staticmethod
    async def delete_code(email: str, purpose: str) -> bool:
        """
        删除验证码（用于业务完成后手动删除）
        
        Args:
            email: 用户邮箱
            purpose: 验证码用途
            
        Returns:
            是否删除成功
        """
        try:
            redis_client = redis_manager.get_client()
            cache_key = f"{settings.app_name.lower()}:verification:{purpose}:{email}"
            await redis_client.delete(cache_key)
            logger.info(f"验证码已删除: {email} - {purpose}")
            return True
        except Exception as e:
            logger.error(f"删除验证码失败: {str(e)}")
            return False


# 邮件服务实例
email_service = EmailService()

# 验证码服务实例
verification_service = VerificationCodeService()


@celery_app.task(bind=True, max_retries=3)
def send_verification_email(self, email: str, purpose: str) -> dict:
    """
    发送验证码邮件任务
    
    Args:
        email: 收件人邮箱
        purpose: |password_change|password_reset）
        
    Returns:
        任务执行结果
    """
    try:
        logger.info(f"开始发送验证码邮件: {email} - {purpose}")
        
        # 生成验证码
        code = verification_service.generate_code()
        
        # 创建邮件HTML内容
        html_content = email_service._create_verification_email_html(code, purpose)
        
        # 设置邮件主题
        purpose_subjects = {
            "register": f"Welcome to {settings.app_name} - Email Verification",
        "password_change": f"{settings.app_name} - Password Change Verification",
        "password_reset": f"{settings.app_name} - Password Reset Verification"
        }
        subject = purpose_subjects.get(purpose, f"{settings.app_name} - Email Verification")
        
        # 使用Resend发送邮件
        params = {
            "from": settings.resend_from_email,
            "to": [email],
            "subject": subject,
            "html": html_content
        }
        
        # 发送邮件
        result = resend.Emails.send(params)
        logger.info(f"Resend邮件发送成功: {email} - ID: {result.get('id', 'unknown')}")
        
        # 存储验证码（使用同步方法，Celery任务函数必须是同步的）
        success = verification_service.store_code_sync(email, code, purpose)
        
        if not success:
            raise Exception("存储验证码失败")
        
        logger.info(f"验证码邮件发送成功: {email} - {purpose}")
        
        return {
            "success": True,
            "message": "Verification email sent successfully",
            "email": email,
            "purpose": purpose,
            "resend_id": result.get('id'),
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"发送验证码邮件失败: {email} - {purpose} - {str(e)}")
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"重试发送邮件: {email} - 第{self.request.retries + 1}次")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send verification email: {str(e)}",
            "email": email,
            "purpose": purpose,
            "error": str(e)
        }


@celery_app.task
def cleanup_expired_codes() -> dict:
    """
    清理过期验证码任务（定时任务）
    Redis会自动过期，这个任务主要用于日志记录
    
    Returns:
        清理结果
    """
    try:
        logger.info("开始清理过期验证码")
        
        # Redis会自动处理过期键，这里主要记录日志
        cleanup_time = datetime.now(timezone.utc).isoformat()
        
        logger.info("过期验证码清理完成")
        
        return {
            "success": True,
            "message": "Expired verification codes cleanup completed",
            "cleanup_time": cleanup_time
        }
        
    except Exception as e:
        logger.error(f"清理过期验证码失败: {str(e)}")
        
        return {
            "success": False,
            "message": f"Failed to cleanup expired codes: {str(e)}",
            "error": str(e)
        }


@celery_app.task(name="app.features.auth.tasks.hello_world_task")
def hello_world_task():
    """
    定时任务示例：每20秒输出 Hello World
    这是一个简单的定时任务示例，用于验证 Celery Beat 调度器是否正常工作
    """
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = f"Hello World! 当前时间: {current_time}"
    
    logger.info(f"[定时任务] {message}")
    
    return {
        "success": True,
        "message": message,
        "timestamp": current_time
    }


# 验证码验证函数（供其他模块调用）
async def verify_verification_code(email: str, code: str, purpose: str, delete_on_success: bool = True) -> bool:
    """
    验证验证码
    
    Args:
        email: 用户邮箱
        code: 验证码
        purpose: 验证码用途
        delete_on_success: 验证成功后是否立即删除（默认True）
        
    Returns:
        验证是否成功
    """
    return await verification_service.verify_code(email, code, purpose, delete_on_success)


async def delete_verification_code(email: str, purpose: str) -> bool:
    """
    删除验证码（业务完成后调用）
    
    Args:
        email: 用户邮箱  
        purpose: 验证码用途
        
    Returns:
        是否删除成功
    """
    return await verification_service.delete_code(email, purpose)