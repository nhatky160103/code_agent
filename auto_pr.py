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

    load_dotenv()


    def parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Run Code Agent, commit changes, push, and open a PR via REST API",
        )
        parser.add_argument(
            "--task",
            type=str,
            default="analyze codebase, find bugs, fix them, refactor, write tests, and "
            "generate PR",
            help="   passed to Code Agent workflow.",
        )
        parser.add_argument(
            "--repo-path",
            type=str,
            default=os.getenv("WORKSPACE_PATH", "."),
            help="Path to the git repository containing code changes.",
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
        """Fetch, checkout base, and create/update head branch."""
        run_cmd(["git", "fetch", "origin", base_branch], repo_path, check=False)
        run_cmd(["git", "checkout", base_branch], repo_path)
        run_cmd(["git", "pull", "origin", base_branch], repo_path, check=False)
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


    def run_code_agent(task: str, api_key: Optional[str], output_json: Optional[str]) -> Dict:
        """Execute the workflow and return the final state."""
        os.environ["OPENROUTER_API_KEY"] = api_key or os.getenv("OPENROUTER_API_KEY", "")

        importlib.reload(importlib.import_module("config"))
        workflow_module = importlib.reload(importlib.import_module("workflow"))
        CodeAgentWorkflow = workflow_module.CodeAgentWorkflow

        workflow = CodeAgentWorkflow(api_key=os.environ.get("OPENROUTER_API_KEY", ""))
        final_state = workflow.run(task, initial_context={})

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
        repo_path = Path(args.repo_path).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")

        os.environ["WORKSPACE_PATH"] = str(repo_path)

        final_state: Dict = {}
        if not args.skip_agent:
            final_state = run_code_agent(args.task, args.api_key, args.output_json)
            pr_payload = extract_pr_payload(final_state)
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

        push_branch(repo_path, args.head_branch)

        from github_rest import create_pr_via_api

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


