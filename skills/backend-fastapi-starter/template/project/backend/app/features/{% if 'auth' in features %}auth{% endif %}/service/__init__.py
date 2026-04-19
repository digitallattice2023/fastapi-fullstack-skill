"""
认证服务模块统一接口
按照功能模块导入并暴露所有业务逻辑函数
"""

# CRUD操作
from .crud import (
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
    create_user,
    update_user_field,
    delete_user
)

# 验证码发送
from .verification import send_code

# 用户注册
from .register import register_user

# 用户登录
from .login import login_user

# 密码管理
from .password import (
    change_password,
    reset_password,
    refresh_token
)

# 用户资料管理
from .profile import (
    get_user_profile,
    update_user_profile,
    logout_user
)

# 所有公共接口导出列表
__all__ = [
    # CRUD
    "get_user_by_id",
    "get_user_by_email",
    "get_user_by_username",
    "create_user",
    "update_user_field",
    "delete_user",
    # 验证码
    "send_code",
    # 注册
    "register_user",
    # 登录
    "login_user",
    # 密码
    "change_password",
    "reset_password",
    "refresh_token",
    # 资料
    "get_user_profile",
    "update_user_profile",
    "logout_user",
]
