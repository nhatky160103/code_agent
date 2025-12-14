"""Configuration for Code Agent system"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Google AI Studio / Gemini configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Model presets for different backends.
# FREE_MODELS are kept for OpenRouter compatibility; GOOGLE_MODELS for direct Gemini use.
FREE_MODELS = {
    "code": "tngtech/deepseek-r1t2-chimera:free",
    "general": "openai/gpt-oss-20b:free",
    "fast": "google/gemma-3-27b-it:free",
}

GOOGLE_MODELS = {
    # A powerful model with advanced reasoning, visual understanding, and coding.
    "general": "gemini-2.5-flash    ",
    # Strong for code + reasoning.
    "code": "gemini-2.5-flash",
    # Fast / high-volume tasks.
    "fast": "gemini-2.5-flash",
}

# Workspace configuration
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", ".")
LOGS_DIR = (Path(WORKSPACE_PATH).expanduser().resolve() / "logs")

# Agent roles
AGENT_ROLES = {
    "planner": (
        "You are a senior product engineer and technical planner. Turn natural "
        "language product requirements into user stories, features, and a file-level "
        "implementation plan."
    ),
    "coder": (
        "You are a senior software engineer. Given a task and a high-level plan, "
        "produce concrete source files that implement the requested behavior."
    ),
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

