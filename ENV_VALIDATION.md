# Environment Variables Validation Guide

## ✅ Format .env File Đúng

File `.env` sử dụng format chuẩn với các quy tắc sau:

### 1. Case Sensitivity
- **Pydantic-settings** được cấu hình với `case_sensitive=False`
- Bạn có thể dùng **UPPER_CASE** hoặc **lowercase** đều được
- Ví dụ: `OPENROUTER_API_KEY` hoặc `openrouter_api_key` đều OK

### 2. Format Chuẩn
```env
# Comment với dấu #
VARIABLE_NAME=value
VARIABLE_NAME="value with spaces"
VARIABLE_NAME='value with spaces'
```

### 3. Boolean Values
```env
# Các giá trị boolean có thể dùng:
ENABLE_METRICS_SERVER=true
ENABLE_METRICS_SERVER=false
ENABLE_METRICS_SERVER=1
ENABLE_METRICS_SERVER=0
ENABLE_METRICS_SERVER=yes
ENABLE_METRICS_SERVER=no
```

### 4. Số và Float
```env
# Số nguyên
MAX_RETRIES=3
METRICS_PORT=8000

# Số thực
TEMPERATURE=0.7
RETRY_INITIAL_WAIT=1.0
```

## 📋 Danh Sách Tất Cả Biến Môi Trường

### API Keys (Bắt buộc ít nhất 1)
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `OPENROUTER_API_KEY` | string | `""` | OpenRouter API key |
| `GOOGLE_API_KEY` | string | `None` | Google Gemini API key |

### Logging
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `LOG_LEVEL` | string | `"INFO"` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FILE` | string | `None` | Custom log file path |
| `ENABLE_METRICS_SERVER` | bool | `false` | Enable Prometheus metrics server |
| `METRICS_PORT` | int | `8000` | Metrics server port |

### Caching
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `CACHE_ENABLED` | bool | `true` | Enable response caching |
| `CACHE_TTL` | int | `3600` | Cache TTL in seconds |
| `CACHE_DIR` | string | `None` | Custom cache directory |
| `CACHE_SIZE_LIMIT` | int | `1073741824` | Cache size limit (1GB) |

### Rate Limiting
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `RATE_LIMIT_ENABLED` | bool | `true` | Enable rate limiting |
| `RATE_LIMIT_MAX_CALLS` | int | `60` | Max calls per period |
| `RATE_LIMIT_PERIOD` | int | `60` | Period in seconds |

### Retry Configuration
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `MAX_RETRIES` | int | `3` | Maximum retry attempts |
| `RETRY_INITIAL_WAIT` | float | `1.0` | Initial wait time (seconds) |
| `RETRY_MAX_WAIT` | float | `60.0` | Maximum wait time (seconds) |
| `RETRY_EXPONENTIAL_BASE` | float | `2.0` | Exponential backoff base |
| `ENABLE_CIRCUIT_BREAKER` | bool | `true` | Enable circuit breaker |

### LLM Configuration
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `DEFAULT_MODEL` | string | `"code"` | Default model type |
| `TEMPERATURE` | float | `0.7` | LLM temperature |
| `MAX_TOKENS` | int | `2000` | Maximum tokens per request |

### Workspace
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `WORKSPACE_PATH` | string | `"."` | Workspace directory path |

### GitHub (Optional)
| Biến | Type | Default | Mô tả |
|------|------|---------|-------|
| `GITHUB_TOKEN` | string | `None` | GitHub personal access token |
| `GITHUB_REPO` | string | `None` | GitHub repository (username/repo) |

## ✅ Ví Dụ .env File Đúng

### Minimal (Tối thiểu)
```env
OPENROUTER_API_KEY=sk-or-v1-your-key
```

### Recommended (Khuyến nghị)
```env
# API Keys
OPENROUTER_API_KEY=sk-or-v1-your-key
GOOGLE_API_KEY=AIzaSyDThWpTjv9HtaBWMQlYv-8rhBXISTmZVRo

# Logging
LOG_LEVEL=INFO
ENABLE_METRICS_SERVER=false

# Caching
CACHE_ENABLED=true
CACHE_TTL=3600

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_CALLS=60
RATE_LIMIT_PERIOD=60

# Workspace
WORKSPACE_PATH=.
```

### Full Configuration (Đầy đủ)
```env
# API Keys
OPENROUTER_API_KEY=sk-or-v1-your-key
GOOGLE_API_KEY=AIzaSyDThWpTjv9HtaBWMQlYv-8rhBXISTmZVRo

# Logging
LOG_LEVEL=INFO
LOG_FILE=
ENABLE_METRICS_SERVER=false
METRICS_PORT=8000

# Caching
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_DIR=
CACHE_SIZE_LIMIT=1073741824

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_CALLS=60
RATE_LIMIT_PERIOD=60

# Retry
MAX_RETRIES=3
RETRY_INITIAL_WAIT=1.0
RETRY_MAX_WAIT=60.0
RETRY_EXPONENTIAL_BASE=2.0
ENABLE_CIRCUIT_BREAKER=true

# LLM
DEFAULT_MODEL=code
TEMPERATURE=0.7
MAX_TOKENS=2000

# Workspace
WORKSPACE_PATH=.

# GitHub (Optional)
GITHUB_TOKEN=ghp_your_token
GITHUB_REPO=username/repo
```

## ⚠️ Lưu Ý Quan Trọng

### 1. Không có khoảng trắng quanh dấu `=`
```env
# ❌ SAI
OPENROUTER_API_KEY = sk-or-v1-key

# ✅ ĐÚNG
OPENROUTER_API_KEY=sk-or-v1-key
```

### 2. Không cần quotes cho giá trị đơn giản
```env
# ✅ ĐÚNG (cả 2 cách)
LOG_LEVEL=INFO
LOG_LEVEL="INFO"
```

### 3. Quotes cho giá trị có khoảng trắng
```env
# ✅ ĐÚNG
WORKSPACE_PATH="/path/to/my workspace"
```

### 4. Boolean values
```env
# ✅ Tất cả đều đúng
CACHE_ENABLED=true
CACHE_ENABLED=false
CACHE_ENABLED=1
CACHE_ENABLED=0
```

## 🔍 Kiểm Tra .env File

### Cách 1: Test trong Python
```python
from config.settings import get_settings

settings = get_settings()
print(f"OpenRouter Key: {settings.openrouter_api_key[:10]}...")
print(f"Cache Enabled: {settings.cache_enabled}")
print(f"Log Level: {settings.log_level}")
```

### Cách 2: Chạy test script
```bash
python -c "from config.settings import get_settings; s = get_settings(); print('✅ Config loaded:', s.cache_enabled, s.log_level)"
```

### Cách 3: Xem logs khi chạy
```bash
python main.py "test" 2>&1 | grep -i "config\|error"
```

## 🐛 Troubleshooting

### Lỗi: "openrouter_api_key is required"
**Nguyên nhân**: Không có API key trong .env
**Giải pháp**: Thêm `OPENROUTER_API_KEY=your-key` vào .env

### Lỗi: "log_level must be one of..."
**Nguyên nhân**: Giá trị LOG_LEVEL không hợp lệ
**Giải pháp**: Dùng một trong: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Config không load
**Nguyên nhân**: File .env không đúng format hoặc không ở thư mục gốc
**Giải pháp**: 
1. Kiểm tra file .env ở thư mục gốc của project
2. Kiểm tra format (không có khoảng trắng quanh `=`)
3. Kiểm tra encoding (UTF-8)

## ✅ Checklist

- [ ] File `.env` nằm ở thư mục gốc của project
- [ ] Có ít nhất 1 API key (OPENROUTER_API_KEY hoặc GOOGLE_API_KEY)
- [ ] Không có khoảng trắng quanh dấu `=`
- [ ] Boolean values dùng `true`/`false` hoặc `1`/`0`
- [ ] Số và float không có quotes
- [ ] Đã test load config thành công

