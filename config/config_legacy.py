"""Legacy configuration for backward compatibility"""
import os
from pathlib import Path
from dotenv import load_dotenv
from config.settings import get_settings

load_dotenv()

# Get settings instance
settings = get_settings()

# Export old-style config variables for backward compatibility
OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_BASE_URL = settings.openrouter_base_url
GOOGLE_API_KEY = settings.google_api_key
WORKSPACE_PATH = settings.workspace_path
LOGS_DIR = settings.logs_dir

# Model presets
FREE_MODELS = settings.free_models
GOOGLE_MODELS = settings.google_models

# Agent roles (keep as is for now)
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

