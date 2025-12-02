"""Main entry point for Code Agent CLI"""
import argparse
import json
from workflow import CodeAgentWorkflow
from config import OPENROUTER_API_KEY


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
    
    # Initialize workflow
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
        
        # Save to file if requested
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(final_state, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {args.output}")
    
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

