"""Configuration package"""
from config.settings import Settings, get_settings, reload_settings
from config.config_legacy import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    GOOGLE_API_KEY,
    WORKSPACE_PATH,
    LOGS_DIR,
    FREE_MODELS,
    GOOGLE_MODELS,
    AGENT_ROLES,
)

# Re-export for convenience
__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    # Legacy exports for backward compatibility
    "OPENROUTER_API_KEY",
    "OPENROUTER_BASE_URL",
    "GOOGLE_API_KEY",
    "WORKSPACE_PATH",
    "LOGS_DIR",
    "FREE_MODELS",
    "GOOGLE_MODELS",
    "AGENT_ROLES",
]
