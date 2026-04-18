"""
结构化错误码枚举
为每个错误场景提供 AI 可读的修复建议（hint）。
"""

from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """
    结构化错误码枚举。
    每个错误码对应一个唯一的字符串标识，
    并可选附带 AI 可读的修复建议。
    """

    # --- 通用错误 ---
    UNKNOWN_ERROR = "ERR_UNKNOWN"
    INTERNAL_ERROR = "ERR_INTERNAL"

    # --- 认证/授权 ---
    UNAUTHORIZED = "ERR_UNAUTHORIZED"
    TOKEN_EXPIRED = "ERR_TOKEN_EXPIRED"
    TOKEN_INVALID = "ERR_TOKEN_INVALID"
    FORBIDDEN = "ERR_FORBIDDEN"
    INVALID_CREDENTIALS = "ERR_INVALID_CREDENTIALS"

    # --- 资源操作 ---
    NOT_FOUND = "ERR_NOT_FOUND"
    CONFLICT = "ERR_CONFLICT"
    VALIDATION_ERROR = "ERR_VALIDATION"
    BAD_REQUEST = "ERR_BAD_REQUEST"

    # --- 数据库 ---
    DATABASE_ERROR = "ERR_DATABASE"
    CONNECTION_ERROR = "ERR_CONNECTION"

    # --- 外部服务 ---
    EXTERNAL_SERVICE_ERROR = "ERR_EXTERNAL_SERVICE"
    RATE_LIMITED = "ERR_RATE_LIMITED"


# 错误码到修复建议的映射
# 这些建议会被全局异常处理器自动附加到响应中，
# 帮助 AI 快速定位和修复问题。
ERROR_HINTS: dict[ErrorCode, str] = {
    ErrorCode.UNAUTHORIZED: "检查请求头是否包含有效的 Authorization: Bearer <token>。如使用 Swagger，先通过 /api/auth/token 获取令牌。",
    ErrorCode.TOKEN_EXPIRED: "访问令牌已过期，请使用刷新令牌调用 /api/auth/refresh-token 获取新令牌。",
    ErrorCode.TOKEN_INVALID: "令牌格式不正确或签名验证失败。检查 SECRET_KEY 配置是否一致。",
    ErrorCode.FORBIDDEN: "当前用户权限不足。检查是否需要 is_admin 标志或特定角色。",
    ErrorCode.INVALID_CREDENTIALS: "邮箱或密码不正确。确认用户是否已注册且密码正确。",
    ErrorCode.NOT_FOUND: "请求的资源不存在。检查路径参数和数据库记录是否存在。",
    ErrorCode.CONFLICT: "资源冲突（如唯一字段重复）。检查是否有同名记录已存在。",
    ErrorCode.VALIDATION_ERROR: "请求参数验证失败。检查请求体字段类型和必填项是否符合 Pydantic 模型。",
    ErrorCode.BAD_REQUEST: "请求格式错误。检查 Content-Type 和请求体格式。",
    ErrorCode.DATABASE_ERROR: "数据库操作失败。查看详细错误信息，常见原因：约束违反、连接超时。",
    ErrorCode.CONNECTION_ERROR: "数据库或外部服务连接失败。检查 .env 中的连接配置和容器是否运行。",
}


def get_hint(error_code: ErrorCode) -> Optional[str]:
    """
    根据错误码获取 AI 可读的修复建议。

    Args:
        error_code: 错误码枚举值

    Returns:
        修复建议字符串，如无对应建议则返回 None
    """
    return ERROR_HINTS.get(error_code)
