"""
Quick Start Script
Chạy script này để setup và test toàn bộ hệ thống
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(step, text):
    print(f"\n[{step}] {text}")

def run_command(cmd, description):
    """Run command and handle errors"""
    print(f"  → {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"  ✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ {description} - FAILED")
        if e.stderr:
            print(f"     Error: {e.stderr[:200]}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ❌ Python 3.8+ required!")
        print(f"     Current version: {version.major}.{version.minor}")
        return False
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_api_key():
    """Check if API key is set"""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("  ⚠️  GEMINI_API_KEY not set")
        print()
        print("  Please set it:")
        print("    Windows: set GEMINI_API_KEY=your-key-here")
        print("    Linux/Mac: export GEMINI_API_KEY=your-key-here")
        print()
        return False
    
    print(f"  ✅ API key found: {key[:10]}...{key[-4:]}")
    return True

def main():
    print_header("🚀 Intelligent Rate Limiter - Quick Start")
    
    print("""
This script will:
  1. Check system requirements
  2. Install dependencies
  3. Run tests
  4. Setup example project
  5. Generate sample code
    """)
    
    # Step 1: Check Python
    print_step("1/6", "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check API key
    print_step("2/6", "Checking API key")
    has_key = check_api_key()
    
    # Step 3: Install dependencies
    print_step("3/6", "Installing dependencies")
    
    # Check if requirements file exists
    req_file = Path("requirements_intelligent.txt")
    if not req_file.exists():
        print("  ⚠️  requirements_intelligent.txt not found")
        print("  📝 Creating basic requirements...")
        req_file.write_text("""google-generativeai>=0.3.0
structlog>=23.1.0
python-dotenv>=1.0.0
""")
    
    if not run_command(
        "pip install -q google-generativeai structlog python-dotenv",
        "Installing packages"
    ):
        print("\n  💡 Try: pip install --user google-generativeai structlog python-dotenv")
        response = input("\n  Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Step 4: Check files exist
    print_step("4/6", "Checking project files")
    
    required_files = [
        "utils/rate_limiter.py",
        "utils/llm_client.py",
        "test_rate_limiter.py",
        "auto_pr_intelligent.py"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            all_exist = False
    
    if not all_exist:
        print("\n  ⚠️  Some files are missing!")
        print("  Make sure you have all the required files.")
        sys.exit(1)
    
    # Step 5: Run tests (if API key available)
    print_step("5/6", "Running tests")
    
    if has_key:
        print("  🧪 Running rate limiter tests...")
        if run_command("python test_rate_limiter.py", "Tests"):
            print("\n  🎉 All tests passed!")
        else:
            print("\n  ⚠️  Some tests failed, but you can still continue")
    else:
        print("  ⏭️  Skipping tests (no API key)")
        print("  💡 Set GEMINI_API_KEY to run tests")
    
    # Step 6: Show next steps
    print_step("6/6", "Setup complete!")
    
    print("""
    
  ✅ Setup successful!
  
  Next steps:
  
  1️⃣  Read the documentation:
      python MIGRATION_GUIDE.py
      # Or open: README_INTELLIGENT_PR.md
  
  2️⃣  Test the rate limiter (if you have API key):
      python test_rate_limiter.py
  
  3️⃣  Generate a project:
      python auto_pr_intelligent.py
  
  4️⃣  Or use the client in your code:
""")
    
    print("""
      from utils.llm_client import SmartLLMClient, LLMProvider
      from utils.rate_limiter import Priority
      
      llm = SmartLLMClient(
          provider=LLMProvider.GEMINI,
          max_requests_per_minute=15
      )
      
      response = llm.generate(
          prompt="Write a hello world function",
          priority=Priority.MEDIUM,
          context="Example generation"
      )
""")
    
    if not has_key:
        print("\n  ⚠️  IMPORTANT: Set your API key first!")
        print("      export GEMINI_API_KEY='your-key-here'")
    
    print("\n" + "="*70)
    print("  🎓 Pro Tips:")
    print("="*70)
    print("""
  - Start with low max_requests_per_minute (10-15)
  - Use Priority.CRITICAL only for essential files
  - Monitor success_rate and adjust parameters
  - Check logs/ folder for detailed information
  - Use HIERARCHICAL context strategy for best results
    """)
    
    print("="*70)
    print("  Happy coding! 🚀")
    print("="*70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Setup interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n  ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
