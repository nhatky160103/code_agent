# Quick Start Guide

## Step 1: Install dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure your API key

1. Create an account at https://openrouter.ai/
2. Generate a free API key
3. Create a `.env` file and add:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key
```

## Step 3: Run a sanity check

```bash
# Verify imports
python test_simple.py

# Run the sample workflow
python example_usage.py
```

## Common CLI tasks

```bash
python main.py "analyze codebase structure"
python main.py "find bugs and fix them"
python main.py "refactor code for better quality"
python main.py "write comprehensive tests"
python main.py "generate pull request"
python main.py "suggest project structure"
```

## Full workflow example

```bash
python main.py "analyze codebase, find bugs, fix them, refactor, write tests, and generate PR"
```

## Notes

- Free OpenRouter models can be slower than paid tiers.
- Ensure your machine has internet access for API calls.
- Use `--output <file>.json` to capture the workflow state as JSON.

