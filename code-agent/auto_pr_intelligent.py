"""
Intelligent Auto PR Generator with Advanced Rate Limiting
Demonstrates professional multi-agent workflow with smart API management
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import structlog

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from utils.llm_client import SmartLLMClient, LLMProvider, ContextStrategy
from utils.rate_limiter import Priority
from utils.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("auto_pr")


@dataclass
class FileGenerationTask:
    """Represents a file to be generated"""
    path: str
    description: str
    priority: Priority
    dependencies: List[str] = None  # Files this depends on
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class IntelligentCodeGenerator:
    """
    Intelligent code generator with:
    - Dependency-aware file generation order
    - Context preservation across files
    - Adaptive rate limiting
    - Progress tracking and recovery
    """
    
    def __init__(
        self,
        llm_client: SmartLLMClient,
        output_dir: Path,
        project_name: str = "generated_project"
    ):
        self.llm = llm_client
        self.output_dir = Path(output_dir)
        self.project_name = project_name
        self.generated_files: Dict[str, str] = {}
        self.generation_order: List[FileGenerationTask] = []
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "code_generator_initialized",
            output_dir=str(self.output_dir),
            project_name=project_name
        )
    
    def plan_file_structure(self, requirements: str) -> List[FileGenerationTask]:
        """
        Create intelligent file generation plan based on requirements
        Uses LLM to determine optimal file structure and dependencies
        """
        logger.info("planning_file_structure")
        
        planning_prompt = f"""
Given the following project requirements, create a detailed file structure plan.

Requirements:
{requirements}

Please provide:
1. List of files to create (with paths)
2. Brief description of each file's purpose
3. Priority level (CRITICAL, HIGH, MEDIUM, LOW)
4. Dependencies between files

Format as JSON:
{{
    "files": [
        {{
            "path": "index.html",
            "description": "Main HTML entry point",
            "priority": "CRITICAL",
            "dependencies": []
        }},
        ...
    ]
}}

Rules for prioritization:
- CRITICAL: Essential files without which the app won't run (e.g., main entry points)
- HIGH: Core logic and functionality files
- MEDIUM: Supporting components and utilities
- LOW: Documentation, examples, optional features
"""
        
        # Use HIGH priority for planning as it's crucial
        plan_response = self.llm.generate(
            prompt=planning_prompt,
            system_prompt="You are an expert software architect. Provide detailed, well-structured file plans.",
            priority=Priority.HIGH,
            context="Project structure planning"
        )
        
        # Parse response (simplified - in production, use proper JSON parsing with error handling)
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', plan_response, re.DOTALL)
        if json_match:
            try:
                plan_data = json.loads(json_match.group())
                files = plan_data.get('files', [])
                
                tasks = []
                for file_info in files:
                    priority_str = file_info.get('priority', 'MEDIUM')
                    priority = getattr(Priority, priority_str, Priority.MEDIUM)
                    
                    task = FileGenerationTask(
                        path=file_info['path'],
                        description=file_info['description'],
                        priority=priority,
                        dependencies=file_info.get('dependencies', [])
                    )
                    tasks.append(task)
                
                # Sort by priority (critical first)
                tasks.sort(key=lambda t: t.priority.value)
                
                logger.info(
                    "file_structure_planned",
                    total_files=len(tasks),
                    critical=sum(1 for t in tasks if t.priority == Priority.CRITICAL),
                    high=sum(1 for t in tasks if t.priority == Priority.HIGH)
                )
                
                return tasks
                
            except json.JSONDecodeError as e:
                logger.error("failed_to_parse_plan", error=str(e))
                # Fallback to basic structure
                return self._create_fallback_plan(requirements)
        
        return self._create_fallback_plan(requirements)
    
    def _create_fallback_plan(self, requirements: str) -> List[FileGenerationTask]:
        """Create basic fallback plan if LLM planning fails"""
        logger.warning("using_fallback_plan")
        
        # Basic web app structure
        return [
            FileGenerationTask(
                path="index.html",
                description="Main HTML entry point",
                priority=Priority.CRITICAL
            ),
            FileGenerationTask(
                path="src/css/style.css",
                description="Main stylesheet",
                priority=Priority.HIGH,
                dependencies=["index.html"]
            ),
            FileGenerationTask(
                path="src/js/main.js",
                description="Main JavaScript entry point",
                priority=Priority.CRITICAL,
                dependencies=["index.html"]
            )
        ]
    
    def _build_file_context(
        self,
        task: FileGenerationTask,
        requirements: str
    ) -> str:
        """
        Build intelligent context for file generation
        Includes relevant information from already generated files
        """
        context_parts = [
            f"=== Generating: {task.path} ===",
            f"Purpose: {task.description}",
            f"",
            f"=== Project Requirements ===",
            requirements,
            f""
        ]
        
        # Add context from dependency files
        if task.dependencies:
            context_parts.append("=== Related Files Already Generated ===")
            for dep_path in task.dependencies:
                if dep_path in self.generated_files:
                    content = self.generated_files[dep_path]
                    # Include summary of dependency file (not full content to save tokens)
                    preview = content[:500] + "..." if len(content) > 500 else content
                    context_parts.append(f"\n--- {dep_path} ---")
                    context_parts.append(preview)
            context_parts.append("")
        
        # Add list of other files in project for awareness
        if self.generated_files:
            context_parts.append("=== Other Files in Project ===")
            context_parts.append(", ".join(self.generated_files.keys()))
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def generate_file(
        self,
        task: FileGenerationTask,
        requirements: str
    ) -> str:
        """Generate content for a single file"""
        logger.info(
            "generating_file",
            path=task.path,
            priority=task.priority.name
        )
        
        # Build context
        file_context = self._build_file_context(task, requirements)
        
        # Generate file content
        generation_prompt = f"""
{file_context}

Generate ONLY the complete, production-ready code for {task.path}.
Do not include explanations, markdown formatting, or code fences.
Output should be the raw file content that can be directly saved.

Requirements for this file:
- {task.description}
- Follow best practices and modern standards
- Include helpful comments
- Ensure compatibility with other project files
"""
        
        system_prompt = f"""You are an expert developer generating {task.path}.
Output ONLY the raw code/content, no explanations or markdown.
Code must be complete, functional, and production-ready."""
        
        content = await self.llm.generate_async(
            prompt=generation_prompt,
            system_prompt=system_prompt,
            priority=task.priority,
            context=f"Generating {task.path}",
            use_cache=False  # Don't cache file generation
        )
        
        # Clean up response (remove markdown code fences if present)
        content = content.strip()
        if content.startswith("```"):
            # Remove first line (```language)
            lines = content.split("\n")
            content = "\n".join(lines[1:])
        if content.endswith("```"):
            # Remove last line
            content = "\n".join(content.split("\n")[:-1])
        
        content = content.strip()
        
        # Save file
        file_path = self.output_dir / task.path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        
        # Store in memory for context
        self.generated_files[task.path] = content
        
        logger.info(
            "file_generated",
            path=task.path,
            size=len(content),
            lines=content.count("\n") + 1
        )
        
        return content
    
    async def generate_all_files(
        self,
        requirements: str,
        delay_between_files: float = 5.0
    ):
        """
        Generate all files with intelligent pacing and error recovery
        """
        # Plan structure
        tasks = self.plan_file_structure(requirements)
        self.generation_order = tasks
        
        logger.info(
            "starting_file_generation",
            total_files=len(tasks),
            output_dir=str(self.output_dir)
        )
        
        # Generate files in priority order
        for i, task in enumerate(tasks, 1):
            try:
                logger.info(
                    "file_generation_progress",
                    current=i,
                    total=len(tasks),
                    file=task.path,
                    priority=task.priority.name
                )
                
                await self.generate_file(task, requirements)
                
                # Adaptive delay between files
                if i < len(tasks):
                    # Check rate limiter status
                    status = self.llm.rate_limiter.get_status()
                    
                    # If low on tokens or high failure rate, wait longer
                    if status['tokens_available'] < 3:
                        delay = delay_between_files * 2
                        logger.info("low_tokens_waiting_longer", delay=delay)
                    elif status['metrics']['success_rate'] < 0.7:
                        delay = delay_between_files * 1.5
                        logger.info("low_success_rate_waiting_longer", delay=delay)
                    else:
                        delay = delay_between_files
                    
                    logger.info("waiting_before_next_file", delay=delay)
                    await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(
                    "file_generation_failed",
                    file=task.path,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                # For critical files, retry once
                if task.priority == Priority.CRITICAL:
                    logger.info("retrying_critical_file", file=task.path)
                    await asyncio.sleep(10)
                    try:
                        await self.generate_file(task, requirements)
                    except Exception as retry_error:
                        logger.error(
                            "critical_file_retry_failed",
                            file=task.path,
                            error=str(retry_error)
                        )
                        raise
                else:
                    # For non-critical files, log and continue
                    logger.warning(
                        "skipping_failed_file",
                        file=task.path,
                        priority=task.priority.name
                    )
                    continue
        
        logger.info(
            "file_generation_completed",
            total_generated=len(self.generated_files),
            total_planned=len(tasks)
        )
    
    def generate_summary(self) -> str:
        """Generate project summary"""
        summary_parts = [
            f"# {self.project_name}",
            f"",
            f"## Generated Files ({len(self.generated_files)})",
            f""
        ]
        
        for path in sorted(self.generated_files.keys()):
            content = self.generated_files[path]
            lines = content.count("\n") + 1
            size = len(content)
            summary_parts.append(f"- `{path}` ({lines} lines, {size} bytes)")
        
        summary_parts.extend([
            f"",
            f"## Project Structure",
            f"```",
            self._generate_tree(),
            f"```"
        ])
        
        return "\n".join(summary_parts)
    
    def _generate_tree(self) -> str:
        """Generate ASCII tree of project structure"""
        # Simple tree generation
        paths = sorted(self.generated_files.keys())
        tree_lines = []
        
        for path in paths:
            depth = path.count('/') + path.count('\\')
            indent = "  " * depth
            filename = Path(path).name
            tree_lines.append(f"{indent}├── {filename}")
        
        return "\n".join(tree_lines)


async def main():
    """Main entry point"""
    logger.info("auto_pr_started")
    
    # Check for API key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("missing_api_key")
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your-key-here'")
        return 1
    
    # Initialize smart LLM client
    llm_client = SmartLLMClient(
        provider=LLMProvider.GEMINI,
        api_key=gemini_key,
        model="gemini-2.5-flash",
        max_requests_per_minute=15,  # Adjust based on your quota
        context_strategy=ContextStrategy.HIERARCHICAL,  # Smart context management
        enable_caching=True
    )
    
    # Project requirements
    requirements = """
Create a fully functional chess game that runs in a web browser with the following requirements:

Core Features:
- Complete chess board with proper 8x8 grid layout
- All 32 chess pieces (16 white, 16 black) with accurate starting positions
- Implement all standard chess rules including:
  * Legal move validation for each piece type (pawn, rook, knight, bishop, queen, king)
  * Castling (both kingside and queenside)
  * En passant capture
  * Pawn promotion
  * Check and checkmate detection
  * Stalemate detection

Gameplay:
- Two-player mode (players alternate turns on same device)
- Click to select piece, click destination to move
- Highlight legal moves when a piece is selected
- Display current turn (White/Black)
- Show game status (check, checkmate, stalemate)
- Move history log
- Reset/New game button

Design:
- Clean, modern interface
- Clear visual distinction between white and black pieces
- Alternating light and dark squares
- Responsive design that works on different screen sizes
- Smooth animations for piece movements

Technical:
- Use HTML, CSS, and JavaScript
- No external dependencies required
- All game logic implemented in code
- Include comments explaining key functions
- Single-page application
"""
    
    # Initialize code generator
    generator = IntelligentCodeGenerator(
        llm_client=llm_client,
        output_dir=Path("./generated_chess_game"),
        project_name="Chess Game"
    )
    
    try:
        # Generate all files
        print("🚀 Starting intelligent code generation...")
        print(f"📁 Output directory: {generator.output_dir}")
        print("⚡ Using adaptive rate limiting with smart context management")
        print()
        
        await generator.generate_all_files(
            requirements=requirements,
            delay_between_files=5.0  # Base delay, will be adjusted adaptively
        )
        
        # Generate and save summary
        summary = generator.generate_summary()
        summary_path = generator.output_dir / "PROJECT_SUMMARY.md"
        summary_path.write_text(summary, encoding='utf-8')
        
        print()
        print("✅ Code generation completed successfully!")
        print(f"📊 Generated {len(generator.generated_files)} files")
        print(f"📄 Project summary: {summary_path}")
        print()
        
        # Print rate limiter statistics
        status = llm_client.get_status()
        print("📈 API Statistics:")
        print(f"  Total requests: {status['rate_limiter']['metrics']['total_requests']}")
        print(f"  Success rate: {status['rate_limiter']['metrics']['success_rate']:.1%}")
        print(f"  Avg response time: {status['rate_limiter']['metrics']['average_response_time']:.2f}s")
        print(f"  Rate limited: {status['rate_limiter']['metrics']['rate_limited_requests']} times")
        print()
        
        logger.info(
            "auto_pr_completed",
            files_generated=len(generator.generated_files),
            output_dir=str(generator.output_dir)
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        logger.warning("interrupted_by_user")
        return 130
        
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        logger.error(
            "auto_pr_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run async main
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
