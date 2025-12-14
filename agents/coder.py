"""
CoderAgent v4 – Ultra-robust with validation and error recovery
"""
import os
import json
import re
from typing import Dict, Any, List
from pathlib import Path

from agents.base_agent import BaseAgent
from config import WORKSPACE_PATH


class CoderAgent(BaseAgent):
    """
    CoderAgent v4 – Production-ready
    - JSON-safe parsing with validation
    - Code syntax validation before saving
    - Chunk reassembly with error recovery
    - Fallback to stub files if generation fails
    """

    def __init__(self, client=None):
        super().__init__("coder", client)
        self.workspace_path = WORKSPACE_PATH
        self.max_retries = 3

    def _write_file(self, relative_path: str, content: str) -> bool:
        """Write file and validate syntax if applicable"""
        try:
            full_path = os.path.join(self.workspace_path, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # ✅ Validate syntax before writing
            if relative_path.endswith(".js"):
                if not self._is_valid_js(content):
                    print(f"[Coder] ⚠️  JavaScript syntax error in {relative_path}")
                    return False
            elif relative_path.endswith(".py"):
                if not self._is_valid_python(content):
                    print(f"[Coder] ⚠️  Python syntax error in {relative_path}")
                    return False

            with open(full_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            
            print(f"[Coder] ✓ Written: {relative_path} ({len(content)} bytes)")
            return True
        except Exception as e:
            print(f"[Coder] ✗ Error writing {relative_path}: {e}")
            return False

    def _is_valid_js(self, code: str) -> bool:
        """Check if JavaScript code has balanced braces"""
        # Count braces, brackets, parentheses
        braces = code.count("{") - code.count("}")
        brackets = code.count("[") - code.count("]")
        parens = code.count("(") - code.count(")")
        
        if braces != 0 or brackets != 0 or parens != 0:
            print(f"[Coder] Syntax check: braces={braces}, brackets={brackets}, parens={parens}")
            return False
        return True

    def _is_valid_python(self, code: str) -> bool:
        """Check if Python code can be parsed"""
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError as e:
            print(f"[Coder] Python syntax error: {e}")
            return False

    def _get_file_plan(self, task: str, plan_markdown: str) -> List[Dict[str, str]]:
        """Get file plan from planner"""
        prompt = f"""
You are a senior software engineer.  
Return ONLY a valid JSON object listing all files for the project.

Task:
{task}

High-level plan:
{plan_markdown}

JSON format:
{{
  "files": [
    {{"path": "index.html", "description": "Main HTML file"}},
    {{"path": "app.js", "description": "Main JavaScript file"}},
    {{"path": "style.css", "description": "Styling"}}
  ]
}}

IMPORTANT:
- Return ONLY valid JSON
- No markdown, no code blocks
- Each file must have "path" and "description"
- Paths must be relative (no leading /)
"""

        raw = self._call_llm(prompt, {"max_tokens": 2000})

        try:
            # ✅ FIX 1: Extract JSON with balanced braces
            data = json.loads(self._extract_json_safe(raw))
            files = data.get("files", [])
            if not files:
                print("[Coder] Warning: No files in plan, using defaults")
                return self._get_default_file_plan()
            return files
        except Exception as e:
            print(f"[Coder] Error parsing file plan: {e}")
            # Check nếu lỗi là quota hoặc non-JSON error trả về từ LLM, fallback empty
            if "quota" in str(raw).lower() or "error calling" in str(raw).lower():
                print(f"[Coder] LLM returned API error, fallback with default or empty file plan. Raw:", raw[:300])
                return []  # hoặc return self._get_default_file_plan() nếu muốn vẫn sinh files
            print(f"[Coder] Raw response: {raw[:500]}")
            return self._get_default_file_plan()

    def _get_default_file_plan(self) -> List[Dict[str, str]]:
        """Fallback file plan for TODO app"""
        return [
            {"path": "index.html", "description": "Main HTML file with form and list"},
            {"path": "app.js", "description": "TodoApp class and DOM logic"},
            {"path": "style.css", "description": "CSS styling"},
            {"path": "package.json", "description": "npm configuration with jest"},
            {"path": "tests/app.test.js", "description": "Jest unit tests"},
            {"path": "README.md", "description": "Documentation"},
        ]

    def _generate_file_content(self, task: str, plan_markdown: str, file_item: Dict[str, str]) -> str:
        """Generate complete file content (not chunked anymore)"""
        path = file_item["path"]
        description = file_item.get("description", "")

        # ✅ FIX 2: Direct generation instead of chunks
        prompt = f"""
You are a senior software engineer. Generate COMPLETE, production-ready code.

Task:
{task}

High-level plan:
{plan_markdown}

File to generate:
- Path: {path}
- Description: {description}

Requirements:
1. Generate COMPLETE, working code (not stubs or pseudocode)
2. No placeholder comments like "TODO:", "...", "your code here"
3. Code must be VALID and EXECUTABLE
4. If JavaScript: balanced braces, proper syntax
5. If Python: valid Python 3 syntax
6. If JSON: valid JSON format
7. Do NOT wrap in markdown code blocks

Return ONLY the file content, nothing else.
"""

        # Try up to 3 times if syntax is invalid
        for attempt in range(self.max_retries):
            raw = self._call_llm(prompt, {"max_tokens": 4000})
            content = self._clean_content(raw)

            if not content:
                print(f"[Coder] Attempt {attempt+1}: Empty content for {path}")
                continue

            # ✅ Validate before returning
            if path.endswith(".js"):
                if self._is_valid_js(content):
                    return content
            elif path.endswith(".py"):
                if self._is_valid_python(content):
                    return content
            elif path.endswith((".json", ".html", ".css", ".md")):
                # Basic validation for other formats
                if len(content) > 50:  # Reasonable minimum
                    return content

            print(f"[Coder] ⚠️  Syntax invalid on attempt {attempt+1}, retrying...")

        # ✅ Last resort: return content as-is (let error handling deal with it)
        print(f"[Coder] ⚠️  Could not generate valid {path}, using partial content")
        return content if content else ""

    def _clean_content(self, raw: str) -> str:
        """Remove markdown code blocks and extra formatting"""
        # Remove markdown code block markers
        content = re.sub(r'^```\w*\n', '', raw)  # Remove opening ```
        content = re.sub(r'\n```$', '', content)  # Remove closing ```
        
        # Remove common prefixes
        content = re.sub(r'^(Here|Below|Here is|Here\'s).*?:\n', '', content, flags=re.IGNORECASE)
        
        return content.strip()

    def _extract_json_safe(self, raw: str) -> str:
        """
        ✅ FIX 3: Safe JSON extraction with bracket matching
        """
        # Try to find JSON object with proper bracket matching
        json_match = re.search(r'\{', raw)
        if not json_match:
            raise ValueError("No JSON object found")

        start = json_match.start()
        brace_count = 0
        end = -1

        for i in range(start, len(raw)):
            if raw[i] == '{':
                brace_count += 1
            elif raw[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break

        if end == -1:
            raise ValueError("Unmatched braces in JSON")

        return raw[start:end]

    def execute(self, task: str, context: Dict[str, Any] = None, batch_size: int = 1) -> Dict[str, Any]:
        """
        Main execution, chia nhỏ LLM call từng file hoặc nhóm file (batch_size, mặc định 1 file/lần call).
        Kết quả chi tiết, retry từng file tối đa 3 lần.
        """
        if context is None:
            context = {}

        plan_markdown = context.get("plan_markdown", "")

        print("[Coder] Getting file plan...")
        file_plan = self._get_file_plan(task, plan_markdown)
        files_written = []
        files_failed = []
        fail_detail = []
        n_files = len(file_plan)
        i = 0

        while i < n_files:
            # Lấy từng batch nhóm file
            batch = file_plan[i:i+batch_size]
            for file_item in batch:
                path = file_item["path"]
                desc = file_item.get("description", "")
                print(f"[Coder] Generating {path}...")
                retries = 0
                success = False
                last_err = None
                while retries < self.max_retries:
                    try:
                        content = self._generate_file_content(task, plan_markdown, file_item)
                        if not content or len(content.strip()) < 5:
                            raise RuntimeError("Empty code generated.")
                        if self._write_file(path, content):
                            files_written.append(path)
                            success = True
                            break
                        else:
                            last_err = "Failed to write file (validation/syntax?)"
                    except Exception as e:
                        last_err = str(e)
                    retries += 1
                    print(f"[Coder] Retry {retries} for {path} failed: {last_err}")
                if not success:
                    files_failed.append(path)
                    fail_detail.append({"file": path, "error": last_err})
            i += batch_size

        if files_failed:
            print(f"[Coder] ⚠️  {len(files_failed)} files failed: {files_failed}")

        return {
            "agent": "coder",
            "task": task,
            "files_written": files_written,
            "files_failed": files_failed,
            "fail_detail": fail_detail,
            "status": "completed" if files_written else "failed",
        }
