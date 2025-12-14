# Hướng Dẫn Sử Dụng Google API Key (Gemini)

## ✅ Hệ thống đã hỗ trợ Google Gemini API

Bạn có thể sử dụng Google API key thay vì OpenRouter API key.

## 🔑 Cách 1: Chỉ dùng Google API Key

### Bước 1: Lấy Google API Key

1. Truy cập: https://ai.google.dev/
2. Đăng nhập với Google account
3. Tạo API key mới
4. Copy API key

### Bước 2: Cấu hình trong `.env`

```env
# Chỉ cần Google API Key
GOOGLE_API_KEY=your-api-key

# Không cần OpenRouter API Key nếu chỉ dùng Google
# OPENROUTER_API_KEY=your-api-key
```

### Bước 3: Chạy

```bash
python main.py "analyze codebase"
```

Hệ thống sẽ tự động:
- ✅ Phát hiện `GOOGLE_API_KEY` có giá trị
- ✅ Sử dụng Google Gemini client
- ✅ In ra: `[LLM] Using Google Gemini backend`

## 🔄 Cách 2: Dùng cả hai (Fallback)

Nếu bạn có cả 2 keys, hệ thống sẽ ưu tiên Google, fallback về OpenRouter nếu Google lỗi:

```env
# Google API Key (ưu tiên)
GOOGLE_API_KEY=AIzaSyDThWpTjv9HtaBWMQlYv-8rhBXISTmZVRo

# OpenRouter API Key (fallback)
OPENROUTER_API_KEY=sk-or-v1-your-key
```

## 📊 Models được sử dụng

Khi dùng Google API Key, hệ thống sẽ dùng các models sau (cấu hình trong `config.py`):

```python
GOOGLE_MODELS = {
    "general": "gemini-2.5-flash",
    "code": "gemini-2.5-flash",
    "fast": "gemini-2.5-flash",
}
```

Bạn có thể thay đổi trong `.env` hoặc file `config/settings.py`.

## ⚙️ Rate Limiting

Google Gemini free tier có giới hạn:
- **5 requests per minute** (RPM)
- Hệ thống đã tự động throttle xuống **4 RPM** để tránh lỗi

Nếu vẫn gặp lỗi 429 (rate limit):
- Hệ thống sẽ tự động retry với backoff
- Hoặc fallback về OpenRouter nếu có

## 🔍 Kiểm tra đang dùng Google hay OpenRouter

Khi chạy, bạn sẽ thấy log:

```
[LLM] Using Google Gemini backend
```

Hoặc:

```
[LLM] Using OpenRouter backend
```

## 🐛 Troubleshooting

### Lỗi: "GOOGLE_API_KEY is not set"

**Giải pháp**: Thêm vào `.env`:
```env
GOOGLE_API_KEY=your-key-here
```

### Lỗi: "429 Quota exceeded"

**Nguyên nhân**: Vượt quá rate limit (5 RPM free tier)

**Giải pháp**:
1. Đợi 1 phút rồi chạy lại
2. Hoặc upgrade Google API plan
3. Hoặc dùng OpenRouter API key thay thế

### Lỗi: "ModuleNotFoundError: No module named 'google.generativeai'"

**Giải pháp**: Cài đặt package:
```bash
pip install google-generativeai
```

Hoặc:
```bash
pip install -r requirements.txt
```

## 📝 Ví dụ cấu hình đầy đủ

File `.env`:

```env
# Google API Key (ưu tiên)
GOOGLE_API_KEY=AIzaSyDThWpTjv9HtaBWMQlYv-8rhBXISTmZVRo

# OpenRouter API Key (fallback - tùy chọn)
OPENROUTER_API_KEY=sk-or-v1-your-key

# Logging
LOG_LEVEL=INFO

# Caching (giảm API calls)
CACHE_ENABLED=true
CACHE_TTL=3600

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_CALLS=4
RATE_LIMIT_PERIOD=60
```

## ✅ Checklist

- [ ] Đã lấy Google API key từ https://ai.google.dev/
- [ ] Đã thêm `GOOGLE_API_KEY` vào file `.env`
- [ ] Đã cài `google-generativeai` package
- [ ] Đã test chạy và thấy log `[LLM] Using Google Gemini backend`

## 🎯 Quick Start

1. **Lấy API key**: https://ai.google.dev/

2. **Thêm vào `.env`**:
```env
GOOGLE_API_KEY=your-key-here
```

3. **Chạy**:
```bash
python main.py "test"
```

Xong! Hệ thống sẽ tự động dùng Google Gemini.

