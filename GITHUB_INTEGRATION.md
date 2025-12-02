# GitHub Integration Guide

## Current Behavior

The PR Generator agent produces **text only**: a commit message and pull-request description. It does not create commits or PRs on GitHub automatically unless you run the automation script described below.

## Manual Flow

1. Run the workflow:
   ```bash
   python main.py "analyze codebase, find bugs, refactor, write tests, generate PR"
   ```
2. Copy the commit message and PR description from the output.
3. Create the PR manually either through the GitHub UI or GitHub CLI:

### Using GitHub CLI

```bash
git add .
git commit -m "commit message from Code Agent"
git push origin your-branch
gh pr create --title "PR Title" --body "PR description from Code Agent"
```

## Automating PR Creation

### Option 1: GitHub CLI (`gh`)

1. Install the CLI (https://cli.github.com/).
2. Authenticate with `gh auth login`.
3. Script the workflow:

```python
import subprocess

def create_github_pr(commit_msg: str, pr_desc: str, title: str = "Auto-generated PR"):
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push"], check=True)
    subprocess.run(
        ["gh", "pr", "create", "--title", title, "--body", pr_desc],
        check=True,
    )
```

### Option 2: GitHub REST API

1. Create a personal access token with `repo` scope (https://github.com/settings/tokens).
2. Store credentials in `.env`:
   ```
   GITHUB_TOKEN=ghp_your_token
   GITHUB_REPO=username/repo-name
   ```
3. Call the API:

```python
import os
import requests

def create_pr_via_api(title: str, body: str, head: str, base: str = "main"):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")

    response = requests.post(
        f"https://api.github.com/repos/{repo}/pulls",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        json={
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["html_url"]
```

## Recommended Workflow

- **Basic:** Code Agent -> copy commit/pr text -> create PR manually.
- **Advanced:** Code Agent -> invoke script (CLI/API) -> commit, push, and create PR automatically.

## Fully Automated Flow (REST API)

A helper script `auto_pr.py` wires the entire process:

1. Ensure `.env` contains:
   ```
   OPENROUTER_API_KEY=sk-or...
   GITHUB_TOKEN=ghp_...
   GITHUB_REPO=your-username/your-repo
   WORKSPACE_PATH=/absolute/path/to/your/local/repo
   ```
2. Make changes inside your local repo (for example `/mnt/d/20242/Code_agent/Grad_card`).
3. Run:
   ```bash
   python auto_pr.py \
     --repo-path /mnt/d/20242/Code_agent/Grad_card \
     --head-branch code-agent/auto-grad-card \
     --base-branch main \
     --task "analyze codebase, fix bugs, refactor, write tests, and generate PR"
   ```
4. The script will:
   - Reload Code Agent with `WORKSPACE_PATH` pointing to the repo.
   - Run the workflow to obtain commit/PR text.
   - Create/switch to the head branch, stage all changes, and commit using the generated message.
   - Push the branch to origin.
   - Call the GitHub REST API (via `github_rest.py`) to open a PR automatically.

Flags:
- `--dry-run` skips git/PR operations but prints the commit/PR text.
- `--skip-agent` uses existing changes without re-running Code Agent.
- `--output-json <file>` saves the entire workflow state for auditing.

## Enhancing `pr_generator.py`

To make PR creation automatic:
1. Inject GitHub credentials via `.env`.
2. Extend `PRGeneratorAgent` to call the CLI/API helpers.
3. Add configuration flags for dry runs vs. live pushes.

## Usage Examples

```python
from workflow import CodeAgentWorkflow

workflow = CodeAgentWorkflow(api_key=OPENROUTER_API_KEY)
result = workflow.run("generate PR for bug fixes")

commit_msg = result["results"]["pr_generator"]["result"]["commit_message"]
pr_desc = result["results"]["pr_generator"]["result"]["pr_description"]

print("Commit message:", commit_msg)
print("PR description:", pr_desc)
```

```python
# Full automation with GitHub CLI
import subprocess
from workflow import CodeAgentWorkflow

workflow = CodeAgentWorkflow(api_key=OPENROUTER_API_KEY)
result = workflow.run("generate PR for bug fixes")
commit_msg = result["results"]["pr_generator"]["result"]["commit_message"]
pr_desc = result["results"]["pr_generator"]["result"]["pr_description"]

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", commit_msg])
subprocess.run(["git", "push"])
subprocess.run(["gh", "pr", "create", "--body", pr_desc])
```

## Security Notes

- Never commit tokens or secrets. Store them in `.env` (already gitignored).
- Grant the smallest possible scope to access tokens.
- Consider enabling `dry-run` or confirmation prompts before pushing.

## References

- GitHub CLI: https://cli.github.com/
- GitHub REST API: https://docs.github.com/en/rest
- GitPython: https://gitpython.readthedocs.io/

