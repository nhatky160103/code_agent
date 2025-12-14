# Setup Guide - Sử dụng các Module Mới

Hướng dẫn chi tiết để setup và sử dụng tất cả các module mới đã được tích hợp.

## 📦 Bước 1: Cài đặt Dependencies

Các module mới yêu cầu thêm một số packages. Chạy lệnh sau:

```bash
pip install -r requirements.txt
```

Hoặc cài đặt từng package nếu cần:

```bash
# Caching
pip install diskcache>=5.6.0

# Logging & Metrics
pip install structlog>=23.2.0
pip install prometheus-client>=0.19.0
pip install rich>=13.7.0

# Rate Limiting & Resilience
pip install tenacity>=8.2.0
pip install circuitbreaker>=1.4.0

# Configuration
pip install pydantic-settings>=2.1.0
```

## 🔑 Bước 2: Cấu hình .env File

Tạo hoặc cập nhật file `.env` trong thư mục gốc của project:

```env
# ============================================
# API Keys (BẮT BUỘC)
# ============================================
OPENROUTER_API_KEY=sk-or-v1-your-key-here
# Hoặc sử dụng Google Gemini (tùy chọn)
# GOOGLE_API_KEY=your-google-api-key

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL=INFO
# Các mức: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Enable Prometheus metrics server (tùy chọn)
ENABLE_METRICS_SERVER=false
METRICS_PORT=8000
# Nếu bật, metrics sẽ có sẵn tại http://localhost:8000/metrics

# ============================================
# Caching Configuration
# ============================================
CACHE_ENABLED=true
CACHE_TTL=3600
# TTL tính bằng giây (3600 = 1 giờ)
# Cache sẽ giảm API calls đáng kể, tiết kiệm chi phí

CACHE_SIZE_LIMIT=1073741824
# Giới hạn cache size (bytes), mặc định 1GB
# 1073741824 = 1GB

# ============================================
# Rate Limiting Configuration
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_CALLS=60
# Số lượng calls tối đa trong một period
RATE_LIMIT_PERIOD=60
# Period tính bằng giây (60 = 1 phút)

# ============================================
# Retry Configuration
# ============================================
MAX_RETRIES=3
# Số lần retry tối đa khi gặp lỗi

RETRY_INITIAL_WAIT=1.0
# Thời gian chờ ban đầu (giây) trước khi retry

RETRY_MAX_WAIT=60.0
# Thời gian chờ tối đa (giây) giữa các lần retry

RETRY_EXPONENTIAL_BASE=2.0
# Hệ số exponential backoff (2.0 = nhân đôi mỗi lần)

ENABLE_CIRCUIT_BREAKER=true
# Bật circuit breaker để tránh cascade failures

# ============================================
# LLM Configuration
# ============================================
DEFAULT_MODEL=code
# Loại model mặc định: code, general, fast

TEMPERATURE=0.7
# Nhiệt độ cho LLM (0.0 - 1.0)

MAX_TOKENS=2000
# Số tokens tối đa mỗi request

# ============================================
# Workspace Configuration
# ============================================
WORKSPACE_PATH=.
# Đường dẫn workspace (mặc định: thư mục hiện tại)
```

## 🚀 Bước 3: Chạy Hệ Thống

### Cách 1: Chạy CLI (Đơn giản nhất)

```bash
python main.py "analyze codebase"
```

Tất cả các module sẽ tự động được kích hoạt:
- ✅ Caching tự động cache LLM responses
- ✅ Structured logging ghi vào `logs/YYYY-MM-DD.log`
- ✅ Metrics được track (nếu bật metrics server)
- ✅ Rate limiting tự động áp dụng
- ✅ Retry logic tự động xử lý errors

### Cách 2: Kiểm tra Metrics (Nếu đã bật)

Nếu bạn đã set `ENABLE_METRICS_SERVER=true` trong `.env`:

1. Chạy workflow:
```bash
python main.py "analyze codebase"
```

2. Mở browser và truy cập:
```
http://localhost:8000/metrics
```

Bạn sẽ thấy Prometheus metrics như:
```
llm_requests_total{agent="coder",model="gemini-2.5-flash",status="success"} 5.0
llm_request_duration_seconds_bucket{agent="coder",model="gemini-2.5-flash",le="1.0"} 3.0
workflow_duration_seconds_sum{status="success"} 45.2
```

## 📊 Bước 4: Kiểm tra Logs

Logs được lưu tự động trong thư mục `logs/`:

```bash
# Xem log hôm nay
cat logs/$(date +%Y-%m-%d).log

# Hoặc tail để xem real-time
tail -f logs/$(date +%Y-%m-%d).log
```

Logs có format JSON, dễ parse:
```json
{
  "event": "llm_request_started",
  "agent": "coder",
  "model": "gemini-2.5-flash",
  "prompt_length": 1234,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## 💾 Bước 5: Kiểm tra Cache

Cache được lưu tự động trong thư mục `.cache/`:

```bash
# Xem cache directory
ls -lh .cache/

# Xóa cache nếu cần
rm -rf .cache/
```

Cache sẽ tự động:
- Giảm API calls cho prompts tương tự
- Tăng tốc độ response (10-100x cho cached requests)
- Tiết kiệm chi phí API

## ⚙️ Bước 6: Tùy chỉnh Cấu hình

### Tắt Caching (Nếu cần)

Trong `.env`:
```env
CACHE_ENABLED=false
```

Hoặc trong code:
```python
from utils.cache import get_cache
cache = get_cache()
cache.disable()
```

### Thay đổi Log Level

Trong `.env`:
```env
LOG_LEVEL=DEBUG  # Để xem chi tiết hơn
```

### Tắt Rate Limiting

Trong `.env`:
```env
RATE_LIMIT_ENABLED=false
```

## 🔍 Bước 7: Verify Setup

Chạy test script để kiểm tra:

```bash
python test_api.py
```

Nếu mọi thứ OK, bạn sẽ thấy:
- ✅ API connection successful
- ✅ Models fetched successfully
- ✅ Chat completion works

## 📝 Ví dụ Sử Dụng

### Example 1: Chạy với Caching

```bash
# Lần đầu - sẽ gọi API
python main.py "analyze codebase"

# Lần thứ hai với prompt tương tự - sẽ dùng cache (nhanh hơn nhiều)
python main.py "analyze codebase"
```

### Example 2: Xem Metrics

```bash
# Bật metrics server trong .env
ENABLE_METRICS_SERVER=true

# Chạy workflow
python main.py "build a todo app"

# Xem metrics
curl http://localhost:8000/metrics | grep llm_requests_total
```

### Example 3: Debug Mode

```bash
# Set log level = DEBUG trong .env
LOG_LEVEL=DEBUG

# Chạy và xem chi tiết logs
python main.py "fix bugs" | tail -f logs/$(date +%Y-%m-%d).log
```

## 🐛 Troubleshooting

### Lỗi: "diskcache is required for caching"

```bash
pip install diskcache
```

### Lỗi: "structlog could not be resolved"

```bash
pip install structlog prometheus-client
```

### Metrics server không start

- Kiểm tra port 8000 có đang được dùng không
- Thử đổi `METRICS_PORT=8001` trong `.env`

### Cache không hoạt động

- Kiểm tra `CACHE_ENABLED=true` trong `.env`
- Kiểm tra quyền ghi vào thư mục `.cache/`

### Rate limit vẫn bị lỗi

- Tăng `RATE_LIMIT_PERIOD` lên 120 (2 phút)
- Giảm `RATE_LIMIT_MAX_CALLS` xuống 30

## ✅ Checklist Setup

- [ ] Đã cài đặt tất cả dependencies (`pip install -r requirements.txt`)
- [ ] Đã tạo file `.env` với `OPENROUTER_API_KEY`
- [ ] Đã cấu hình các settings cần thiết trong `.env`
- [ ] Đã test chạy `python main.py "test"` thành công
- [ ] Đã kiểm tra logs trong `logs/` directory
- [ ] (Tùy chọn) Đã bật metrics server và kiểm tra tại `http://localhost:8000/metrics`

## 🎯 Quick Start (Minimal)

Nếu bạn chỉ muốn chạy nhanh với cấu hình tối thiểu:

1. **Cài dependencies:**
```bash
pip install -r requirements.txt
```

2. **Tạo `.env` với API key:**
```env
OPENROUTER_API_KEY=sk-or-v1-your-key
```

3. **Chạy:**
```bash
python main.py "analyze codebase"
```

Tất cả các module sẽ tự động hoạt động với default settings!

## 📚 Tài liệu Thêm

- `INTEGRATION_RECOMMENDATIONS.md` - Chi tiết về các module
- `IMPLEMENTATION_SUMMARY.md` - Tóm tắt implementation
- `FIXES_APPLIED.md` - Các fixes đã áp dụng

