import subprocess
import json
import os
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpencodeEvaluator:
    def __init__(self, test_repo_path: str):
        self.test_repo_path = Path(test_repo_path)
        self.results = []
        
    def run_opencode_query(
        self,
        model: str,
        prompt: str,
        timeout: int = 120
    ) -> Dict:
        """
        Run opencode with a specific model and prompt.
        Returns the session data and execution metrics.
        """
        logger.info(f"Running opencode with model: {model}")
        logger.info(f"Prompt: {prompt[:100]}...")

        start_time = time.time()

        try:
            # Construct command: opencode run [message] -m model
            # The command runs in the project directory (cwd)
            cmd = [
                "opencode", "run",
                prompt,  # The prompt/message
                "-m", model  # The model to use
            ]

            logger.info(f"Executing command: {' '.join(cmd)}")
            logger.info(f"Working directory: {self.test_repo_path}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.test_repo_path)  # Run in the project directory
            )

            execution_time = time.time() - start_time

            logger.info(f"Command completed in {execution_time:.2f}s")
            logger.info(f"Return code: {result.returncode}")

            return {
                "model": model,
                "prompt": prompt,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "execution_time": execution_time,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s")
            return {
                "model": model,
                "prompt": prompt,
                "stdout": "",
                "stderr": f"Timeout after {timeout}s",
                "returncode": -1,
                "execution_time": timeout,
                "success": False,
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"Error running opencode: {str(e)}")
            return {
                "model": model,
                "prompt": prompt,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "execution_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    def extract_session_id(self, output: str) -> Optional[str]:
        """Extract session ID from opencode output."""
        for line in output.split('\n'):
            if 'session' in line.lower() or 'id' in line.lower():
                parts = line.split()
                for part in parts:
                    if len(part) > 10 and '-' in part:
                        return part
        return None
    
    def export_session(self, session_id: str) -> Optional[Dict]:
        """Export session data from opencode."""
        try:
            logger.info(f"Exporting session: {session_id}")
            result = subprocess.run(
                ["opencode", "export", session_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
            else:
                logger.warning(f"Failed to export session: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting session: {str(e)}")
            return None
    
    def analyze_agent_response(self, result: Dict) -> Dict:
        """
        Analyze the agent's response for quality metrics.
        """
        analysis = {
            "model": result["model"],
            "prompt": result["prompt"],
            "execution_time": result["execution_time"],
            "success": result["success"],
            "metrics": {}
        }
        
        output = result.get("stdout", "")
        stderr = result.get("stderr", "")
        
        # Check if tools were used
        analysis["metrics"]["tools_used"] = self._detect_tools_used(output)
        analysis["metrics"]["tool_count"] = len(analysis["metrics"]["tools_used"])
        
        # Check for errors - only count actual failures
        # Don't count stderr alone as many tools output warnings/info to stderr
        # Don't count the word "error" as it could be in code, docs, or normal output
        analysis["metrics"]["has_errors"] = not result["success"]
        
        # Check response completeness
        analysis["metrics"]["response_length"] = len(output)
        analysis["metrics"]["has_code"] = "```" in output or "def " in output or "class " in output
        
        # Check for file operations
        analysis["metrics"]["file_operations"] = self._detect_file_operations(output)
        
        # Check for search operations
        analysis["metrics"]["search_operations"] = self._detect_search_operations(output)
        
        return analysis
    
    def _detect_tools_used(self, output: str) -> List[str]:
        """Detect which tools were mentioned/used in the output."""
        tools = []
        tool_keywords = [
            "read_file", "edit", "grep_search", "file_search",
            "run_in_terminal", "list_dir", "semantic_search",
            "fetch_url", "web_search", "mkdir", "delete_file"
        ]
        
        for tool in tool_keywords:
            if tool in output.lower():
                tools.append(tool)
        
        return tools
    
    def _detect_file_operations(self, output: str) -> List[str]:
        """Detect file operations in the output."""
        operations = []
        if "read" in output.lower() or "reading" in output.lower():
            operations.append("read")
        if "edit" in output.lower() or "editing" in output.lower() or "modif" in output.lower():
            operations.append("edit")
        if "creat" in output.lower():
            operations.append("create")
        if "delet" in output.lower():
            operations.append("delete")
        return operations
    
    def _detect_search_operations(self, output: str) -> List[str]:
        """Detect search operations in the output."""
        operations = []
        if "grep" in output.lower() or "search" in output.lower():
            operations.append("search")
        if "find" in output.lower():
            operations.append("find")
        return operations
    
    def compare_models(
        self,
        models: List[str],
        prompts: List[str]
    ) -> List[Dict]:
        """
        Compare multiple models across multiple prompts.
        """
        results = []
        
        for prompt in prompts:
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing prompt: {prompt[:100]}...")
            logger.info(f"{'='*80}\n")
            
            prompt_results = {
                "prompt": prompt,
                "model_results": []
            }
            
            for model in models:
                logger.info(f"\nTesting model: {model}")
                
                # Run the query
                result = self.run_opencode_query(model, prompt)
                
                # Analyze the response
                analysis = self.analyze_agent_response(result)
                
                prompt_results["model_results"].append({
                    "model": model,
                    "raw_result": result,
                    "analysis": analysis
                })
                
                # Small delay between requests
                time.sleep(2)
            
            results.append(prompt_results)
        
        return results
    
    def generate_comparison_report(self, results: List[Dict]) -> str:
        """
        Generate a detailed comparison report.
        """
        report = []
        report.append("=" * 100)
        report.append("OPENCODE AGENT EVALUATION REPORT")
        report.append("=" * 100)
        report.append("")
        
        for idx, prompt_result in enumerate(results, 1):
            report.append(f"\n{'='*100}")
            report.append(f"PROMPT {idx}: {prompt_result['prompt']}")
            report.append(f"{'='*100}\n")
            
            for model_result in prompt_result["model_results"]:
                model = model_result["model"]
                analysis = model_result["analysis"]
                raw = model_result["raw_result"]
                
                report.append(f"\n{'-'*100}")
                report.append(f"MODEL: {model}")
                report.append(f"{'-'*100}")
                report.append(f"Success: {analysis['success']}")
                report.append(f"Execution Time: {analysis['execution_time']:.2f}s")
                report.append(f"Tools Used ({analysis['metrics']['tool_count']}): {', '.join(analysis['metrics']['tools_used'])}")
                report.append(f"File Operations: {', '.join(analysis['metrics']['file_operations']) if analysis['metrics']['file_operations'] else 'None'}")
                report.append(f"Search Operations: {', '.join(analysis['metrics']['search_operations']) if analysis['metrics']['search_operations'] else 'None'}")
                report.append(f"Has Code: {analysis['metrics']['has_code']}")
                report.append(f"Response Length: {analysis['metrics']['response_length']} chars")
                report.append(f"Has Errors: {analysis['metrics']['has_errors']}")
                
                if raw.get("stdout"):
                    report.append(f"\nOutput Preview (first 500 chars):")
                    report.append("-" * 50)
                    report.append(raw["stdout"][:500])
                    report.append("-" * 50)
                
                if raw.get("stderr"):
                    report.append(f"\nErrors:")
                    report.append("-" * 50)
                    report.append(raw["stderr"][:500])
                    report.append("-" * 50)
                
                report.append("")
        
        # Summary statistics
        report.append(f"\n{'='*100}")
        report.append("SUMMARY STATISTICS")
        report.append(f"{'='*100}\n")
        
        all_models = set()
        model_stats = {}
        
        for prompt_result in results:
            for model_result in prompt_result["model_results"]:
                model = model_result["model"]
                all_models.add(model)
                
                if model not in model_stats:
                    model_stats[model] = {
                        "total_runs": 0,
                        "successful_runs": 0,
                        "total_time": 0,
                        "total_tools": 0,
                        "total_errors": 0
                    }
                
                stats = model_stats[model]
                analysis = model_result["analysis"]
                
                stats["total_runs"] += 1
                if analysis["success"]:
                    stats["successful_runs"] += 1
                stats["total_time"] += analysis["execution_time"]
                stats["total_tools"] += analysis["metrics"]["tool_count"]
                if analysis["metrics"]["has_errors"]:
                    stats["total_errors"] += 1
        
        for model in sorted(all_models):
            stats = model_stats[model]
            report.append(f"\nModel: {model}")
            report.append(f"  Total Runs: {stats['total_runs']}")
            report.append(f"  Success Rate: {stats['successful_runs']}/{stats['total_runs']} ({100*stats['successful_runs']/stats['total_runs']:.1f}%)")
            report.append(f"  Avg Execution Time: {stats['total_time']/stats['total_runs']:.2f}s")
            report.append(f"  Avg Tools Used: {stats['total_tools']/stats['total_runs']:.1f}")
            report.append(f"  Error Rate: {stats['total_errors']}/{stats['total_runs']} ({100*stats['total_errors']/stats['total_runs']:.1f}%)")
        
        report.append(f"\n{'='*100}")
        
        return "\n".join(report)
    
    def save_results(self, results: List[Dict], output_file: str):
        """Save results to a JSON file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")


def main():
    """Example usage of the OpencodeEvaluator."""
    
    # Configuration
    TEST_REPO_PATH = os.getenv("TEST_REPO_PATH", ".")
    
    # Models to test
    models = [
        "openrouter/openai/gpt-oss-120b",
        "openrouter/openai/gpt-oss-20b",
        "openrouter/qwen/qwen3-coder",
        "openrouter/deepseek/deepseek-chat-v3-0324"
    ]
    
    # Test prompts
    prompts = [
        "List all Python files in this repository",
        "Find all functions that contain 'evaluate' in their name",
        "Show me the main entry point of this application",
        "What dependencies does this project use?",
        "Create a simple test file for the main module"
    ]
    
    # Initialize evaluator
    evaluator = OpencodeEvaluator(TEST_REPO_PATH)
    
    # Run comparison
    logger.info("Starting model comparison...")
    results = evaluator.compare_models(models, prompts)
    
    # Generate report
    report = evaluator.generate_comparison_report(results)
    print(report)
    
    # Save results
    evaluator.save_results(results, "opencode_evaluation_results.json")
    
    # Save report
    with open("opencode_evaluation_report.txt", "w") as f:
        f.write(report)
    logger.info("Report saved to opencode_evaluation_report.txt")


if __name__ == "__main__":
    main()
