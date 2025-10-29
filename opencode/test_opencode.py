#!/usr/bin/env python3
"""
Quick CLI tool to test opencode agent evaluation with JSON-driven scenarios.

Usage:
  - Run all scenarios from config:
      python test_opencode.py --config config.json

  - List scenarios:
      python test_opencode.py --config config.json --list-configs

  - Run a single scenario by name:
      python test_opencode.py --config config.json --config-name "Code Search and Analysis"

  - Override models and/or repo:
      python test_opencode.py --config config.json --config-name "Code Generation" \
          --models openrouter/openai/gpt-oss-120b,openrouter/qwen/qwen3-coder --repo /path/to/repo

  - Run one ad-hoc prompt (skips config):
      python test_opencode.py --repo . --models openrouter/openai/gpt-oss-120b --prompt "List all Python files"

  - Shuffle and sample (e.g., run only 5 prompts from a scenario):
      python test_opencode.py --config config.json --config-name "Advanced Agent Tasks" --shuffle --sample-prompts 5
"""

import argparse
import sys
import os
import json
import logging
import re
import random
from typing import Any, Dict, List, Optional

from opencode_evaluation import OpencodeEvaluator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


FALLBACK_DEFAULT_MODELS = [
    "openrouter/openai/gpt-oss-120b",
    "openrouter/openai/gpt-oss-20b",
]

FALLBACK_DEFAULT_PROMPTS = [
    "List all Python files in this repository",
    "Find all functions that contain 'evaluate' in their name",
    "Show me the main entry point of this application",
    "What dependencies does this project use?",
]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_config(path: str) -> Dict[str, Any]:
    if not path:
        return {}
    if not os.path.exists(path):
        logger.warning(f"Config file not found at '{path}'. Using built-in defaults.")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read config JSON '{path}': {e}", exc_info=True)
        return {}


def extract_prompts(config_prompts: Optional[List[Any]], default_prompts: List[str]) -> List[str]:
    """
    Supports prompts as plain strings or objects like {"text": "..."}.
    """
    if not config_prompts:
        return default_prompts
    out = []
    for p in config_prompts:
        if isinstance(p, str):
            out.append(p)
        elif isinstance(p, dict):
            text = p.get("text")
            if text:
                out.append(text)
    return out or default_prompts


def choose_models(args_models: Optional[str], scenario_models: Optional[List[str]], config_defaults: List[str]) -> List[str]:
    if args_models:
        return [m.strip() for m in args_models.split(",") if m.strip()]
    if scenario_models:
        return scenario_models
    return config_defaults or FALLBACK_DEFAULT_MODELS


def run_scenario(
    evaluator: OpencodeEvaluator,
    repo: str,
    scenario_name: str,
    models: List[str],
    prompts: List[str],
    timeout: int,
    output_prefix: str,
) -> Dict[str, Any]:
    logger.info("=" * 80)
    logger.info(f"SCENARIO: {scenario_name}")
    logger.info("=" * 80)
    logger.info(f"Repository: {repo}")
    logger.info(f"Models: {', '.join(models)}")
    logger.info(f"Prompts: {len(prompts)}")
    logger.info(f"Timeout: {timeout}s")
    logger.info("=" * 80)

    results = evaluator.compare_models(models, prompts, timeout=timeout)
    report = evaluator.generate_comparison_report(results)
    print("\n" + report)

    scenario_slug = slugify(scenario_name)
    json_file = f"{output_prefix}-{scenario_slug}.json"
    txt_file = f"{output_prefix}-{scenario_slug}.txt"

    evaluator.save_results(results, json_file)
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info("\n✅ Results saved to:")
    logger.info(f"   - {json_file}")
    logger.info(f"   - {txt_file}")

    return {
        "name": scenario_name,
        "models": models,
        "prompts_count": len(prompts),
        "timeout": timeout,
        "json_file": json_file,
        "txt_file": txt_file,
        "results": results,  # Keep raw in aggregate for downstream analysis
    }


def main():
    parser = argparse.ArgumentParser(description="Test opencode agent with different models (JSON-driven).")

    parser.add_argument("--repo", default=".", help="Path to the test repository (default: current directory)")
    parser.add_argument("--models", help="Comma-separated list of models to test (overrides config)")
    parser.add_argument("--prompt", help="Single prompt to test (if set, skips config and runs an ad-hoc test)")

    parser.add_argument("--timeout", type=int, help="Timeout in seconds for each query (overrides scenario/config)")
    parser.add_argument("--output", default="opencode_test_results", help="Output file prefix (default: opencode_test_results)")

    parser.add_argument("--config", default="config.json", help="Path to JSON config file (default: config.json)")
    parser.add_argument("--config-name", help="Name of a specific test configuration to run (comma-separated allowed)")
    parser.add_argument("--list-configs", action="store_true", help="List available configuration names and exit")

    parser.add_argument("--shuffle", action="store_true", help="Shuffle prompts before running")
    parser.add_argument("--sample-prompts", type=int, help="Randomly sample N prompts from the scenario")

    args = parser.parse_args()

    # If user passed a single ad-hoc prompt, run that and exit
    if args.prompt:
        models = choose_models(args.models, None, FALLBACK_DEFAULT_MODELS)
        prompts = [args.prompt]
        timeout = args.timeout or 120

        evaluator = OpencodeEvaluator(args.repo)
        try:
            _ = run_scenario(
                evaluator=evaluator,
                repo=args.repo,
                scenario_name="Ad-hoc Prompt",
                models=models,
                prompts=prompts,
                timeout=timeout,
                output_prefix=args.output,
            )
            return 0
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Evaluation interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"\n❌ Error during evaluation: {str(e)}", exc_info=True)
            return 1

    # Otherwise, use JSON config to drive scenarios
    cfg = load_config(args.config)
    test_configurations = cfg.get("test_configurations", [])
    default_models = cfg.get("default_models", FALLBACK_DEFAULT_MODELS)
    default_prompts = cfg.get("default_prompts", FALLBACK_DEFAULT_PROMPTS)

    if args.list_configs:
        if not test_configurations:
            logger.info("No configurations found in config. You can still run with --prompt or defaults.")
        else:
            logger.info("Available configurations:")
            for i, sc in enumerate(test_configurations, 1):
                logger.info(f"  {i}. {sc.get('name', f'Unnamed-{i}')}")
        return 0

    # If no scenarios in config, fall back to one default scenario
    if not test_configurations:
        logger.warning("No 'test_configurations' found; running a Default Scenario with default prompts.")
        models = choose_models(args.models, None, default_models)
        prompts = extract_prompts(None, default_prompts)
        if args.shuffle:
            random.shuffle(prompts)
        if args.sample_prompts:
            prompts = random.sample(prompts, k=min(args.sample_prompts, len(prompts)))
        timeout = args.timeout or 120

        evaluator = OpencodeEvaluator(args.repo)
        try:
            _ = run_scenario(
                evaluator=evaluator,
                repo=args.repo,
                scenario_name="Default Scenario",
                models=models,
                prompts=prompts,
                timeout=timeout,
                output_prefix=args.output,
            )
            return 0
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Evaluation interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"\n❌ Error during evaluation: {str(e)}", exc_info=True)
            return 1

    # Filter scenarios by --config-name if provided
    selected_names: Optional[List[str]] = None
    if args.config_name:
        selected_names = [n.strip() for n in args.config_name.split(",") if n.strip()]

    scenarios = []
    for sc in test_configurations:
        name = sc.get("name") or "Unnamed Scenario"
        if selected_names and name not in selected_names:
            continue
        scenarios.append(sc)

    if not scenarios:
        logger.error("No scenarios to run. Check --config-name or your config file.")
        return 1

    evaluator = OpencodeEvaluator(args.repo)
    aggregate: Dict[str, Any] = {
        "repo": args.repo,
        "output_prefix": args.output,
        "scenarios": [],
    }

    exit_code = 0
    for sc in scenarios:
        name = sc.get("name") or "Unnamed Scenario"

        # Resolve models and prompts
        sc_models = choose_models(args.models, sc.get("models"), default_models)
        sc_prompts = extract_prompts(sc.get("prompts"), default_prompts)

        # Shuffle / sample if requested
        if args.shuffle:
            random.shuffle(sc_prompts)
        if args.sample_prompts:
            sc_prompts = random.sample(sc_prompts, k=min(args.sample_prompts, len(sc_prompts)))

        # Resolve timeout precedence: CLI > scenario > default(120)
        sc_timeout = args.timeout or sc.get("timeout") or 120

        try:
            result = run_scenario(
                evaluator=evaluator,
                repo=args.repo,
                scenario_name=name,
                models=sc_models,
                prompts=sc_prompts,
                timeout=sc_timeout,
                output_prefix=args.output,
            )
            aggregate["scenarios"].append({
                "name": name,
                "models": sc_models,
                "prompts_count": result["prompts_count"],
                "timeout": sc_timeout,
                "json_file": result["json_file"],
                "txt_file": result["txt_file"],
            })
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Evaluation interrupted by user")
            exit_code = 1
            break
        except Exception as e:
            logger.error(f"\n❌ Error during scenario '{name}': {str(e)}", exc_info=True)
            exit_code = 1
            # continue to next scenario

    # Save aggregate index
    try:
        aggregate_file = f"{args.output}-aggregate.json"
        with open(aggregate_file, "w", encoding="utf-8") as f:
            json.dump(aggregate, f, indent=2)
        logger.info(f"\n📦 Aggregate index saved to: {aggregate_file}")
    except Exception as e:
        logger.warning(f"Could not write aggregate file: {e}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())