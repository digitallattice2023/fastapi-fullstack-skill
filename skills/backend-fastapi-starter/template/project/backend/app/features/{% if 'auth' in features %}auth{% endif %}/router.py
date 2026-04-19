"""
认证模块API路由
包含用户注册、登录、密码管理、用户资料等端点
"""

# 路由元数据（供自动发现机制使用）
ROUTER_PREFIX = "/api/auth"
ROUTER_TAGS = ["Authentication"]

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.postgresql import get_db
from app.shared.models import BaseResponse
from .models import (
    UserCreate, UserLogin, UserUpdate, PasswordChange,
    PasswordReset, VerificationCodeRequest, TokenResponse, 
    TokenRefresh, UserResponse
)
from . import service
from .dependencies import get_current_user, get_current_admin_user, rate_limit_dependency

# 创建路由器
router = APIRouter()


@router.post(
    "/send-verification-code",
    response_model=BaseResponse[dict],
    summary="发送验证码",
    description="向指定邮箱发送验证码，用于注册、密码修改等操作"
)
async def send_verification_code(
    request: VerificationCodeRequest,
    _: None = Depends(rate_limit_dependency)
):
    """发送验证码到指定邮箱"""
    logger.info(f"请求发送验证码: {request.email} - {request.purpose}")
    result = await service.send_code(request.email, request.purpose)
    return BaseResponse(data=result, message="Verification code sent successfully")


@router.post(
    "/register",
    response_model=BaseResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="使用邮箱验证码进行用户注册"
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency)
):
    """用户注册"""
    logger.info(f"用户注册请求: {user_data.email}")
    user = await service.register_user(user_data, db)
    return BaseResponse(data=user, message="User registered successfully")


@router.post(
    "/login",
    response_model=BaseResponse[TokenResponse],
    summary="用户登录",
    description="使用邮箱和密码进行用户登录"
)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency)
):
    """用户登录"""
    logger.info(f"用户登录请求: {login_data.email}")
    token_data = await service.login_user(login_data, db)
    return BaseResponse(data=token_data, message="Login successful")


@router.post(
    "/refresh-token",
    response_model=BaseResponse[TokenResponse],
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌"
)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """刷新访问令牌"""
    logger.info("请求刷新令牌")
    new_token_data = await service.refresh_token(token_data.refresh_token, db)
    return BaseResponse(data=new_token_data, message="Token refreshed successfully")

@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 密码模式获取令牌",
    description=(
        "遵循 OAuth2 password flow，通过账户密码颁发访问令牌。\n"
        "注意：Swagger UI 的 Username 字段请填写邮箱。"
    )
)
async def oauth2_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency)
):
    """按照 OAuth2 密码模式提供令牌获取端点
    说明：
    - Swagger UI 的 OAuth2 授权会向该端点发送 x-www-form-urlencoded 的表单（username、password）。
    - 我们将 username 当作邮箱来处理，以复用现有登录逻辑。
    - 返回值使用 TokenResponse 原始结构（不包裹 BaseResponse），这是为了兼容 Swagger UI 的授权流程，它会直接读取 access_token 与 token_type。
    """
    logger.info(f"OAuth2 登录请求: {form_data.username}")
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    token_data = await service.login_user(login_data, db)
    return token_data
        



@router.post(
    "/change-password",
    response_model=BaseResponse[dict],
    summary="修改密码",
    description="使用旧密码和验证码修改用户密码"
)
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency)
):
    """修改密码"""
    logger.info(f"用户 {current_user.email} 请求修改密码")
    result = await service.change_password(current_user.id, password_data, db)
    return BaseResponse(data=result, message="Password changed successfully")


@router.post(
    "/reset-password",
    response_model=BaseResponse[dict],
    summary="重置密码",
    description="使用邮箱验证码重置用户密码"
)
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency)
):
    """重置密码"""
    logger.info(f"用户 {reset_data.email} 请求重置密码")
    result = await service.reset_password(reset_data, db)
    return BaseResponse(data=result, message="Password reset successfully")


@router.post(
    "/logout",
    response_model=BaseResponse[dict],
    summary="用户注销",
    description="注销当前用户，清除缓存信息"
)
async def logout(
    current_user: UserResponse = Depends(get_current_user)
):
    """用户注销"""
    logger.info(f"用户 {current_user.email} 注销登录")
    result = await service.logout_user(current_user.id)
    return BaseResponse(data=result, message="Logged out successfully")


@router.get(
    "/profile",
    response_model=BaseResponse[UserResponse],
    summary="获取用户资料",
    description="获取当前用户的详细资料信息"
)
async def get_profile(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户资料"""
    logger.info(f"用户 {current_user.email} 获取资料")
    user_profile = await service.get_user_profile(current_user.id, db)
    return BaseResponse(data=user_profile, message="Profile retrieved successfully")


@router.put(
    "/profile",
    response_model=BaseResponse[UserResponse],
    summary="更新用户资料",
    description="更新当前用户的资料信息"
)
async def update_profile(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency)
):
    """更新用户资料"""
    logger.info(f"用户 {current_user.email} 更新资料")
    updated_user = await service.update_user_profile(current_user.id, update_data, db)
    return BaseResponse(data=updated_user, message="Profile updated successfully")


# 管理员专用端点
@router.get(
    "/admin/users/{user_id}",
    response_model=BaseResponse[UserResponse],
    summary="管理员获取用户信息",
    description="管理员获取指定用户的详细信息"
)
async def admin_get_user(
    user_id: str,
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员获取用户信息"""
    logger.info(f"管理员 {current_admin.email} 获取用户 {user_id} 信息")
    user_profile = await service.get_user_profile(user_id, db)
    return BaseResponse(data=user_profile, message="User profile retrieved successfully")