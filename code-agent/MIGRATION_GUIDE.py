"""
Migration Guide: Từ Code Cũ sang Intelligent Rate Limiter

Script này giúp migrate code cũ sang hệ thống mới
"""

print("""
╔════════════════════════════════════════════════════════════════════════╗
║                    🚀 MIGRATION GUIDE                                  ║
║          Từ code cũ sang Intelligent Rate Limiter System              ║
╚════════════════════════════════════════════════════════════════════════╝

📋 BƯỚC 1: Backup code hiện tại
─────────────────────────────────────────────────────────────────────────

Nếu bạn có code cũ (auto_pr.py hoặc tương tự), hãy backup:

    cp auto_pr.py auto_pr.py.backup
    cp -r agents/ agents.backup/

─────────────────────────────────────────────────────────────────────────
📦 BƯỚC 2: Cài đặt dependencies
─────────────────────────────────────────────────────────────────────────

    pip install -r requirements_intelligent.txt

Hoặc:

    pip install google-generativeai structlog python-dotenv

─────────────────────────────────────────────────────────────────────────
🔑 BƯỚC 3: Setup API Key
─────────────────────────────────────────────────────────────────────────

Windows:
    set GEMINI_API_KEY=your-api-key-here

Linux/Mac:
    export GEMINI_API_KEY=your-api-key-here

Hoặc tạo file .env:
    echo "GEMINI_API_KEY=your-key-here" > .env

─────────────────────────────────────────────────────────────────────────
🧪 BƯỚC 4: Test hệ thống mới
─────────────────────────────────────────────────────────────────────────

Chạy test script trước:

    python test_rate_limiter.py

Kết quả mong đợi:
    ✅ Test 1: Basic Rate Limiting - PASS
    ✅ Test 2: Priority Queue - PASS
    ✅ Test 3: Circuit Breaker - PASS
    ✅ Test 4: LLM Client Integration - PASS

─────────────────────────────────────────────────────────────────────────
🎯 BƯỚC 5: Chạy code generation mới
─────────────────────────────────────────────────────────────────────────

    python auto_pr_intelligent.py

Hệ thống sẽ:
    1. 📋 Plan file structure thông minh
    2. 🎯 Sắp xếp theo priority
    3. ⚡ Generate với rate limiting adaptive
    4. 🔄 Tự động retry khi rate limit
    5. 📊 Track metrics real-time
    6. ✅ Generate summary report

─────────────────────────────────────────────────────────────────────────
💡 SO SÁNH: Code Cũ vs Code Mới
─────────────────────────────────────────────────────────────────────────

❌ CODE CŨ (Có vấn đề):
────────────────────────────
    # Không có rate limiting thông minh
    for file in files:
        response = llm.generate(prompt)  # ❌ Rate limit!
        time.sleep(3)  # ❌ Fixed delay
    
    # Vấn đề:
    - Bị rate limit liên tục
    - Circuit breaker không hiệu quả
    - Không có priority
    - Không quản lý context
    - Không có retry thông minh

✅ CODE MỚI (Đã fix):
────────────────────────────
    from utils.llm_client import SmartLLMClient
    from utils.rate_limiter import Priority
    
    llm = SmartLLMClient(
        max_requests_per_minute=15,
        context_strategy=ContextStrategy.HIERARCHICAL
    )
    
    for task in tasks:
        response = await llm.generate_async(
            prompt=task.prompt,
            priority=task.priority,  # ✅ Smart priority
            context=task.description
        )
    
    # Ưu điểm:
    ✅ Token bucket rate limiting
    ✅ Exponential backoff với jitter
    ✅ Priority queue
    ✅ Circuit breaker thông minh
    ✅ Context management strategies
    ✅ Automatic retry
    ✅ Metrics tracking
    ✅ Adaptive delays

─────────────────────────────────────────────────────────────────────────
🔧 BƯỚC 6: Migrate code cũ của bạn (nếu có)
─────────────────────────────────────────────────────────────────────────

Nếu bạn có LLM wrapper cũ, thay thế như sau:

BEFORE (Old code):
─────────────────
    import google.generativeai as genai
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    for i in range(10):
        response = model.generate_content(prompt)
        time.sleep(3)  # Fixed delay

AFTER (New code):
────────────────
    from utils.llm_client import SmartLLMClient, LLMProvider
    from utils.rate_limiter import Priority
    
    llm = SmartLLMClient(
        provider=LLMProvider.GEMINI,
        max_requests_per_minute=15
    )
    
    prompts = [
        {'prompt': p, 'priority': Priority.MEDIUM}
        for p in prompt_list
    ]
    
    responses = llm.batch_generate(prompts)

─────────────────────────────────────────────────────────────────────────
📊 BƯỚC 7: Monitor & Optimize
─────────────────────────────────────────────────────────────────────────

Kiểm tra metrics sau khi chạy:

    status = llm.get_status()
    print(f"Success rate: {status['rate_limiter']['metrics']['success_rate']}")

Nếu success rate < 80%:
    - Giảm max_requests_per_minute
    - Tăng base_delay_seconds
    - Review priorities

Nếu quá chậm:
    - Tăng max_requests_per_minute (nếu quota cho phép)
    - Sử dụng ContextStrategy.SLIDING_WINDOW
    - Enable caching

─────────────────────────────────────────────────────────────────────────
⚙️ BƯỚC 8: Fine-tuning Parameters
─────────────────────────────────────────────────────────────────────────

Tùy chỉnh cho use case của bạn:

# Cho API có quota thấp (free tier):
SmartLLMClient(
    max_requests_per_minute=10,  # Conservative
    base_delay_seconds=8.0,      # Longer delays
    context_strategy=ContextStrategy.SLIDING_WINDOW
)

# Cho API có quota cao (paid tier):
SmartLLMClient(
    max_requests_per_minute=30,  # Aggressive
    base_delay_seconds=3.0,      # Shorter delays
    context_strategy=ContextStrategy.HIERARCHICAL
)

# Cho production environment:
SmartLLMClient(
    max_requests_per_minute=20,  # Balanced
    base_delay_seconds=5.0,
    context_strategy=ContextStrategy.HIERARCHICAL,
    enable_caching=True  # Cache responses
)

─────────────────────────────────────────────────────────────────────────
🐛 TROUBLESHOOTING
─────────────────────────────────────────────────────────────────────────

Lỗi: "GEMINI_API_KEY not set"
→ Giải pháp: export GEMINI_API_KEY='your-key'

Lỗi: "Rate limit exceeded"
→ Giải pháp: 
  1. Đợi 2-3 phút
  2. Giảm max_requests_per_minute
  3. Tăng base_delay_seconds

Lỗi: "Circuit breaker OPEN"
→ Giải pháp:
  1. Hệ thống tự recovery sau 3 phút
  2. Hoặc restart script
  3. Check API quota status

Lỗi: "Import error"
→ Giải pháp:
  pip install -r requirements_intelligent.txt

─────────────────────────────────────────────────────────────────────────
✅ CHECKLIST HOÀN THÀNH
─────────────────────────────────────────────────────────────────────────

[ ] Backup code cũ
[ ] Cài đặt dependencies
[ ] Setup API key
[ ] Test rate limiter (python test_rate_limiter.py)
[ ] Chạy auto_pr_intelligent.py thành công
[ ] Review metrics và optimize parameters
[ ] Đọc README_INTELLIGENT_PR.md
[ ] Understand các strategies (Priority, Context, etc.)

─────────────────────────────────────────────────────────────────────────
📚 TÀI LIỆU THAM KHẢO
─────────────────────────────────────────────────────────────────────────

1. README_INTELLIGENT_PR.md - Hướng dẫn chi tiết
2. test_rate_limiter.py - Examples và tests
3. auto_pr_intelligent.py - Production code
4. utils/rate_limiter.py - Core rate limiting logic
5. utils/llm_client.py - LLM client wrapper

─────────────────────────────────────────────────────────────────────────
🎓 BEST PRACTICES
─────────────────────────────────────────────────────────────────────────

1. ✅ Luôn set PRIORITY phù hợp:
   - CRITICAL: index.html, main entry points
   - HIGH: core logic files
   - MEDIUM: supporting files (default)
   - LOW: documentation, optional

2. ✅ Chọn CONTEXT STRATEGY hợp lý:
   - HIERARCHICAL: recommended cho most cases
   - SLIDING_WINDOW: cho very long tasks
   - FULL_CONTEXT: cho simple tasks

3. ✅ Monitor metrics:
   - Check success_rate thường xuyên
   - Adjust parameters dựa trên metrics
   - Log errors để debug

4. ✅ Handle errors gracefully:
   - Sử dụng try-catch
   - Log chi tiết
   - Có recovery strategy

─────────────────────────────────────────────────────────────────────────
🎉 HOÀN THÀNH!
─────────────────────────────────────────────────────────────────────────

Bạn đã sẵn sàng sử dụng hệ thống Intelligent Rate Limiter!

Chạy ngay:
    python auto_pr_intelligent.py

Hoặc test trước:
    python test_rate_limiter.py

Need help? Check:
    - README_INTELLIGENT_PR.md
    - Logs trong logs/ folder
    - Status metrics với llm.get_status()

Happy coding! 🚀

╔════════════════════════════════════════════════════════════════════════╗
║  "Rate limits are just challenges waiting to be intelligently solved"  ║
╚════════════════════════════════════════════════════════════════════════╝
""")
