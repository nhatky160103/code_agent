"""Refactorer Agent - improves code readability and maintainability"""

import json
import os
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from config import WORKSPACE_PATH


class RefactorerAgent(BaseAgent):

    def __init__(self, client=None):
        super().__init__("refactorer", client)
        self.workspace_path = WORKSPACE_PATH

    def _safe_json(self, raw: str, file_path: str = "") -> dict:
        """Extract JSON from LLM response"""
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return {"result": raw, "status": "completed"}
        try:
            return json.loads(raw[start:end + 1])
        except Exception as e:
            return {"result": raw, "status": "completed", "error": str(e)}

    def read_file(self, file_path: str) -> str:
        """Read a file from workspace"""
        full_path = os.path.join(self.workspace_path, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Refactor code to improve readability and maintainability"""
        context = context or {}
        
        # Get files to refactor
        files = context.get("files", [])
        if not files:
            # Try to get from codebase_info
            codebase_info = context.get("codebase_info", {})
            files = codebase_info.get("files", [])
        
        # If specific file provided, focus on that
        target_file = context.get("file_path")
        if target_file and target_file not in files:
            files = [target_file]
        
        if not files:
            return {
                "agent": "refactorer",
                "status": "skipped",
                "note": "No files found to refactor"
            }

        # Read file contents
        file_contents = {}
        for file_path in files[:5]:  # Limit to 5 files
            content = self.read_file(file_path)
            if not content.startswith("Error"):
                file_contents[file_path] = content

        if not file_contents:
            return {
                "agent": "refactorer",
                "status": "error",
                "error": "Could not read any files"
            }

        # Build prompt
        files_text = "\n\n".join([
            f"File: {path}\n```\n{content}\n```"
            for path, content in file_contents.items()
        ])

        prompt = f"""Refactor the following code to improve readability and maintainability without changing behavior.

Task: {task}

Files to refactor:
{files_text}

Please provide:
1. Refactored code for each file
2. Explanation of improvements made
3. Any patterns or best practices applied

Return your response as JSON with this structure:
{{
    "refactored_code": {{
        "file_path": "refactored code here"
    }},
    "improvements": "explanation of improvements",
    "patterns_applied": ["pattern1", "pattern2"]
}}"""

        try:
            raw_response = self._call_llm(prompt, context)
            result = self._safe_json(raw_response, list(file_contents.keys())[0])
            
            return {
                "agent": "refactorer",
                "status": "completed",
                "files_refactored": list(file_contents.keys()),
                **result
            }
        except Exception as e:
            return {
                "agent": "refactorer",
                "status": "error",
                "error": str(e),
                "raw_response": raw_response if 'raw_response' in locals() else None
            }

