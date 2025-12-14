"""Main entry point for Code Agent CLI"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from workflow import CodeAgentWorkflow
from config.config_legacy import OPENROUTER_API_KEY
from utils.logging import setup_logging, get_logger
from config.settings import get_settings


def print_results(results: dict):
    """Pretty print results"""
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    for agent_name, result in results.items():
        if isinstance(result, dict):
            print(f"\n[{agent_name.upper()}]")
            print("-" * 80)
            
            if "status" in result:
                print(f"Status: {result['status']}")
            
            if "analysis" in result:
                print(f"\nAnalysis:\n{result['analysis']}")
            
            if "summary" in result:
                print(f"\nSummary:\n{result['summary']}")
            
            if "fixed_code" in result:
                print(f"\nFixed Code:\n{result['fixed_code']}")
            
            if "refactored_code" in result:
                print(f"\nRefactored Code:\n{result['refactored_code']}")
            
            if "test_code" in result:
                print(f"\nTest Code:\n{result['test_code']}")
            
            if "test_results" in result:
                test_results = result["test_results"]
                print(f"\nTest Results:")
                print(f"  Success: {test_results.get('success', False)}")
                if test_results.get("stdout"):
                    print(f"  Output:\n{test_results['stdout']}")
            
            if "commit_message" in result.get("result", {}):
                print(f"\nCommit Message:\n{result['result']['commit_message']}")
            
            if "pr_description" in result.get("result", {}):
                print(f"\nPR Description:\n{result['result']['pr_description']}")
            
            if "structure_suggestions" in result:
                print(f"\nStructure Suggestions:\n{result['structure_suggestions']}")
            
            if "best_practices" in result:
                print(f"\nBest Practices:\n{result['best_practices']}")
    
    print("\n" + "="*80)


def setup_logging() -> Path:
    """Configure structured logging"""
    settings = get_settings()
    logger = setup_logging(
        log_level=settings.log_level,
        log_file=Path(settings.log_file) if settings.log_file else None,
        enable_metrics_server=settings.enable_metrics_server,
        metrics_port=settings.metrics_port
    )
    log_path = settings.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    return log_path


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Code Agent - Multi-agent AI system for code tasks"
    )
    
    parser.add_argument(
        "task",
        type=str,
        help="Task to perform (e.g., 'analyze codebase', 'fix bugs', 'refactor code')"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=OPENROUTER_API_KEY,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
        
    parser.add_argument(
        "--file",
        type=str,
        help="Specific file to work on"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results (JSON format)"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        help="Additional context as JSON string"
    )
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Error: OpenRouter API key is required!")
        print("Set OPENROUTER_API_KEY environment variable or use --api-key flag")
        return
    
    # Initialize logging + workflow
    log_file = setup_logging()
    logger = get_logger("code_agent.main")
    logger.info(
        "cli_started",
        task=args.task,
        file=args.file,
        output=args.output
    )
    workflow = CodeAgentWorkflow(api_key=args.api_key)
    
    # Prepare context
    context = {}
    if args.file:
        context["file_path"] = args.file
    
    if args.context:
        try:
            context.update(json.loads(args.context))
        except json.JSONDecodeError:
            print("Warning: invalid JSON context, ignoring it.")
    
    # Run workflow
    try:
        final_state = workflow.run(args.task, context)
        
        # Print results
        print_results(final_state.get("results", {}))
        logger.info(
            "workflow_completed",
            completed_agents=final_state.get("completed_agents", []),
            log_file=str(log_file)
        )
        
        # Save to file if requested
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(final_state, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {args.output}")
    
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
        logger.warning("workflow_interrupted", reason="user_interrupt")
    except Exception as e:
        print(f"\nError: {str(e)}")
        logger.error(
            "workflow_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

