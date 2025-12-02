"""Code Reader Agent - Reads and analyzes codebase"""
import os
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from config import WORKSPACE_PATH


class CodeReaderAgent(BaseAgent):
    """Agent specialized in reading and understanding codebases"""
    
    def __init__(self, client=None):    
        super().__init__("code_reader", client)
        self.workspace_path = WORKSPACE_PATH
    
    def read_file(self, file_path: str) -> str:
        """Read a file from the codebase"""
        full_path = os.path.join(self.workspace_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
    def list_files(self, directory: str = ".", extensions: List[str] = None) -> List[str]:
        """List files in a directory"""
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs"]
        
        files = []
        full_path = os.path.join(self.workspace_path, directory)
        
        try:
            for root, dirs, filenames in os.walk(full_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    if any(filename.endswith(ext) for ext in extensions):
                        rel_path = os.path.relpath(
                            os.path.join(root, filename),
                            self.workspace_path
                        )
                        files.append(rel_path)
        except Exception as e:
            print(f"Error listing files: {e}")
        
        return files
    
    def analyze_codebase(self, max_files: int = 20) -> Dict[str, Any]:
        """Analyze the codebase structure"""
        files = self.list_files()
        file_contents = {}
        
        # Read first N files
        for file_path in files[:max_files]:
            content = self.read_file(file_path)
            file_contents[file_path] = content[:2000]  # Limit content size
        
        return {
            "total_files": len(files),
            "files_analyzed": len(file_contents),
            "file_contents": file_contents,
            "file_list": files
        }
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute code reading task"""
        if context is None:
            context = {}
        
        # Analyze codebase
        analysis = self.analyze_codebase()
        
        # Build prompt for LLM
        files_summary = "\n".join([
            f"- {path}" for path in analysis["file_list"][:10]
        ])
        
        prompt = f"""
Task: {task}

Codebase Summary:
- Total files: {analysis['total_files']}
- Files analyzed: {analysis['files_analyzed']}

Key files:
{files_summary}

Please analyze this codebase and provide:
1. Project structure overview
2. Main technologies used
3. Key components and their relationships
4. Potential issues or improvements
"""
        
        # Get some file contents for context
        sample_content = ""
        for path, content in list(analysis["file_contents"].items())[:3]:
            sample_content += f"\n\n--- {path} ---\n{content[:500]}"
        
        prompt += f"\n\nSample code:\n{sample_content}"
        
        analysis_result = self._call_llm(prompt, context)
        
        return {
            "agent": "code_reader",
            "task": task,
            "analysis": analysis_result,
            "codebase_info": {
                "total_files": analysis["total_files"],
                "files": analysis["file_list"]
            },
            "status": "completed"
        }

