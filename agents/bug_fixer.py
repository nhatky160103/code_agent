"""Bug Fixer Agent — fixed version (compatible with your CodeReaderAgent)"""

import json
import os
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from config import WORKSPACE_PATH


class BugFixerAgent(BaseAgent):

    def __init__(self, client=None):
        super().__init__("bug_fixer", client)
        self.workspace_path = WORKSPACE_PATH

    # ============================================================
    # Safe JSON extractor
    # ============================================================
    def _safe_json(self, raw: str, file_path: str = "") -> dict:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError(
                f"[BugFixer] JSON not detected for {file_path}\nRAW:\n{raw}"
            )
        try:
            return json.loads(raw[start:end + 1])
        except Exception as e:
            raise RuntimeError(
                f"[BugFixer] Error parsing JSON for {file_path}: {e}\nRAW:\n{raw}"
            )

    # ============================================================
    # Build usable context info for each file
    # (compatible with your CodeReaderAgent)
    # ============================================================
    def _build_context_for_file(self, file_path: str, codebase_map: dict) -> str:
        meta = codebase_map.get(file_path, {})
        ast_info = meta.get("ast_info", {})

        imports = ast_info.get("imports", [])
        functions = ast_info.get("functions", [])
        classes = ast_info.get("classes", [])

        return f"""
File: {file_path}
Imports: {imports}
Functions: {functions}
Classes: {classes}
"""

    # ============================================================
    # Find bugs
    # ============================================================
    def find_bugs(self, code: str, file_path: str, context_info: str):
        prompt = f"""
You are a senior software engineer.

Analyze the code below and detect bugs.
Use the context to understand dependencies.

Context:
{context_info}

<CODE>
{code}
</CODE>

Return ONLY valid JSON:
{{
  "file": "{file_path}",
  "issues": [
    {{
      "line": number,
      "type": "syntax | logic | runtime | security | performance",
      "description": "short description"
    }}
  ]
}}
"""

        raw = self._call_llm(prompt)
        return self._safe_json(raw, file_path)

    # ============================================================
    # Fix bugs
    # ============================================================
    def fix_bug(self, code: str, issues: List[Dict[str, Any]], file_path: str, context_info: str):
        prompt = f"""
You are a senior software engineer.

Fix the issues listed below.  
Rewrite the entire corrected file.

Context:
{context_info}

Issues:
{issues}

Original code:
<CODE>
{code}
</CODE>

Return ONLY this JSON structure:
{{
  "file": "{file_path}",
  "fixed_code": "<entire corrected file>",
  "explanation": "brief explanation of changes"
}}
"""

        raw = self._call_llm(prompt)
        return self._safe_json(raw, file_path)

    # ============================================================
    # Save file
    # ============================================================
    def _save_fixed_code(self, file_path: str, fixed_code: str) -> bool:
        try:
            full_path = os.path.join(self.workspace_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            print(f"[BugFixer] ✓ Saved fixed file: {file_path}")
            return True
        except Exception as e:
            print(f"[BugFixer] ✗ Error saving {file_path}: {e}")
            return False

    # ============================================================
    # Main execute
    # ============================================================
    def execute(self, task: str, context: Dict[str, Any] = None, batch_size: int = 1) -> Dict[str, Any]:
        """
        Main execute chia nhỏ: mỗi lần fix từng file một (batch_size có thể mở rộng trong tương lai), retry tối đa 3 lần mỗi file nếu lỗi.
        """
        if context is None:
            context = {}

        codebase_map = context.get("codebase_map", {})
        file_path = context.get("file_path", "")

        def fix_single_file(fp, meta):
            code = meta.get("content", "")
            context_info = self._build_context_for_file(fp, codebase_map)
            retries = 0
            last_err = None
            # Từng bước retry mạnh mẽ
            while retries < 3:
                try:
                    bug_info = self.find_bugs(code, fp, context_info)
                    issues = bug_info.get("issues", [])
                    if issues:
                        fix_result = self.fix_bug(code, issues, fp, context_info)
                        fixed_code = fix_result.get("fixed_code", "")
                        if fixed_code and self._save_fixed_code(fp, fixed_code):
                            return {
                                "file": fp,
                                "fixed": True,
                                "issues": issues,
                                "explanation": fix_result.get("explanation", ""),
                            }
                        else:
                            last_err = "Failed to save or fix code"
                    else:
                        return {"file": fp, "fixed": False, "issues": [], "explanation": "No issues found."}
                except Exception as e:
                    last_err = str(e)
                retries += 1
                print(f"[BugFixer] Retry {retries} for {fp} failed: {last_err}")
            return {"file": fp, "fixed": False, "error": last_err}

        if not file_path:
            print("[BugFixer] Full project scan (per file, retry/fallback)...")

            all_results = []
            for fp, meta in codebase_map.items():
                if not fp.endswith((".py", ".js", ".ts")):
                    continue
                result = fix_single_file(fp, meta)
                all_results.append(result)

            return {
                "agent": "bug_fixer",
                "task": task,
                "results": all_results,
                "status": "completed" if any(r.get("fixed") for r in all_results) else "failed"
            }

        # Fix single file
        if file_path not in codebase_map:
            raise RuntimeError(f"[BugFixer] File not found in codebase_map: {file_path}")
        meta = codebase_map[file_path]
        result = fix_single_file(file_path, meta)
        return {
            "agent": "bug_fixer",
            "task": task,
            "result": result,
            "status": "completed" if result.get("fixed") else "failed"
        }
