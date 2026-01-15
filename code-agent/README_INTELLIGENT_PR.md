# Intelligent Auto PR Generator

## 🎯 Tổng quan

Hệ thống tự động tạo code với **rate limit management thông minh**, được thiết kế để xử lý hiệu quả các giới hạn API thông qua nhiều chiến lược tiên tiến.

## ✨ Tính năng chính

### 1. **Adaptive Rate Limiting** 
- ✅ Token bucket algorithm cho rate limiting chính xác
- ✅ Exponential backoff với jitter để tránh thundering herd
- ✅ Circuit breaker tự động khi API quá tải
- ✅ Priority queue (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Adaptive delay dựa trên success rate và response time

### 2. **Intelligent Context Management**
- ✅ 4 chiến lược quản lý context:
  - **FULL_CONTEXT**: Giữ toàn bộ lịch sử (cho task ngắn)
  - **SLIDING_WINDOW**: Chỉ giữ N messages gần nhất (tiết kiệm token)
  - **SUMMARY**: Tóm tắt context cũ, giữ chi tiết mới (cân bằng)
  - **HIERARCHICAL**: Key points + recent details (tối ưu nhất)
- ✅ Tự động truncate khi vượt quá token limit
- ✅ Context-aware file generation với dependencies

### 3. **Smart File Generation**
- ✅ Tự động planning file structure dựa trên requirements
- ✅ Dependency-aware generation order
- ✅ Priority-based scheduling
- ✅ Automatic retry cho critical files
- ✅ Progress tracking và error recovery

### 4. **Professional Monitoring**
- ✅ Structured logging với structlog
- ✅ Real-time metrics tracking
- ✅ Success rate monitoring
- ✅ Response time analysis
- ✅ Detailed error reporting

## 🚀 Cài đặt

### 1. Clone repository

```bash
cd D:\20242\Code_agent\code-agent
```

### 2. Cài đặt dependencies

```bash
pip install google-generativeai structlog
# Hoặc cho OpenAI/Claude:
# pip install openai anthropic
```

### 3. Set API key

```bash
# Windows
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY=your-api-key-here
```

## 📖 Cách sử dụng

### Basic Usage

```bash
python auto_pr_intelligent.py
```

### Trong Code

```python
from utils.llm_client import SmartLLMClient, LLMProvider, ContextStrategy
from utils.rate_limiter import Priority

# Initialize client
llm = SmartLLMClient(
    provider=LLMProvider.GEMINI,
    max_requests_per_minute=15,  # Điều chỉnh theo quota của bạn
    context_strategy=ContextStrategy.HIERARCHICAL
)

# Generate với priority
response = llm.generate(
    prompt="Create a function to...",
    priority=Priority.HIGH,
    context="Generating core logic"
)

# Batch generation
responses = llm.batch_generate([
    {
        'prompt': 'Create index.html',
        'priority': Priority.CRITICAL,
        'context': 'Main entry point'
    },
    {
        'prompt': 'Create style.css',
        'priority': Priority.HIGH,
        'context': 'Styling'
    }
])
```

## 🎛️ Cấu hình

### Rate Limiter Settings

```python
from utils.rate_limiter import AdaptiveRateLimiter

limiter = AdaptiveRateLimiter(
    max_requests_per_minute=15,    # Số request tối đa/phút
    max_concurrent_requests=3,      # Số request đồng thời
    base_delay_seconds=5.0,         # Delay cơ bản
    max_delay_seconds=120.0,        # Delay tối đa
    circuit_breaker_threshold=5,    # Số lỗi liên tiếp để mở circuit
    circuit_breaker_timeout=180     # Thời gian chờ khi circuit mở (giây)
)
```

### Context Strategy

```python
# Cho task ngắn (< 5 files)
context_strategy=ContextStrategy.FULL_CONTEXT

# Cho task trung bình (5-15 files) - RECOMMENDED
context_strategy=ContextStrategy.HIERARCHICAL

# Cho task dài (> 15 files)
context_strategy=ContextStrategy.SLIDING_WINDOW
```

## 🔧 Troubleshooting

### Vấn đề: Rate Limit Liên Tục

**Triệu chứng:**
```
[LLM] Gemini rate-limit hit (attempt 1/3)
CIRCUIT BREAKER: Hit rate limit 5 times consecutively
```

**Giải pháp:**

1. **Giảm `max_requests_per_minute`:**
   ```python
   max_requests_per_minute=10  # Giảm từ 15 xuống 10
   ```

2. **Tăng `base_delay_seconds`:**
   ```python
   base_delay_seconds=10.0  # Tăng từ 5s lên 10s
   ```

3. **Đợi circuit breaker reset:**
   - Hệ thống tự động đợi 3 phút (180s) khi circuit mở
   - Sau đó tự động retry

4. **Sử dụng priority thấp hơn cho non-critical files:**
   ```python
   priority=Priority.LOW  # Thay vì HIGH/CRITICAL
   ```

### Vấn đề: Context quá dài

**Triệu chứng:**
```
[WARNING] context_truncated
```

**Giải pháp:**

1. **Chuyển sang SLIDING_WINDOW strategy:**
   ```python
   context_strategy=ContextStrategy.SLIDING_WINDOW
   ```

2. **Giảm `max_context_tokens`:**
   ```python
   max_context_tokens=20000  # Giảm từ 30000
   ```

### Vấn đề: File generation thất bại

**Triệu chứng:**
```
[ERROR] file_generation_failed
```

**Giải pháp:**

1. **Tự động retry cho CRITICAL files** (đã built-in)
2. **Kiểm tra dependencies:**
   ```python
   # Đảm bảo dependencies được generate trước
   dependencies=["index.html"]
   ```

3. **Xem log chi tiết:**
   ```bash
   # Log được lưu trong logs/
   tail -f logs/YYYY-MM-DD.log
   ```

## 📊 Monitoring & Metrics

### Xem status real-time

```python
# Trong code
status = llm.get_status()
print(f"Success rate: {status['rate_limiter']['metrics']['success_rate']:.1%}")
print(f"Tokens available: {status['rate_limiter']['tokens_available']}")
print(f"Active requests: {status['rate_limiter']['active_requests']}")
```

### Metrics được track

- ✅ Total requests
- ✅ Success/failure rate
- ✅ Average response time
- ✅ Rate limited requests count
- ✅ Consecutive failures
- ✅ Circuit breaker status
- ✅ Token bucket level

## 🎯 Best Practices

### 1. **Prioritize Correctly**

```python
# CRITICAL: Không thể thiếu
Priority.CRITICAL  # index.html, main.js

# HIGH: Core functionality
Priority.HIGH      # game logic, core components

# MEDIUM: Supporting files
Priority.MEDIUM    # utilities, helpers

# LOW: Optional
Priority.LOW       # documentation, examples
```

### 2. **Manage Context Wisely**

```python
# Cho simple tasks
ContextStrategy.FULL_CONTEXT

# Cho complex projects (RECOMMENDED)
ContextStrategy.HIERARCHICAL

# Cho very long tasks
ContextStrategy.SLIDING_WINDOW
```

### 3. **Handle Errors Gracefully**

```python
try:
    await generator.generate_all_files(requirements)
except Exception as e:
    logger.error("generation_failed", error=str(e))
    # Có thể resume từ checkpoint
```

### 4. **Monitor and Adjust**

```python
# Kiểm tra metrics sau mỗi batch
status = llm.get_status()

if status['rate_limiter']['metrics']['success_rate'] < 0.7:
    # Tăng delay
    delay_between_files *= 1.5
```

## 🔬 Advanced Features

### Custom Rate Limiting Strategy

```python
from utils.rate_limiter import AdaptiveRateLimiter

class CustomRateLimiter(AdaptiveRateLimiter):
    def _calculate_delay(self, attempt, priority):
        # Custom logic
        if priority == Priority.CRITICAL:
            return 3.0  # Aggressive retry
        return super()._calculate_delay(attempt, priority)
```

### Multi-Provider Fallback

```python
# Primary: Gemini
llm_gemini = SmartLLMClient(provider=LLMProvider.GEMINI)

# Fallback: OpenRouter
llm_fallback = SmartLLMClient(provider=LLMProvider.OPENROUTER)

try:
    response = llm_gemini.generate(prompt)
except RateLimitError:
    logger.warning("gemini_rate_limited_using_fallback")
    response = llm_fallback.generate(prompt)
```

### Checkpoint & Resume

```python
# Save progress
checkpoint = {
    'generated_files': generator.generated_files,
    'remaining_tasks': generator.generation_order[current_index:]
}

# Resume from checkpoint
generator.generated_files = checkpoint['generated_files']
for task in checkpoint['remaining_tasks']:
    await generator.generate_file(task, requirements)
```

## 📈 Performance Tips

1. **Batch similar files:**
   - Group CSS files together
   - Group JS components together
   - Reduces context switching

2. **Use caching:**
   - Enable `enable_caching=True`
   - Reuse common patterns

3. **Optimize delays:**
   - Start with `base_delay=5s`
   - Let adaptive algorithm adjust
   - Monitor success rate

4. **Smart priorities:**
   - Only mark truly critical files as CRITICAL
   - Most files should be MEDIUM
   - Use LOW for nice-to-have features

## 🆘 Support

### Logs Location
```
logs/YYYY-MM-DD.log
```

### Debug Mode
```python
# Enable detailed logging
import structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)
```

### Report Issues
Kiểm tra log file và báo cáo với:
- Error message đầy đủ
- Rate limiter metrics
- Context strategy đang dùng
- API provider và quota

## 📝 License

MIT License - Tự do sử dụng và customize

## 🙏 Credits

Built with:
- `google-generativeai` - Gemini API
- `structlog` - Structured logging
- `asyncio` - Async operations

---

**Made with ❤️ for professional developers who hate rate limits**
