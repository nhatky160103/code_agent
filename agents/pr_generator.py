"""PR Generator Agent - Generates pull requests and commit messages"""
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
import os


class PRGeneratorAgent(BaseAgent):
    """Agent specialized in generating PR descriptions and commit messages"""
    
    def __init__(self, client=None):
        super().__init__("pr_generator", client)
    
    def generate_commit_message(self, changes: Dict[str, Any]) -> str:
        """Generate commit message from changes"""
        prompt = f"""
Generate a clear and descriptive commit message for the following changes:

Changes:
{self._format_changes(changes)}

Follow conventional commit format:
- type(scope): subject
- body (optional)
- footer (optional)

Types: feat, fix, refactor, test, docs, style, chore
"""
        
        commit_msg = self._call_llm(prompt)
        return commit_msg
    
    def generate_pr_description(self, changes: Dict[str, Any], commits: List[str] = None) -> str:
        """Generate PR description"""
        prompt = f"""
Generate a comprehensive pull request description for the following changes:

Changes Summary:
{self._format_changes(changes)}

Commits:
{chr(10).join(commits) if commits else 'N/A'}

Please include:
1. Summary of changes
2. What was changed and why
3. Testing done
4. Screenshots/demos if applicable
5. Checklist
"""
        
        pr_description = self._call_llm(prompt)
        return pr_description
    
    def _format_changes(self, changes: Dict[str, Any]) -> str:
        """Format changes for display"""
        formatted = []
        for key, value in changes.items():
            if isinstance(value, dict):
                formatted.append(f"{key}:")
                for k, v in value.items():
                    formatted.append(f"  - {k}: {v}")
            else:
                formatted.append(f"{key}: {value}")
        return "\n".join(formatted)
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute PR generation task"""
        if context is None:
            context = {}
        
        changes = context.get("changes", {})
        commits = context.get("commits", [])
        action = context.get("action", "both")  # "commit", "pr", or "both"
        
        result = {}
        
        if action in ["commit", "both"]:
            commit_msg = self.generate_commit_message(changes)
            result["commit_message"] = commit_msg
        
        if action in ["pr", "both"]:
            pr_desc = self.generate_pr_description(changes, commits)
            result["pr_description"] = pr_desc
        
        return {
            "agent": "pr_generator",
            "task": task,
            "result": result,
            "status": "completed",
            "note": "Commit and PR text created. To open an actual GitHub PR:\n"
                    "1. Commit your code with the generated message.\n"
                    "2. Push your branch to GitHub.\n"
                    "3. Create a PR with the generated description, or call the "
                    "GitHub CLI/API to automate these steps."
        }

