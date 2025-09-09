"""
日志配置模块
使用structlog进行结构化日志记录
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import EventDict


def add_request_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加请求ID到日志"""
    # 如果有request_id上下文变量，添加到日志中
    return event_dict


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """设置日志配置"""
    
    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )
    
    # 配置structlog处理器
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        add_request_id,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )