#!/usr/bin/env python3
"""
Simple example demonstrating opencode agent evaluation.
This script runs a quick test comparing two models on a simple task.
"""

from opencode_evaluation import OpencodeEvaluator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("="*80)
    print("OPENCODE AGENT EVALUATION - SIMPLE EXAMPLE")
    print("="*80)
    print()
    print("This example will:")
    print("  1. Test two models (gpt-oss-20b in lmstudio and openrouter)")
    print("  2. Run a simple query: 'List all Python files in this repository'")
    print("  3. Compare their responses and tool usage")
    print()
    print("="*80)
    print()
    
    input("Press Enter to start the evaluation...")
    print()
    
    evaluator = OpencodeEvaluator(".")
    
    models = [
        "openrouter/openai/gpt-oss-20b",
        "lmstudio/openai/gpt-oss-20b"
    ]
    
    prompt = "List all Python files in this repository"
    
    logger.info(f"Testing prompt: {prompt}")
    logger.info(f"Models: {', '.join(models)}")
    print()
    
    results = []
    
    for model in models:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing: {model}")
        logger.info(f"{'='*80}\n")
        
        result = evaluator.run_opencode_query(model, prompt, timeout=120)
        analysis = evaluator.analyze_agent_response(result)
        
        results.append({
            "model": model,
            "result": result,
            "analysis": analysis
        })
        
        print(f"\n{'-'*80}")
        print(f"Model: {model.split('/')[-1]}")
        print(f"{'-'*80}")
        print(f"Success: {'✅' if analysis['success'] else '❌'}")
        print(f"Execution Time: {analysis['execution_time']:.2f}s")
        print(f"Tools Used: {', '.join(analysis['metrics']['tools_used']) if analysis['metrics']['tools_used'] else 'None'}")
        print(f"Tool Count: {analysis['metrics']['tool_count']}")
        print(f"Has Errors: {'⚠️ Yes' if analysis['metrics']['has_errors'] else '✅ No'}")
        print(f"Response Length: {analysis['metrics']['response_length']} chars")
        
        if result.get('stdout'):
            print(f"\nOutput Preview (first 300 chars):")
            print("-" * 40)
            print(result['stdout'][:300])
            if len(result['stdout']) > 300:
                print("...")
            print("-" * 40)
        
        print()
    
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    
    for i, r in enumerate(results):
        model_name = r['model'].split('/')[-1]
        analysis = r['analysis']
        
        print(f"\n{i+1}. {model_name}")
        print(f"   Success: {analysis['success']}")
        print(f"   Time: {analysis['execution_time']:.2f}s")
        print(f"   Tools: {analysis['metrics']['tool_count']}")
        print(f"   Errors: {analysis['metrics']['has_errors']}")
    
    if len(results) == 2:
        r1, r2 = results
        a1, a2 = r1['analysis'], r2['analysis']
        
        print(f"\n{'='*80}")
        print("WINNER ANALYSIS")
        print(f"{'='*80}")
        
        if a1['execution_time'] < a2['execution_time']:
            print(f"⚡ Faster: {r1['model'].split('/')[-1]} ({a1['execution_time']:.2f}s vs {a2['execution_time']:.2f}s)")
        else:
            print(f"⚡ Faster: {r2['model'].split('/')[-1]} ({a2['execution_time']:.2f}s vs {a1['execution_time']:.2f}s)")
        
        if a1['metrics']['tool_count'] > a2['metrics']['tool_count']:
            print(f"🔧 More Tools: {r1['model'].split('/')[-1]} ({a1['metrics']['tool_count']} vs {a2['metrics']['tool_count']})")
        elif a2['metrics']['tool_count'] > a1['metrics']['tool_count']:
            print(f"🔧 More Tools: {r2['model'].split('/')[-1]} ({a2['metrics']['tool_count']} vs {a1['metrics']['tool_count']})")
        else:
            print(f"🔧 Same Tool Count: {a1['metrics']['tool_count']}")
        
        if not a1['metrics']['has_errors'] and a2['metrics']['has_errors']:
            print(f"✅ No Errors: {r1['model'].split('/')[-1]}")
        elif not a2['metrics']['has_errors'] and a1['metrics']['has_errors']:
            print(f"✅ No Errors: {r2['model'].split('/')[-1]}")
        elif not a1['metrics']['has_errors'] and not a2['metrics']['has_errors']:
            print(f"✅ Both models completed without errors")
        else:
            print(f"⚠️ Both models had errors")
    
    print(f"\n{'='*80}")
    print("Example complete!")
    print(f"{'='*80}\n")
    
    print("Next steps:")
    print("  • Run the full dashboard: streamlit run opencode_app.py")
    print("  • Try more models: python test_opencode.py --models 'model1,model2'")
    print("  • Run all scenarios: python run_opencode_eval.py --config opencode_test_config.json --all")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
