#!/usr/bin/env python3
"""
Advanced CLI tool to test opencode agent evaluation with configuration support.
Usage: 
  python run_opencode_eval.py --config opencode_test_config.json
  python run_opencode_eval.py --scenario "Basic Code Understanding"
  python run_opencode_eval.py --repo PATH --models MODEL1,MODEL2 --prompt "Your prompt"
"""

import argparse
import sys
import json
from pathlib import Path
from opencode_evaluation import OpencodeEvaluator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_file: str) -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        sys.exit(1)


def run_scenario(evaluator: OpencodeEvaluator, scenario: dict, output_prefix: str):
    """Run a specific test scenario."""
    logger.info("="*80)
    logger.info(f"SCENARIO: {scenario['name']}")
    logger.info("="*80)
    logger.info(f"Models: {', '.join(scenario['models'])}")
    logger.info(f"Prompts: {len(scenario['prompts'])}")
    logger.info(f"Timeout: {scenario.get('timeout', 120)}s")
    logger.info("="*80)
    
    results = evaluator.compare_models(
        scenario['models'],
        scenario['prompts']
    )
    
    report = evaluator.generate_comparison_report(results)
    print("\n" + report)
    
    scenario_name = scenario['name'].lower().replace(' ', '_')
    json_file = f"{output_prefix}_{scenario_name}.json"
    txt_file = f"{output_prefix}_{scenario_name}.txt"
    
    evaluator.save_results(results, json_file)
    
    with open(txt_file, 'w') as f:
        f.write(report)
    
    logger.info(f"\n✅ Results saved to:")
    logger.info(f"   - {json_file}")
    logger.info(f"   - {txt_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test opencode agent with different models and scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with configuration file
  python run_opencode_eval.py --config opencode_test_config.json
  
  # Run specific scenario
  python run_opencode_eval.py --config opencode_test_config.json --scenario "Basic Code Understanding"
  
  # Run all scenarios
  python run_opencode_eval.py --config opencode_test_config.json --all
  
  # Quick test without config
  python run_opencode_eval.py --models "openrouter/openai/gpt-oss-120b" --prompt "List Python files"
        """
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration JSON file"
    )
    
    parser.add_argument(
        "--scenario",
        help="Name of specific scenario to run from config"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios from config"
    )
    
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the test repository (default: current directory)"
    )
    
    parser.add_argument(
        "--models",
        help="Comma-separated list of models to test"
    )
    
    parser.add_argument(
        "--prompt",
        help="Single prompt to test"
    )
    
    parser.add_argument(
        "--prompts",
        help="Comma-separated list of prompts to test"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds for each query (default: 120)"
    )
    
    parser.add_argument(
        "--output",
        default="opencode_eval",
        help="Output file prefix (default: opencode_eval)"
    )
    
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios from config and exit"
    )
    
    args = parser.parse_args()
    
    evaluator = OpencodeEvaluator(args.repo)
    
    if args.config:
        config = load_config(args.config)
        
        if args.list_scenarios:
            logger.info("Available scenarios:")
            for i, scenario in enumerate(config.get('test_configurations', []), 1):
                logger.info(f"  {i}. {scenario['name']}")
                logger.info(f"     Models: {len(scenario['models'])}")
                logger.info(f"     Prompts: {len(scenario['prompts'])}")
            return 0
        
        if args.all:
            logger.info(f"Running all {len(config['test_configurations'])} scenarios...")
            all_results = []
            
            for scenario in config['test_configurations']:
                try:
                    results = run_scenario(evaluator, scenario, args.output)
                    all_results.append({
                        'scenario': scenario['name'],
                        'results': results
                    })
                    logger.info("\n" + "="*80 + "\n")
                except Exception as e:
                    logger.error(f"Error in scenario '{scenario['name']}': {e}")
                    continue
            
            summary_file = f"{args.output}_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            logger.info(f"\n✅ Summary saved to: {summary_file}")
            
            return 0
        
        elif args.scenario:
            scenarios = config.get('test_configurations', [])
            matching = [s for s in scenarios if s['name'] == args.scenario]
            
            if not matching:
                logger.error(f"Scenario '{args.scenario}' not found in config")
                logger.info("Available scenarios:")
                for scenario in scenarios:
                    logger.info(f"  - {scenario['name']}")
                return 1
            
            try:
                run_scenario(evaluator, matching[0], args.output)
                return 0
            except Exception as e:
                logger.error(f"Error running scenario: {e}", exc_info=True)
                return 1
        
        else:
            logger.info("Using default configuration from config file")
            models = config.get('default_models', [])
            prompts = config.get('default_prompts', [])
    
    else:
        if not args.models:
            logger.error("Either --config or --models must be provided")
            return 1
        
        models = [m.strip() for m in args.models.split(',')]
        
        if args.prompt:
            prompts = [args.prompt]
        elif args.prompts:
            prompts = [p.strip() for p in args.prompts.split(',')]
        else:
            prompts = [
                "List all Python files in this repository",
                "Find all functions that contain 'evaluate' in their name",
                "Show me the main entry point of this application",
                "What dependencies does this project use?",
            ]
    
    logger.info("="*80)
    logger.info("OPENCODE AGENT EVALUATION")
    logger.info("="*80)
    logger.info(f"Repository: {args.repo}")
    logger.info(f"Models: {', '.join(models)}")
    logger.info(f"Prompts: {len(prompts)}")
    logger.info(f"Timeout: {args.timeout}s")
    logger.info("="*80)
    
    try:
        results = evaluator.compare_models(models, prompts)
        
        report = evaluator.generate_comparison_report(results)
        print("\n" + report)
        
        json_file = f"{args.output}.json"
        txt_file = f"{args.output}.txt"
        
        evaluator.save_results(results, json_file)
        
        with open(txt_file, 'w') as f:
            f.write(report)
        
        logger.info(f"\n✅ Results saved to:")
        logger.info(f"   - {json_file}")
        logger.info(f"   - {txt_file}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Evaluation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Error during evaluation: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
