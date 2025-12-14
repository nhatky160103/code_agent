"""Pydantic-based configuration management"""
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # API Keys
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    google_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    
    # Workspace
    workspace_path: str = Field(default=".", description="Workspace directory path")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Custom log file path")
    enable_metrics_server: bool = Field(default=False, description="Enable Prometheus metrics server")
    metrics_port: int = Field(default=8000, description="Prometheus metrics server port")
    
    # Caching
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    cache_dir: Optional[str] = Field(default=None, description="Cache directory path")
    cache_size_limit: int = Field(default=2**30, description="Cache size limit in bytes (1GB)")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_max_calls: int = Field(default=60, description="Max calls per period")
    rate_limit_period: int = Field(default=60, description="Rate limit period in seconds")
    
    # Retry Configuration
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_initial_wait: float = Field(default=1.0, description="Initial retry wait time (seconds)")
    retry_max_wait: float = Field(default=60.0, description="Maximum retry wait time (seconds)")
    retry_exponential_base: float = Field(default=2.0, description="Exponential backoff base")
    enable_circuit_breaker: bool = Field(default=True, description="Enable circuit breaker")
    
    # LLM Configuration
    default_model: str = Field(default="code", description="Default model type (code/general/fast)")
    temperature: float = Field(default=0.7, description="LLM temperature")
    max_tokens: int = Field(default=2000, description="Maximum tokens per request")
    
    # Model Presets
    free_models: dict = Field(
        default={
            "code": "tngtech/deepseek-r1t2-chimera:free",
            "general": "openai/gpt-oss-20b:free",
            "fast": "google/gemma-3-27b-it:free",
        },
        description="Free model presets for OpenRouter"
    )
    
    google_models: dict = Field(
        default={
            "general": "gemini-2.5-flash",
            "code": "gemini-2.5-flash",
            "fast": "gemini-2.5-flash",
        },
        description="Google Gemini model presets"
    )
    
    # API Configuration
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )
    request_timeout: int = Field(default=60, description="HTTP request timeout in seconds")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("workspace_path")
    @classmethod
    def validate_workspace_path(cls, v: str) -> str:
        """Validate and expand workspace path"""
        path = Path(v).expanduser().resolve()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory path"""
        workspace = Path(self.workspace_path)
        return workspace / "logs"
    
    @property
    def cache_directory(self) -> Path:
        """Get cache directory path"""
        if self.cache_dir:
            return Path(self.cache_dir).expanduser().resolve()
        workspace = Path(self.workspace_path)
        return workspace / ".cache"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings

