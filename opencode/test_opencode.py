#!/usr/bin/env python3
"""
Quick CLI tool to test opencode agent evaluation.
Usage: python test_opencode.py [--repo PATH] [--models MODEL1,MODEL2] [--prompt "Your prompt"]
"""

import argparse
import sys
from opencode_evaluation import OpencodeEvaluator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Test opencode agent with different models"
    )
    
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the test repository (default: current directory)"
    )
    
    parser.add_argument(
        "--models",
        default="openrouter/openai/gpt-oss-120b,openrouter/openai/gpt-oss-20b",
        help="Comma-separated list of models to test"
    )
    
    parser.add_argument(
        "--prompt",
        help="Single prompt to test (if not provided, uses default prompts)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds for each query (default: 120)"
    )
    
    parser.add_argument(
        "--output",
        default="opencode_test_results",
        help="Output file prefix (default: opencode_test_results)"
    )
    
    args = parser.parse_args()
    
    models = [m.strip() for m in args.models.split(',')]
    
    if args.prompt:
        prompts = [args.prompt]
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
    
    evaluator = OpencodeEvaluator(args.repo)
    
    try:
        results = evaluator.compare_models(models, prompts, timeout=args.timeout)
        
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
