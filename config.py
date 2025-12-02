"""Configuration for Code Agent system"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Free models from OpenRouter
# Note: Model names may need to be updated. Check available models at:
# https://openrouter.ai/models or use get_available_models() method
FREE_MODELS = {
    "code": "google/gemma-3-27b-it:free",  # Good for code tasks
    "general": "openai/gpt-oss-20b:free",  # General purpose (removed :free suffix)
    "fast": "tngtech/deepseek-r1t2-chimera:free",  # Fast responses (removed :free suffix)
    # Alternative free models to try:
    # "code": "google/gemini-flash-1.5-8b:free",
    # "general": "meta-llama/llama-3.2-3b-instruct:free",
    # "fast": "qwen/qwen-2.5-7b-instruct:free",
}

# Workspace configuration
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", ".")

# Agent roles
AGENT_ROLES = {
    "code_reader": (
        "You are an expert at reading and summarizing codebases. "
        "Inspect the repository, capture structure, technologies, and key files."
    ),
    "bug_fixer": (
        "You specialize in bug fixing. Identify defects, explain root causes, "
        "and provide corrected code."
    ),
    "refactorer": (
        "You focus on refactoring. Improve readability and maintainability "
        "without changing behavior."
    ),
    "tester": (
        "You write and optionally run tests. Produce thorough pytest suites "
        "and describe the coverage."
    ),
    "pr_generator": (
        "You prepare pull-request documentation. Summarize changes and draft "
        "commit messages plus PR descriptions."
    ),
    "architect": (
        "You act as a software architect. Suggest project structure improvements "
        "and best practices."
    ),
}

