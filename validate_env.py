#!/usr/bin/env python3
"""Script to validate .env file configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    from config.settings import get_settings, Settings
    from config.config_legacy import OPENROUTER_API_KEY, GOOGLE_API_KEY
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️  Warning: New settings module not available, using basic validation")

def validate_env_file():
    """Validate .env file format and required variables"""
    print("=" * 80)
    print("🔍 Validating .env File")
    print("=" * 80)
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ ERROR: .env file not found!")
        print("   Create .env file in the project root directory")
        print("   You can copy .env.example as a template")
        return False
    
    print(f"✅ Found .env file: {env_file.absolute()}")
    
    # Load .env
    load_dotenv()
    
    # Check required variables
    errors = []
    warnings = []
    
    # API Keys (at least one required)
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    google_key = os.getenv("GOOGLE_API_KEY", "")
    
    if not openrouter_key and not google_key:
        errors.append("❌ At least one API key is required: OPENROUTER_API_KEY or GOOGLE_API_KEY")
    else:
        if openrouter_key:
            if not openrouter_key.startswith("sk-or-v1-"):
                warnings.append("⚠️  OPENROUTER_API_KEY format may be incorrect (should start with 'sk-or-v1-')")
            else:
                print(f"✅ OPENROUTER_API_KEY: {openrouter_key[:15]}...")
        
        if google_key:
            if not google_key.startswith("AIza"):
                warnings.append("⚠️  GOOGLE_API_KEY format may be incorrect (should start with 'AIza')")
            else:
                print(f"✅ GOOGLE_API_KEY: {google_key[:15]}...")
    
    # Validate with pydantic-settings if available
    if SETTINGS_AVAILABLE:
        try:
            settings = get_settings()
            print("\n📋 Configuration loaded successfully:")
            print(f"   - Log Level: {settings.log_level}")
            print(f"   - Cache Enabled: {settings.cache_enabled}")
            print(f"   - Rate Limit Enabled: {settings.rate_limit_enabled}")
            print(f"   - Max Retries: {settings.max_retries}")
            print(f"   - Workspace Path: {settings.workspace_path}")
            print(f"   - Logs Directory: {settings.logs_dir}")
            print(f"   - Cache Directory: {settings.cache_directory}")
        except Exception as e:
            errors.append(f"❌ Error loading settings: {e}")
    else:
        warnings.append("⚠️  Cannot validate with pydantic-settings (module not available)")
    
    # Check optional variables format
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_log_levels:
        errors.append(f"❌ LOG_LEVEL='{log_level}' is invalid. Must be one of: {valid_log_levels}")
    else:
        print(f"✅ LOG_LEVEL: {log_level}")
    
    # Check boolean values
    bool_vars = [
        "CACHE_ENABLED",
        "RATE_LIMIT_ENABLED",
        "ENABLE_METRICS_SERVER",
        "ENABLE_CIRCUIT_BREAKER"
    ]
    
    for var in bool_vars:
        value = os.getenv(var, "").lower()
        if value and value not in ["true", "false", "1", "0", "yes", "no", ""]:
            warnings.append(f"⚠️  {var}='{value}' may be invalid (use true/false)")
    
    # Check numeric values
    try:
        metrics_port = int(os.getenv("METRICS_PORT", "8000"))
        if metrics_port < 1 or metrics_port > 65535:
            errors.append(f"❌ METRICS_PORT={metrics_port} is invalid (must be 1-65535)")
        else:
            print(f"✅ METRICS_PORT: {metrics_port}")
    except ValueError:
        errors.append("❌ METRICS_PORT must be a number")
    
    try:
        cache_ttl = int(os.getenv("CACHE_TTL", "3600"))
        if cache_ttl < 0:
            errors.append(f"❌ CACHE_TTL={cache_ttl} is invalid (must be >= 0)")
        else:
            print(f"✅ CACHE_TTL: {cache_ttl} seconds")
    except ValueError:
        errors.append("❌ CACHE_TTL must be a number")
    
    # Print results
    print("\n" + "=" * 80)
    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"   {error}")
        print("\n" + "=" * 80)
        return False
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
        print("\n" + "=" * 80)
        print("✅ .env file is valid (with warnings)")
        return True
    
    print("✅ .env file is valid!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = validate_env_file()
    exit(0 if success else 1)

