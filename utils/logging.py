"""Structured logging and metrics for Code Agent"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from config import LOGS_DIR


# Prometheus Metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['agent', 'model', 'status']
)

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['agent', 'model']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens processed',
    ['agent', 'model', 'type']  # type: input or output
)

workflow_duration = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['status']
)

workflow_total = Counter(
    'workflow_total',
    'Total workflows executed',
    ['status']
)

active_workflows = Gauge(
    'active_workflows',
    'Currently active workflows'
)

agent_executions_total = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent', 'status']
)

agent_execution_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent']
)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_metrics_server: bool = False,
    metrics_port: int = 8000
) -> structlog.BoundLogger:
    """
    Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path. If None, uses daily log file in LOGS_DIR
        enable_metrics_server: Start Prometheus metrics HTTP server
        metrics_port: Port for metrics server
        
    Returns:
        Configured structlog logger
    """
    # Create logs directory
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Determine log file path
    if log_file is None:
        log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if log_file else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Add file handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # Start metrics server if enabled
    if enable_metrics_server:
        try:
            start_http_server(metrics_port)
            logger = structlog.get_logger()
            logger.info("metrics_server_started", port=metrics_port)
        except OSError:
            logger = structlog.get_logger()
            logger.warning("metrics_server_failed", port=metrics_port, reason="port_in_use")
    
    logger = structlog.get_logger()
    logger.info(
        "logging_initialized",
        log_level=log_level,
        log_file=str(log_file),
        metrics_enabled=enable_metrics_server
    )
    
    return logger


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Structlog logger instance
    """
    return structlog.get_logger(name)


def get_metrics():
    """Get metrics dictionary for easy access"""
    return {
        "llm_requests_total": llm_requests_total,
        "llm_request_duration": llm_request_duration,
        "llm_tokens_total": llm_tokens_total,
        "workflow_duration": workflow_duration,
        "workflow_total": workflow_total,
        "active_workflows": active_workflows,
        "agent_executions_total": agent_executions_total,
        "agent_execution_duration": agent_execution_duration,
    }

