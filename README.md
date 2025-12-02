# Code Agent - Multi-Agent AI System

Code Agent uses LangGraph to orchestrate a team of specialized AI agents that can analyze, modify, test, and document a codebase on your behalf.

## Features

- **Code Reader** - scans the repository, summarizes technologies, and captures structural context
- **Bug Fixer** - identifies defects and proposes patched code
- **Refactorer** - improves readability and structure without changing behavior
- **Tester** - writes and optionally runs pytest suites
- **PR Generator** - drafts commit messages and pull-request descriptions
- **Architect** - suggests high-level structure and best practices

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd code-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your OpenRouter key:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key
```
You can request a free key at https://openrouter.ai/.

## Usage

### CLI

```bash
# Analyze the repository
python main.py "analyze codebase"

# Find and fix bugs
python main.py "find and fix bugs"

# Refactor code
python main.py "refactor code to improve quality"

# Write tests (prints test code by default)
python main.py "write tests for the codebase"

# Generate a pull-request summary
python main.py "generate pull request"

# Provide additional context
python main.py "fix bugs in utils.py" --file utils.py
python main.py "write tests" --context '{"action": "run"}'

# Save JSON output
python main.py "analyze codebase" --output results.json
```

### Python API

```python
from workflow import CodeAgentWorkflow

workflow = CodeAgentWorkflow(api_key="your_api_key")
result = workflow.run("analyze codebase and fix bugs")
print(result["results"])
```

## Project Structure

```
code-agent/
|-- agents/                 # Agent implementations
|-- auto_pr.py              # End-to-end automation (git + PR)
|-- config.py               # Environment and role configuration
|-- github_rest.py          # REST helper for GitHub PRs
|-- workflow.py             # LangGraph workflow
|-- main.py                 # CLI entry point
|-- openrouter_client.py    # Client wrapper for OpenRouter
|-- requirements.txt
`-- docs (*.md)
```

## How It Works

1. **Router driven workflow** - LangGraph routes the request to the right agent(s).
2. **Shared state** - each agent updates a shared context dictionary with results.
3. **OpenRouter models** - calls go through OpenRouter so you can swap LLMs easily.
4. **Composable tasks** - combine actions (analyze -> fix -> refactor -> test -> PR) in a single prompt.

### Workflow Overview

```
Task Input -> Router -> Code Reader -> Bug Fixer -> Refactorer -> Tester
                                                   |
                                                   v
                                             PR Generator
                                                   |
                                                   v
                                              Architect
                                                   |
                                                   v
                                             Results Output
```

## Default Models

You can override models in `config.py`. By default the agent uses OpenRouter free tiers such as:
- `google/gemma-3-27b-it:free` for code-related tasks
- `openai/gpt-oss-20b:free` for general reasoning
- `tngtech/deepseek-r1t2-chimera:free` for faster responses

## Examples

```bash
# Analyze, fix, refactor, test, and draft a PR
python main.py "analyze codebase, find bugs, fix them, refactor, write tests, and generate PR"

# Run tests that were previously generated
python main.py "write tests for the codebase" --context '{"action":"run"}'

# Automate git push + PR creation (requires GITHUB_TOKEN/GITHUB_REPO)
python auto_pr.py --repo-path /path/to/repo --head-branch code-agent/changes
```

## Notes

- Ensure the `OPENROUTER_API_KEY` environment variable is set.
- Free models can be rate-limited; upgrade the key for production workloads.
- The tester agent only runs pytest when `context.action` is set to `"run"`.

## Extending The System

1. Add a new agent under `agents/` inheriting from `BaseAgent`.
2. Implement `execute`.
3. Register the agent inside `CodeAgentWorkflow` and update the router logic.

## License

MIT

