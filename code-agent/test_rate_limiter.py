"""
Quick Test Script for Rate Limiter
Tests the intelligent rate limiting system
"""

import asyncio
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from utils.llm_client import SmartLLMClient, LLMProvider, ContextStrategy
from utils.rate_limiter import Priority, AdaptiveRateLimiter
from utils.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("test_rate_limiter")


async def test_basic_rate_limiting():
    """Test basic rate limiting functionality"""
    print("🧪 Test 1: Basic Rate Limiting")
    print("=" * 60)
    
    limiter = AdaptiveRateLimiter(
        max_requests_per_minute=10,
        max_concurrent_requests=2,
        base_delay_seconds=2.0
    )
    
    async def mock_api_call(task_id: int):
        """Simulate API call"""
        print(f"  📞 Calling API for task {task_id}")
        await asyncio.sleep(0.5)  # Simulate API latency
        return f"Response for task {task_id}"
    
    # Test multiple requests
    tasks = []
    for i in range(5):
        tasks.append(
            limiter.execute_with_retry(
                mock_api_call,
                i,
                priority=Priority.MEDIUM,
                context=f"Task {i}"
            )
        )
    
    results = await asyncio.gather(*tasks)
    
    print(f"\n✅ Completed {len(results)} requests")
    print(f"📊 Status: {limiter.get_status()}")
    print()


async def test_priority_queue():
    """Test priority-based execution"""
    print("🧪 Test 2: Priority Queue")
    print("=" * 60)
    
    limiter = AdaptiveRateLimiter(
        max_requests_per_minute=5,
        base_delay_seconds=1.0
    )
    
    async def prioritized_task(name: str, priority: Priority):
        print(f"  🎯 Executing {name} (Priority: {priority.name})")
        await asyncio.sleep(0.3)
        return f"{name} completed"
    
    # Submit tasks with different priorities
    tasks = [
        limiter.execute_with_retry(
            prioritized_task, "Low priority task", Priority.LOW,
            priority=Priority.LOW, context="Low task"
        ),
        limiter.execute_with_retry(
            prioritized_task, "Critical task", Priority.CRITICAL,
            priority=Priority.CRITICAL, context="Critical task"
        ),
        limiter.execute_with_retry(
            prioritized_task, "High priority task", Priority.HIGH,
            priority=Priority.HIGH, context="High task"
        ),
        limiter.execute_with_retry(
            prioritized_task, "Medium priority task", Priority.MEDIUM,
            priority=Priority.MEDIUM, context="Medium task"
        ),
    ]
    
    results = await asyncio.gather(*tasks)
    
    print(f"\n✅ All tasks completed")
    print(f"📊 Final status: {limiter.get_status()}")
    print()


async def test_circuit_breaker():
    """Test circuit breaker activation"""
    print("🧪 Test 3: Circuit Breaker")
    print("=" * 60)
    
    limiter = AdaptiveRateLimiter(
        max_requests_per_minute=10,
        circuit_breaker_threshold=3,
        circuit_breaker_timeout=10  # 10 seconds for test
    )
    
    call_count = 0
    
    async def failing_api_call():
        """Simulate failing API"""
        nonlocal call_count
        call_count += 1
        print(f"  ❌ API call {call_count} failed (simulated)")
        raise Exception("Simulated rate limit error: 429 Too Many Requests")
    
    # Try to make requests that will fail
    print("Making requests that will fail...")
    try:
        for i in range(5):
            try:
                await limiter.execute_with_retry(
                    failing_api_call,
                    max_retries=2,
                    priority=Priority.LOW,
                    context=f"Failing task {i}"
                )
            except Exception as e:
                print(f"  ⚠️  Request {i} failed after retries")
                if "Circuit breaker" in str(e):
                    print(f"  🔌 Circuit breaker activated!")
                    break
    except Exception as e:
        print(f"  🛑 Stopped: {str(e)[:100]}")
    
    print(f"\n📊 Status: {limiter.get_status()}")
    print(f"🔌 Circuit open: {limiter.get_status()['circuit_breaker_open']}")
    print()


async def test_llm_client():
    """Test actual LLM client (if API key available)"""
    print("🧪 Test 4: LLM Client Integration")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("  ⚠️  GEMINI_API_KEY not set, skipping LLM test")
        print("  💡 Set API key to test: export GEMINI_API_KEY='your-key'")
        return
    
    print("  🔧 Initializing LLM client...")
    llm = SmartLLMClient(
        provider=LLMProvider.GEMINI,
        api_key=api_key,
        max_requests_per_minute=15,
        context_strategy=ContextStrategy.SLIDING_WINDOW
    )
    
    # Test simple generation
    print("  📝 Generating simple response...")
    try:
        response = await llm.generate_async(
            prompt="Say 'Hello, rate limiter!' in a creative way.",
            priority=Priority.MEDIUM,
            context="Test generation"
        )
        print(f"  ✅ Response: {response[:100]}...")
        
        # Test batch generation
        print("\n  📚 Testing batch generation...")
        responses = llm.batch_generate([
            {
                'prompt': 'Count from 1 to 3',
                'priority': Priority.LOW,
                'context': 'Counting test'
            },
            {
                'prompt': 'Name 3 colors',
                'priority': Priority.MEDIUM,
                'context': 'Colors test'
            }
        ])
        
        print(f"  ✅ Generated {len(responses)} responses")
        
        # Show statistics
        status = llm.get_status()
        print(f"\n  📊 LLM Client Statistics:")
        print(f"     Total requests: {status['rate_limiter']['metrics']['total_requests']}")
        print(f"     Success rate: {status['rate_limiter']['metrics']['success_rate']:.1%}")
        print(f"     Avg response time: {status['rate_limiter']['metrics']['average_response_time']:.2f}s")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Intelligent Rate Limiter Test Suite")
    print("=" * 60)
    print()
    
    # Run tests
    await test_basic_rate_limiting()
    await test_priority_queue()
    await test_circuit_breaker()
    await test_llm_client()
    
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print()
    
    print("💡 Tips:")
    print("  - Adjust max_requests_per_minute based on your API quota")
    print("  - Use Priority.CRITICAL only for essential requests")
    print("  - Monitor success_rate in production")
    print("  - Circuit breaker activates after 5 consecutive failures")
    print()


if __name__ == "__main__":
    asyncio.run(main())
