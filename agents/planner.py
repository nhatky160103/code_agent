"""Requirements Planner Agent - turns user requirements into a plan."""
from typing import Dict, Any

from agents.base_agent import BaseAgent


class RequirementsPlannerAgent(BaseAgent):
    """Agent that reads high-level product requirements and produces a plan."""

    def __init__(self, client=None):
        super().__init__("planner", client)

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Turn a natural-language task + raw requirements file into a plan."""
        if context is None:
            context = {}

        requirements_text = context.get("requirements_text", "").strip()

        prompt = f"""
You are a senior product engineer. The user wants an application defined by:

High-level task:
{task}
    
Detailed requirements file (if provided):
{requirements_text or '[no external requirements file provided]'}

The WORKSPACE_PATH directory contains (or will contain) the target project.

Please produce:
1. A short problem statement.
2. A list of user stories.
3. A feature list for the first version (MVP).
4. A file/module plan (paths and responsibilities) to implement the MVP.
5. A rough testing strategy (what to test and where tests should live).

Return the plan in clear markdown sections.
"""
        analysis = self._call_llm(prompt, context)

        return {
            "agent": "planner",
            "task": task,
            "plan_markdown": analysis,
            "status": "completed",
        }


