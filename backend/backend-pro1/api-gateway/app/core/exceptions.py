"""
异常处理模块
定义全局异常处理器和自定义异常
"""

from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog
from datetime import datetime


logger = structlog.get_logger()


class APIException(Exception):
    """自定义API异常基类"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(APIException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED"
        )


class AuthorizationError(APIException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_FAILED"
        )


class ValidationError(APIException):
    """验证异常"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value:
            details["value"] = value
            
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ResourceNotFoundError(APIException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource}未找到",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class ResourceConflictError(APIException):
    """资源冲突异常"""
    
    def __init__(self, message: str, resource: str = None):
        details = {}
        if resource:
            details["resource"] = resource
            
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details=details
        )


class RateLimitError(APIException):
    """限流异常"""
    
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED"
        )


def create_error_response(
    message: str,
    status_code: int,
    error_code: str = "ERROR",
    details: Dict[str, Any] = None,
    request_id: str = None
) -> JSONResponse:
    """创建标准错误响应"""
    
    error_data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if details:
        error_data["error"]["details"] = details
    
    if request_id:
        error_data["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API异常处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        "API异常",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        path=str(request.url),
        method=request.method,
        details=exc.details
    )
    
    return create_error_response(
        message=exc.message,
        status_code=exc.status_code,
        error_code=exc.error_code,
        details=exc.details,
        request_id=request_id
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        "HTTP异常",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=str(request.url),
        method=request.method
    )
    
    return create_error_response(
        message=exc.detail,
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        request_id=request_id
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """请求验证异常处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field_path = ".".join(str(x) for x in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.warning(
        "请求验证失败",
        errors=errors,
        request_id=request_id,
        path=str(request.url),
        method=request.method
    )
    
    return create_error_response(
        message="请求参数验证失败",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        details={"errors": errors},
        request_id=request_id
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        "未处理的异常",
        exception=str(exc),
        exception_type=type(exc).__name__,
        request_id=request_id,
        path=str(request.url),
        method=request.method,
        exc_info=True
    )
    
    # 生产环境不暴露详细错误信息
    message = "服务器内部错误，请稍后重试"
    details = None
    
    # 开发环境可以显示更多信息
    from shared.config import get_settings
    settings = get_settings()
    if settings.DEBUG:
        message = f"内部服务器错误: {str(exc)}"
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        details=details,
        request_id=request_id
    )


def setup_exception_handlers(app: FastAPI):
    """设置异常处理器"""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)