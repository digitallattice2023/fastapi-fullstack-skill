"""
自定义异常类
支持携带结构化错误码，供全局异常处理器使用。
"""

from fastapi import HTTPException
from app.shared.error_codes import ErrorCode


class AppException(HTTPException):
    """
    应用级异常，支持携带结构化错误码。

    用法:
        raise AppException(
            status_code=404,
            detail="项目不存在",
            error_code=ErrorCode.NOT_FOUND
        )
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: ErrorCode | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
