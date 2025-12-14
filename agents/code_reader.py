"""
Improved Code Reader Agent (Fixed):
- Phân tích codebase
- Xuất đúng key `codebase_info`
- Tương thích với BugFixerAgent & CodeReaderNode
"""

import os
import ast
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from config import WORKSPACE_PATH


class CodeReaderAgent(BaseAgent):

    def __init__(self, client=None):
        super().__init__("code_reader", client)
        self.workspace_path = WORKSPACE_PATH

    # -----------------------------------------------------
    # BASIC FILE OPS
    # -----------------------------------------------------
    def read_file(self, file_path: str) -> str:
        full_path = os.path.join(self.workspace_path, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"

    def list_files(self, directory=".", extensions=None) -> List[str]:
        if extensions is None:
            extensions = [".py"]

        files = []
        full_path = os.path.join(self.workspace_path, directory)

        for root, dirs, filenames in os.walk(full_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    rel = os.path.relpath(os.path.join(root, filename), self.workspace_path)
                    files.append(rel)
        return files

    # -----------------------------------------------------
    # AST PARSER
    # -----------------------------------------------------
    def parse_python_file(self, file_path: str, content: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(content)
        except Exception:
            return {"error": "unable to parse AST"}

        functions, classes, imports = [], [], []

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "args": [arg.arg for arg in node.args.args]
                })

            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "lineno": node.lineno
                })

            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])

            if isinstance(node, ast.ImportFrom):
                imports.append(node.module)

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports
        }

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------
    def summarize_file(self, file_path: str, content: str, ast_info: Dict[str, Any]):
        return "\n".join([
            f"File: {file_path}",
            f"Classes: {[c['name'] for c in ast_info.get('classes', [])]}",
            f"Functions: {[f['name'] for f in ast_info.get('functions', [])]}",
        ])

    # -----------------------------------------------------
    # MAIN CODE ANALYSIS
    # -----------------------------------------------------
    def analyze_codebase(self, batch_size: int = 5) -> Dict[str, Any]:
        """
        Phân tích codebase theo từng batch file nhỏ (tránh quá tải memory/LLM), trả về tổng hợp từng nhóm file.
        """
        files = self.list_files()
        context_map = {}
        n_files = len(files)
        i = 0
        errors = []
        while i < n_files:
            batch = files[i:i+batch_size]
            for file_path in batch:
                try:
                    content = self.read_file(file_path)
                    ast_info = self.parse_python_file(file_path, content)
                    context_map[file_path] = {
                        "content": content,
                        "summary": self.summarize_file(file_path, content, ast_info),
                        "ast_info": ast_info,
                    }
                except Exception as e:
                    errors.append({"file": file_path, "error": str(e)})
            i += batch_size
        return {
            "total_files": len(files),
            "files": files,
            "context_map": context_map,
            "errors": errors
        }

    # -----------------------------------------------------
    # EXECUTE (Fixed)
    # -----------------------------------------------------
    def execute(self, task: str, context: Dict[str, Any] = None, batch_size: int = 5) -> Dict[str, Any]:
        """
        Phân tích codebase chia nhỏ từng batch file; tổng hợp trả về, trả về rõ ràng trường hợp file lỗi.
        """
        analysis = self.analyze_codebase(batch_size)
        return {
            "agent": "code_reader",
            "task": task,
            "status": "completed" if not analysis.get("errors") else "partial",
            "codebase_info": analysis["context_map"],
            "file_list": analysis["files"],
            "total_files": analysis["total_files"],
            "errors": analysis["errors"]
        }
