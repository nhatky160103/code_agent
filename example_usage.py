"""Example usage of Code Agent system"""
from workflow import CodeAgentWorkflow
from config import OPENROUTER_API_KEY


def example_analyze_codebase():
    """Example: Analyze codebase"""
    print("=" * 80)
    print("Example 1: Analyze Codebase")
    print("=" * 80)
    
    workflow = CodeAgentWorkflow(api_key=OPENROUTER_API_KEY)
    result = workflow.run("analyze the codebase structure and technologies used")
    
    if "code_reader" in result["results"]:
        print("\nAnalysis completed successfully!")
        print(result["results"]["code_reader"]["analysis"])


def example_fix_bugs():
    """Example: Find and fix bugs"""
    print("\n" + "=" * 80)
    print("Example 2: Find and Fix Bugs")
    print("=" * 80)
    
    workflow = CodeAgentWorkflow(api_key=OPENROUTER_API_KEY)
    result = workflow.run("find and fix all bugs in the codebase")
    
    if "bug_fixer" in result["results"]:
        print("\nBug fixing completed successfully!")
        bug_result = result["results"]["bug_fixer"]
        if "summary" in bug_result:
            print(bug_result["summary"])


def example_refactor():
    """Example: Refactor code"""
    print("\n" + "=" * 80)
    print("Example 3: Refactor Code")
    print("=" * 80)
    
    workflow = CodeAgentWorkflow(api_key=OPENROUTER_API_KEY)
    result = workflow.run("refactor code to improve readability and maintainability")
    
    if "refactorer" in result["results"]:
        print("\nRefactoring completed successfully!")
        refactor_result = result["results"]["refactorer"]
        if "result" in refactor_result:
            print(refactor_result["result"])


def example_full_workflow():
    """Example: Full workflow"""
    print("\n" + "=" * 80)
    print("Example 4: Full Workflow")
    print("=" * 80)
    
    workflow = CodeAgentWorkflow(api_key=OPENROUTER_API_KEY)
    result = workflow.run(
        "analyze codebase, find bugs, refactor code, write tests, and suggest improvements"
    )
    
    print("\nFull workflow completed!")
    print(f"\nCompleted agents: {result.get('completed_agents', [])}")
    
    # Print summary of each agent's work
    for agent_name, agent_result in result["results"].items():
        if agent_result.get("status") == "completed":
            print(f"\n[{agent_name}]: completed")
            
            # Print PR Generator results
            if agent_name == "pr_generator" and "result" in agent_result:
                pr_result = agent_result["result"]
                if "commit_message" in pr_result:
                    print("\n" + "=" * 80)
                    print("COMMIT MESSAGE")
                    print("=" * 80)
                    print(pr_result["commit_message"])
                
                if "pr_description" in pr_result:
                    print("\n" + "=" * 80)
                    print("PULL REQUEST DESCRIPTION")
                    print("=" * 80)
                    print(pr_result["pr_description"])
            
            # Print other agent results if available
            try:
                if agent_name == "code_reader" and "analysis" in agent_result:
                    analysis_text = str(agent_result.get('analysis', ''))
                    if analysis_text:
                        print(f"\nAnalysis preview: {analysis_text[:200]}...")
                
                if agent_name == "bug_fixer" and "summary" in agent_result:
                    summary_text = str(agent_result.get('summary', ''))
                    if summary_text:
                        print(f"\nBug summary: {summary_text[:200]}...")
                
                if agent_name == "architect":
                    if "structure_suggestions" in agent_result:
                        suggestions = agent_result.get('structure_suggestions', {})
                        # structure_suggestions is a dict with 'suggestions' key
                        if isinstance(suggestions, dict) and "suggestions" in suggestions:
                            suggestions_text = str(suggestions.get("suggestions", ""))
                        else:
                            suggestions_text = str(suggestions)
                        
                        if suggestions_text and suggestions_text != "{}":
                            print(f"\nStructure suggestions: {suggestions_text[:200]}...")
                    
                    if "best_practices" in agent_result:
                        practices = agent_result.get('best_practices', {})
                        if isinstance(practices, dict) and "best_practices" in practices:
                            practices_text = str(practices.get("best_practices", ""))
                        else:
                            practices_text = str(practices)
                        
                        if practices_text and practices_text != "{}":
                            print(f"\nBest practices: {practices_text[:200]}...")
            except Exception as e:
                # Silently skip if there's an error printing preview
                pass


if __name__ == "__main__":
    # Check API key
    if not OPENROUTER_API_KEY:
        print("Error: please set OPENROUTER_API_KEY in the .env file")
        exit(1)
    
    # Run examples
    try:
        # example_analyze_codebase()
        # Uncomment to run more examples:
        # example_fix_bugs()
        # example_refactor()
        example_full_workflow()
        
        # Debug: Print full results (uncomment to see all details)
        # import json
        # workflow = CodeAgentWorkflow(api_key=OPENROUTER_API_KEY)
        # result = workflow.run("analyze codebase, find bugs, refactor code, write tests, and suggest improvements")
        # print("\n" + "=" * 80)
        # print("DEBUG: Full Results")
        # print("=" * 80)
        # print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

