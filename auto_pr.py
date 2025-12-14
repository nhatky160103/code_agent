"""Automate Code Agent workflow, git commit/push, and PR creation."""
from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
from github_rest import create_pr_via_api, create_repo_for_current_user

load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Code Agent, commit changes, push, and open a PR via REST API",
    )
    parser.add_argument(
        "--task",
        type=str,
        help="Optional high-level task description. If omitted, it will be built "
        "from the requirements file.",
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        default=None,
        help=(
            "Path to the git repository containing code changes. "
            "If omitted, WORKSPACE_PATH from the environment/.env will be used."
        ),
    )
    parser.add_argument(
        "--base-branch",
        type=str,
        default="main",
        help="Target branch for the pull request.",
    )
    parser.add_argument(
        "--head-branch",
        type=str,
        default="code-agent/auto-pr",
        help="Branch to push changes to before creating the PR.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("OPENROUTER_API_KEY"),
        help="Override OpenRouter API key (defaults to env).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run Code Agent but skip git/PR operations.",
    )
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="Skip running Code Agent (useful if commit message/PR already known).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Optional path to save the full workflow state as JSON.",
    )
    parser.add_argument(
        "--requirements-file",
        type=str,
        default="user_requirements.txt",
        help="Path to the requirements text file describing the desired app.",
    )
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path, check: bool = True) -> str:
    """Run a subprocess command inside the repo path."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed with code {result.returncode}:\n"
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def ensure_branch(repo_path: Path, base_branch: str, head_branch: str) -> None:
    """Ensure a git repo exists, then fetch base and create/update head branch."""
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        # Initialize a new git repository
        run_cmd(["git", "init"], repo_path)
        # Optionally add origin remote from GITHUB_REPO env
        github_repo = os.getenv("GITHUB_REPO")
        if github_repo:
            remote_url = f"https://github.com/{github_repo}.git"
            run_cmd(["git", "remote", "add", "origin", remote_url], repo_path, check=False)

    # Try to make sure base branch exists locally
    run_cmd(["git", "fetch", "origin", base_branch], repo_path, check=False)
    # Create or switch to base branch
    run_cmd(["git", "checkout", "-B", base_branch], repo_path, check=False)
    # Try to fast-forward from remote if it exists
    run_cmd(["git", "pull", "origin", base_branch], repo_path, check=False)
    # Create/update head branch from base
    run_cmd(["git", "checkout", "-B", head_branch], repo_path)


def stage_and_commit(repo_path: Path, commit_msg: str) -> bool:
    """Stage all changes and create a commit if there are staged diffs."""
    run_cmd(["git", "add", "."], repo_path)
    diff = run_cmd(["git", "status", "--short"], repo_path)
    if not diff:
        print("No changes detected; skipping commit.")
        return False
    run_cmd(["git", "commit", "-m", commit_msg], repo_path)
    return True


def push_branch(repo_path: Path, head_branch: str) -> None:
    run_cmd(["git", "push", "-u", "origin", head_branch], repo_path)


def remote_has_branch(repo_path: Path, branch: str) -> bool:
    """
    Check if a given branch already exists on the remote.
    """
    output = run_cmd(
        ["git", "ls-remote", "--heads", "origin", branch],
        repo_path,
        check=False,
    )
    return bool(output.strip())


def ensure_remote_base_branch(repo_path: Path, base_branch: str, head_branch: str) -> None:
    """
    Ensure the remote has the base branch required for creating a PR.

    On a freshly created repository, only the head branch may exist.
    In that case we create/update the base branch to point at the same
    commit as the head branch and push it, so that the GitHub PR API
    has a valid base to target.
    """
    if base_branch == head_branch:
        return

    if remote_has_branch(repo_path, base_branch):
        return

    # Base branch does not exist remotely; create/update it from head.
    # We assume we are currently on the head_branch after committing.
    run_cmd(["git", "checkout", head_branch], repo_path, check=False)
    run_cmd(["git", "branch", "-f", base_branch], repo_path)
    run_cmd(["git", "push", "-u", "origin", base_branch], repo_path)


def run_code_agent(
    task: str,
    api_key: Optional[str],
    output_json: Optional[str],
    initial_context: Optional[Dict] = None,
) -> Dict:
    """Execute the workflow and return the final state."""
    os.environ["OPENROUTER_API_KEY"] = api_key or os.getenv("OPENROUTER_API_KEY", "")

    importlib.reload(importlib.import_module("config"))
    workflow_module = importlib.reload(importlib.import_module("workflow"))
    CodeAgentWorkflow = workflow_module.CodeAgentWorkflow

    workflow = CodeAgentWorkflow(api_key=os.environ.get("OPENROUTER_API_KEY", ""))
    final_state = workflow.run(task, initial_context=initial_context or {})

    if output_json:
        import json

        with open(output_json, "w", encoding="utf-8") as fh:
            json.dump(final_state, fh, indent=2)
        print(f"Workflow state saved to {output_json}")

    return final_state


def extract_pr_payload(final_state: Dict) -> Dict[str, str]:
    """Pull commit message and PR description from workflow results."""
    pr_agent = final_state.get("results", {}).get("pr_generator", {})
    result = pr_agent.get("result", {})
    commit_msg = result.get("commit_message")
    pr_desc = result.get("pr_description")
    if not commit_msg or not pr_desc:
        raise RuntimeError(
            "PR Generator result missing. Ensure your task includes 'generate PR'."
        )
    return {"commit_message": commit_msg.strip(), "pr_description": pr_desc.strip()}


def main() -> None:
    args = parse_args()
    # Determine target repo path: CLI flag wins; otherwise fall back to WORKSPACE_PATH.
    repo_root = args.repo_path or os.getenv("WORKSPACE_PATH")
    if not repo_root:
        raise FileNotFoundError(
            "No repo path provided. Set WORKSPACE_PATH in your .env "
            "or pass --repo-path explicitly."
        )

    repo_path = Path(repo_root).resolve()
    if not repo_path.exists():
        # Auto-create the workspace directory if it does not exist yet.
        repo_path.mkdir(parents=True, exist_ok=True)

    os.environ["WORKSPACE_PATH"] = str(repo_path)

    # If no GITHUB_REPO is configured, auto-create one on GitHub for the
    # currently authenticated user using the local folder name.
    github_repo = os.getenv("GITHUB_REPO")
    if not github_repo:
        repo_name = repo_path.name
        print(
            f"GITHUB_REPO is not set. Creating a new GitHub repository "
            f"'{repo_name}' for the current user..."
        )
        full_name = create_repo_for_current_user(
            name=repo_name,
            private=True,
            description=f"Auto-created by Code Agent for local workspace {repo_name}",
        )
        os.environ["GITHUB_REPO"] = full_name
        print(f"GitHub repository created: https://github.com/{full_name}")

    # Read user requirements from file. This is intentionally resolved
    # relative to the Code Agent project (the directory of this script),
    # not the target workspace, so you don't need to copy the file into
    # WORKSPACE_PATH.
    script_dir = Path(__file__).resolve().parent
    req_path = Path(args.requirements_file)
    if not req_path.is_absolute():
        requirements_path = script_dir / req_path
    else:
        requirements_path = req_path
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")

    requirements_text = requirements_path.read_text(encoding="utf-8")

    # Build a rich task string if not explicitly provided
    if args.task:
        task = args.task
    else:
        task = (
            "Using the following requirements, design and implement an application, "
            "write tests, run them, fix bugs, refactor, and prepare a pull request:\n\n"
            f"{requirements_text}"
        )

    final_state: Dict = {}
    if not args.skip_agent:
        final_state = run_code_agent(
            task,
            args.api_key,
            args.output_json,
            initial_context={"requirements_text": requirements_text},
        )
        print("[DEBUG] Final workflow state:", final_state)
        print("[DEBUG] final_state['results']:", final_state.get('results'))
        if final_state.get('results'):
            print("[DEBUG] result keys:", final_state['results'].keys())
        try:
            pr_payload = extract_pr_payload(final_state)
        except Exception as e:
            print(f"[ERROR] PR payload extraction failed: {e}")
            print("[ERROR] Missing pr_generator or fields in workflow results!")
            pr_payload = {
                "commit_message": "chore: Code Agent updates",
                "pr_description": "Automated PR (missing pr_generator output)",
            }
            if not final_state:
                print("[FATAL] Workflow did not return any results, exiting...")
                sys.exit(2)
    else:
        pr_payload = {
            "commit_message": "chore: Code Agent updates",
            "pr_description": "Automated pull request generated via auto_pr.py",
        }

    if args.dry_run:
        print("Dry run enabled; skipping git and PR steps.")
        print(f"Commit message:\n{pr_payload['commit_message']}\n")
        print(f"PR description:\n{pr_payload['pr_description']}\n")
        return

    ensure_branch(repo_path, args.base_branch, args.head_branch)
    has_commit = stage_and_commit(repo_path, pr_payload["commit_message"])
    if not has_commit:
        return

    # Make sure the remote has the base branch so that PR creation
    # does not fail with "base invalid" on first run.
    ensure_remote_base_branch(repo_path, args.base_branch, args.head_branch)

    push_branch(repo_path, args.head_branch)
    pr_url = create_pr_via_api(
        title=pr_payload["commit_message"][:70],
        body=pr_payload["pr_description"],
        head=args.head_branch,
        base=args.base_branch,
    )
    print(f"Pull request created: {pr_url}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Auto PR failed: {exc}")
        sys.exit(1)
