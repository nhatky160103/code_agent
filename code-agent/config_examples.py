# Configuration Examples for Intelligent Rate Limiter

# ============================================================================
# 1. FREE TIER CONFIGURATION (Conservative)
# ============================================================================
# Use này khi bạn có quota thấp hoặc sử dụng free tier
# Đặc điểm: Chậm nhưng ổn định, ít bị rate limit

FREE_TIER_CONFIG = {
    "max_requests_per_minute": 10,
    "max_concurrent_requests": 2,
    "base_delay_seconds": 8.0,
    "max_delay_seconds": 120.0,
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 180,
    "context_strategy": "SLIDING_WINDOW",
    "max_context_tokens": 20000,
    "enable_caching": True
}

# Sử dụng:
"""
from utils.llm_client import SmartLLMClient, ContextStrategy

llm = SmartLLMClient(
    max_requests_per_minute=10,
    base_delay_seconds=8.0,
    context_strategy=ContextStrategy.SLIDING_WINDOW,
    max_context_tokens=20000,
    enable_caching=True
)
"""

# ============================================================================
# 2. PAID TIER CONFIGURATION (Aggressive)
# ============================================================================
# Use khi bạn có quota cao và cần generate nhanh
# Đặc điểm: Nhanh, tận dụng tối đa quota

PAID_TIER_CONFIG = {
    "max_requests_per_minute": 30,
    "max_concurrent_requests": 5,
    "base_delay_seconds": 3.0,
    "max_delay_seconds": 60.0,
    "circuit_breaker_threshold": 8,
    "circuit_breaker_timeout": 120,
    "context_strategy": "HIERARCHICAL",
    "max_context_tokens": 40000,
    "enable_caching": True
}

# Sử dụng:
"""
llm = SmartLLMClient(
    max_requests_per_minute=30,
    base_delay_seconds=3.0,
    context_strategy=ContextStrategy.HIERARCHICAL,
    max_context_tokens=40000,
    enable_caching=True
)
"""

# ============================================================================
# 3. PRODUCTION CONFIGURATION (Balanced - RECOMMENDED)
# ============================================================================
# Best practice cho production environment
# Đặc điểm: Cân bằng giữa tốc độ và ổn định

PRODUCTION_CONFIG = {
    "max_requests_per_minute": 20,
    "max_concurrent_requests": 3,
    "base_delay_seconds": 5.0,
    "max_delay_seconds": 90.0,
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 180,
    "context_strategy": "HIERARCHICAL",
    "max_context_tokens": 30000,
    "enable_caching": True
}

# Sử dụng:
"""
llm = SmartLLMClient(
    max_requests_per_minute=20,
    base_delay_seconds=5.0,
    context_strategy=ContextStrategy.HIERARCHICAL,
    max_context_tokens=30000,
    enable_caching=True
)
"""

# ============================================================================
# 4. DEVELOPMENT CONFIGURATION (Fast iteration)
# ============================================================================
# Cho development/testing, ưu tiên tốc độ
# Đặc điểm: Nhanh, có thể accept một số failures

DEVELOPMENT_CONFIG = {
    "max_requests_per_minute": 25,
    "max_concurrent_requests": 4,
    "base_delay_seconds": 3.0,
    "max_delay_seconds": 60.0,
    "circuit_breaker_threshold": 7,
    "circuit_breaker_timeout": 120,
    "context_strategy": "SLIDING_WINDOW",
    "max_context_tokens": 25000,
    "enable_caching": True
}

# ============================================================================
# 5. BATCH PROCESSING CONFIGURATION
# ============================================================================
# Cho batch processing nhiều files cùng lúc
# Đặc điểm: Optimize cho throughput cao

BATCH_CONFIG = {
    "max_requests_per_minute": 25,
    "max_concurrent_requests": 5,
    "base_delay_seconds": 4.0,
    "max_delay_seconds": 80.0,
    "circuit_breaker_threshold": 6,
    "circuit_breaker_timeout": 150,
    "context_strategy": "HIERARCHICAL",
    "max_context_tokens": 30000,
    "enable_caching": True,
    "batch_size": 5,
    "delay_between_batches": 10.0
}

# ============================================================================
# 6. CRITICAL TASKS CONFIGURATION
# ============================================================================
# Cho tasks critical cần success rate cao nhất
# Đặc điểm: Chậm nhưng gần như không bao giờ fail

CRITICAL_CONFIG = {
    "max_requests_per_minute": 12,
    "max_concurrent_requests": 2,
    "base_delay_seconds": 7.0,
    "max_delay_seconds": 150.0,
    "circuit_breaker_threshold": 3,
    "circuit_breaker_timeout": 300,  # 5 minutes
    "context_strategy": "FULL_CONTEXT",
    "max_context_tokens": 35000,
    "enable_caching": True,
    "max_retries": 8  # More retries
}

# ============================================================================
# 7. NIGHT/OFF-PEAK CONFIGURATION
# ============================================================================
# Cho chạy vào ban đêm khi ít người dùng
# Đặc điểm: Aggressive, tận dụng API idle time

NIGHT_CONFIG = {
    "max_requests_per_minute": 35,
    "max_concurrent_requests": 6,
    "base_delay_seconds": 2.0,
    "max_delay_seconds": 45.0,
    "circuit_breaker_threshold": 10,
    "circuit_breaker_timeout": 90,
    "context_strategy": "HIERARCHICAL",
    "max_context_tokens": 40000,
    "enable_caching": True
}

# ============================================================================
# 8. CUSTOM CONFIGURATION BUILDER
# ============================================================================

def build_custom_config(
    api_tier="free",  # free, paid, enterprise
    priority="balanced",  # fast, balanced, stable
    task_type="general"  # general, batch, critical
):
    """
    Build custom configuration based on parameters
    
    Args:
        api_tier: Your API tier (affects quota)
        priority: What you prioritize (speed vs stability)
        task_type: Type of task (affects strategy)
    
    Returns:
        Dict with configuration
    """
    
    # Base configs by tier
    tier_configs = {
        "free": {
            "max_requests_per_minute": 10,
            "base_delay_seconds": 8.0
        },
        "paid": {
            "max_requests_per_minute": 25,
            "base_delay_seconds": 4.0
        },
        "enterprise": {
            "max_requests_per_minute": 40,
            "base_delay_seconds": 2.0
        }
    }
    
    # Adjustments by priority
    priority_adjustments = {
        "fast": {
            "multiplier": 1.2,
            "delay_multiplier": 0.7
        },
        "balanced": {
            "multiplier": 1.0,
            "delay_multiplier": 1.0
        },
        "stable": {
            "multiplier": 0.8,
            "delay_multiplier": 1.3
        }
    }
    
    # Context strategy by task type
    task_strategies = {
        "general": "HIERARCHICAL",
        "batch": "SLIDING_WINDOW",
        "critical": "FULL_CONTEXT"
    }
    
    # Build config
    base = tier_configs.get(api_tier, tier_configs["free"])
    adj = priority_adjustments.get(priority, priority_adjustments["balanced"])
    
    config = {
        "max_requests_per_minute": int(base["max_requests_per_minute"] * adj["multiplier"]),
        "base_delay_seconds": base["base_delay_seconds"] * adj["delay_multiplier"],
        "max_concurrent_requests": 3,
        "max_delay_seconds": 90.0,
        "circuit_breaker_threshold": 5,
        "circuit_breaker_timeout": 180,
        "context_strategy": task_strategies.get(task_type, "HIERARCHICAL"),
        "max_context_tokens": 30000,
        "enable_caching": True
    }
    
    return config

# Usage:
"""
# For free tier, prioritizing stability, general tasks
config = build_custom_config(
    api_tier="free",
    priority="stable",
    task_type="general"
)

llm = SmartLLMClient(**config)
"""

# ============================================================================
# 9. ENVIRONMENT-BASED CONFIGURATION
# ============================================================================

import os

def get_config_from_env():
    """
    Load configuration from environment variables
    Useful for deployment and CI/CD
    """
    return {
        "max_requests_per_minute": int(os.getenv("LLM_MAX_RPM", "20")),
        "max_concurrent_requests": int(os.getenv("LLM_MAX_CONCURRENT", "3")),
        "base_delay_seconds": float(os.getenv("LLM_BASE_DELAY", "5.0")),
        "max_delay_seconds": float(os.getenv("LLM_MAX_DELAY", "90.0")),
        "circuit_breaker_threshold": int(os.getenv("LLM_CIRCUIT_THRESHOLD", "5")),
        "circuit_breaker_timeout": int(os.getenv("LLM_CIRCUIT_TIMEOUT", "180")),
        "context_strategy": os.getenv("LLM_CONTEXT_STRATEGY", "HIERARCHICAL"),
        "max_context_tokens": int(os.getenv("LLM_MAX_CONTEXT_TOKENS", "30000")),
        "enable_caching": os.getenv("LLM_ENABLE_CACHE", "true").lower() == "true"
    }

# Set in .env file:
"""
LLM_MAX_RPM=20
LLM_BASE_DELAY=5.0
LLM_CONTEXT_STRATEGY=HIERARCHICAL
LLM_ENABLE_CACHE=true
"""

# ============================================================================
# 10. ADAPTIVE CONFIGURATION (Auto-tune)
# ============================================================================

class AdaptiveConfig:
    """
    Configuration that adapts based on observed metrics
    """
    
    def __init__(self, initial_config):
        self.config = initial_config
        self.metrics_history = []
    
    def update_from_metrics(self, metrics):
        """
        Auto-tune configuration based on performance
        
        Args:
            metrics: Dictionary with success_rate, avg_response_time, etc.
        """
        self.metrics_history.append(metrics)
        
        success_rate = metrics.get('success_rate', 1.0)
        avg_response_time = metrics.get('average_response_time', 3.0)
        
        # If success rate is low, be more conservative
        if success_rate < 0.8:
            self.config['max_requests_per_minute'] = max(
                10,
                int(self.config['max_requests_per_minute'] * 0.8)
            )
            self.config['base_delay_seconds'] *= 1.2
            print(f"⚠️  Low success rate, reducing speed")
        
        # If success rate is high and response time good, can be more aggressive
        elif success_rate > 0.95 and avg_response_time < 3.0:
            self.config['max_requests_per_minute'] = min(
                40,
                int(self.config['max_requests_per_minute'] * 1.1)
            )
            self.config['base_delay_seconds'] *= 0.9
            print(f"✅ High performance, increasing speed")
        
        return self.config

# Usage:
"""
adaptive_config = AdaptiveConfig(PRODUCTION_CONFIG.copy())

# After each batch
status = llm.get_status()
updated_config = adaptive_config.update_from_metrics(
    status['rate_limiter']['metrics']
)

# Apply new config (would need to recreate client or add update method)
"""

# ============================================================================
# CONFIGURATION SELECTION GUIDE
# ============================================================================

SELECTION_GUIDE = """
Chọn config phù hợp với tình huống của bạn:

1. FREE_TIER_CONFIG:
   ✓ Bạn dùng free tier hoặc quota thấp
   ✓ Ưu tiên ổn định hơn tốc độ
   ✓ Success rate > Speed

2. PAID_TIER_CONFIG:
   ✓ Bạn có paid account với quota cao
   ✓ Cần generate nhanh
   ✓ Speed > Delay time

3. PRODUCTION_CONFIG: ⭐ RECOMMENDED
   ✓ Cân bằng tốt nhất
   ✓ Phù hợp cho most use cases
   ✓ Proven settings

4. DEVELOPMENT_CONFIG:
   ✓ Local development
   ✓ Fast iteration cycles
   ✓ OK với occasional failures

5. BATCH_CONFIG:
   ✓ Generate nhiều files
   ✓ Batch processing
   ✓ High throughput needed

6. CRITICAL_CONFIG:
   ✓ Mission-critical tasks
   ✓ Must not fail
   ✓ OK với slow speed

7. NIGHT_CONFIG:
   ✓ Run vào off-peak hours
   ✓ Tận dụng idle API time
   ✓ Maximum throughput

8. Custom with build_custom_config():
   ✓ Tùy chỉnh theo nhu cầu
   ✓ Flexible parameters
   ✓ Fine-grained control

9. Environment-based:
   ✓ Deployment flexibility
   ✓ CI/CD integration
   ✓ Easy configuration management

10. Adaptive:
    ✓ Auto-tuning
    ✓ Learn from performance
    ✓ Self-optimizing
"""

print(SELECTION_GUIDE)
