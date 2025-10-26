# Opencode Agent Evaluation

This module provides comprehensive evaluation tools for testing AI models as coding agents using the [opencode](https://github.com/sst/opencode) framework.

## Overview

The evaluation system tests how well different AI models perform when acting as coding agents, measuring:

- **Tool Usage**: Which tools the agent uses (file operations, search, terminal commands, etc.)
- **Response Quality**: Completeness, accuracy, and relevance of responses
- **Execution Time**: How fast the agent responds
- **Error Handling**: Whether the agent encounters errors
- **Code Generation**: Quality of generated code

## Files

- `opencode_evaluation.py` - Core evaluation logic and OpencodeEvaluator class
- `opencode_app.py` - Streamlit dashboard for interactive evaluation
- `test_opencode.py` - CLI tool for quick testing
- `run_opencode_eval.py` - Configuration-based evaluation runner
- `opencode_test_config.json` - Test scenarios and configurations

## Installation

### Prerequisites

Install opencode:

```bash
npm install -g @opencode/cli
# or
pnpm install -g @opencode/cli

# Verify installation
opencode --help

# Configure API keys (if needed)
opencode auth
```

Install Python dependencies:

```bash
pip install streamlit pandas plotly
```

## 🚀 Quick Start (5 minutes)

### Option A: Streamlit Dashboard (Recommended)

```bash
streamlit run opencode_app.py
```

Then:
1. Select models (e.g., gpt-oss-120b, gpt-oss-20b)
2. Choose default prompts or add custom ones
3. Click "Run Evaluation"
4. View results and export reports

### Option B: CLI Tool

```bash
# Quick test with defaults
python test_opencode.py

# Test specific models
python test_opencode.py --models "openrouter/openai/gpt-oss-120b,openrouter/qwen/qwen3-coder"

# Test with custom prompt
python test_opencode.py --prompt "List all Python files in this repository"

# Test in a specific repository
python test_opencode.py --repo /path/to/your/repo

# Full example
python test_opencode.py \
  --repo /path/to/repo \
  --models "openrouter/openai/gpt-oss-120b,openrouter/deepseek/deepseek-chat-v3-0324" \
  --prompt "Refactor the main function to use async/await" \
  --timeout 180 \
  --output my_test_results
```

### Option C: Configuration-Based Testing

```bash
# List available scenarios
python run_opencode_eval.py --config opencode_test_config.json --list-scenarios

# Run specific scenario
python run_opencode_eval.py --config opencode_test_config.json --scenario "Basic Code Understanding"

# Run all scenarios
python run_opencode_eval.py --config opencode_test_config.json --all
```

## Usage

### 1. Python API

Use the evaluator programmatically:

```python
from opencode_evaluation import OpencodeEvaluator

# Initialize
evaluator = OpencodeEvaluator("/path/to/test/repo")

# Define models and prompts
models = [
    "openrouter/openai/gpt-oss-120b",
    "openrouter/qwen/qwen3-coder"
]

prompts = [
    "List all Python files",
    "Find functions with 'test' in the name"
]

# Run evaluation
results = evaluator.compare_models(models, prompts)

# Generate report
report = evaluator.generate_comparison_report(results)
print(report)

# Save results
evaluator.save_results(results, "results.json")

# Or run a single query
results = evaluator.run_opencode_query(
    model="openrouter/openai/gpt-oss-120b",
    prompt="List all Python files"
)

analysis = evaluator.analyze_agent_response(results)
print(f"Tools used: {analysis['metrics']['tools_used']}")
print(f"Success: {analysis['success']}")
```

### 2. Custom Test Configuration

Edit `opencode_test_config.json`:

```json
{
  "test_configurations": [
    {
      "name": "My Custom Test",
      "models": [
        "openrouter/openai/gpt-oss-120b",
        "openrouter/qwen/qwen3-coder"
      ],
      "prompts": [
        "Your custom prompt 1",
        "Your custom prompt 2"
      ],
      "timeout": 120
    }
  ]
}
```

Then run:

```bash
python run_opencode_eval.py --config opencode_test_config.json --scenario "My Custom Test"
```

## Supported Models

The evaluation supports any model available in opencode. Common options:

### OpenRouter Models
- `openrouter/openai/gpt-oss-120b` - GPT-OSS 120B
- `openrouter/openai/gpt-oss-20b` - GPT-OSS 20B
- `openrouter/qwen/qwen3-coder` - Qwen3 Coder
- `openrouter/deepseek/deepseek-chat-v3-0324` - DeepSeek Chat v3
- `openrouter/anthropic/claude-sonnet-4` - Claude Sonnet 4
- `openrouter/google/gemini-2.5-flash` - Gemini 2.5 Flash
- `openrouter/mistralai/codestral-2508` - Mistral Codestral

### Local Models (if configured)
- `ollama/gpt-oss:20b`
- `lmstudio/openai/gpt-oss-20b`

Check available models:
```bash
opencode models
```

## Test Prompts

### Default Prompts

The evaluation includes these default prompts:

1. "List all Python files in this repository"
2. "Find all functions that contain 'evaluate' in their name"
3. "Show me the main entry point of this application"
4. "What dependencies does this project use?"

### Custom Prompts

You can test with any prompts relevant to your use case:

**Code Understanding:**
- "Explain what this codebase does"
- "Find all API endpoints in this project"
- "Show me the database schema"

**Code Search:**
- "Find all TODO comments"
- "Locate error handling code"
- "Find all test files"

**Code Generation:**
- "Create a new API endpoint for user authentication"
- "Add error handling to the main function"
- "Write unit tests for the UserService class"

**Code Modification:**
- "Refactor the database connection code"
- "Add logging to all API endpoints"
- "Update the README with installation instructions"

## 🎯 Common Use Cases

### 1. Compare Two Models

```bash
python test_opencode.py \
  --models "openrouter/openai/gpt-oss-120b,openrouter/openai/gpt-oss-20b" \
  --prompt "Find all TODO comments in the codebase"
```

### 2. Test Code Understanding

```bash
python run_opencode_eval.py \
  --config opencode_test_config.json \
  --scenario "Basic Code Understanding"
```

### 3. Test Code Generation

```bash
python test_opencode.py \
  --models "openrouter/qwen/qwen3-coder" \
  --prompt "Create a simple test file for the main module"
```

### 4. Test on Different Repository

```bash
python test_opencode.py \
  --repo /path/to/your/project \
  --models "openrouter/openai/gpt-oss-120b" \
  --prompt "Analyze the project structure"
```

## Evaluation Metrics

The evaluator tracks these metrics for each model:

### Success Metrics
- **Success Rate**: Percentage of queries completed without errors
- **Execution Time**: Average time to complete queries
- **Tool Count**: Number of tools used per query

### Quality Metrics
- **Tools Used**: Which specific tools were invoked
- **File Operations**: Read, edit, create, delete operations
- **Search Operations**: Grep, file search, semantic search
- **Has Code**: Whether the response includes code
- **Response Length**: Size of the response
- **Error Rate**: Percentage of queries with errors

### Understanding Metrics

| Metric | Description | Good Value |
|--------|-------------|------------|
| Success Rate | % of queries completed without errors | > 90% |
| Execution Time | Average time per query | < 10s |
| Tools Used | Number of tools invoked | 2-5 |
| Error Rate | % of queries with errors | < 10% |
| Response Length | Size of response | Varies |

## Output Format

### Results Location

Results are saved in multiple formats:

- **JSON**: `opencode_eval.json` - Machine-readable results
- **Text Report**: `opencode_eval.txt` - Human-readable summary
- **Dashboard**: Interactive charts in Streamlit

### JSON Results

```json
[
  {
    "prompt": "List all Python files",
    "model_results": [
      {
        "model": "openrouter/openai/gpt-oss-120b",
        "raw_result": {
          "stdout": "...",
          "stderr": "...",
          "returncode": 0,
          "execution_time": 5.23,
          "success": true
        },
        "analysis": {
          "success": true,
          "execution_time": 5.23,
          "metrics": {
            "tools_used": ["list_dir", "file_search"],
            "tool_count": 2,
            "has_errors": false,
            "response_length": 1234,
            "has_code": false,
            "file_operations": ["read"],
            "search_operations": ["search"]
          }
        }
      }
    ]
  }
]
```

### Text Report Example

```
================================================================================
OPENCODE AGENT EVALUATION REPORT
================================================================================

PROMPT 1: List all Python files in this repository
================================================================================

Model: gpt-oss-120b
--------------------------------------------------------------------------------
Success: True
Execution Time: 5.23s
Tools Used (2): list_dir, file_search
File Operations: read
Search Operations: search
Has Code: False
Response Length: 1234 chars
Has Errors: False

Model: gpt-oss-20b
--------------------------------------------------------------------------------
Success: True
Execution Time: 4.87s
Tools Used (3): list_dir, file_search, grep_search
File Operations: read
Search Operations: search, find
Has Code: False
Response Length: 1156 chars
Has Errors: False

================================================================================
SUMMARY STATISTICS
================================================================================

Model: gpt-oss-120b
  Total Runs: 4
  Success Rate: 4/4 (100.0%)
  Avg Execution Time: 5.45s
  Avg Tools Used: 2.5
  Error Rate: 0/4 (0.0%)

Model: gpt-oss-20b
  Total Runs: 4
  Success Rate: 4/4 (100.0%)
  Avg Execution Time: 5.12s
  Avg Tools Used: 2.8
  Error Rate: 0/4 (0.0%)
```

## Example Workflow

1. **Setup**: Choose a test repository with representative code
2. **Select Models**: Pick 2-4 models to compare
3. **Define Prompts**: Create prompts that test different capabilities
4. **Run Evaluation**: Execute via dashboard or CLI
5. **Analyze Results**: Review metrics and outputs
6. **Export**: Save results for documentation or further analysis

## Tips for Effective Evaluation

1. **Use Diverse Prompts**: Test different types of tasks (search, generation, modification)
2. **Test on Real Code**: Use actual repositories, not toy examples
3. **Compare Apples to Apples**: Use the same prompts for all models
4. **Consider Context**: Some models may be better at specific tasks
5. **Check Tool Usage**: Models that use appropriate tools are often more reliable
6. **Review Outputs**: Don't just look at metrics - read the actual responses
7. **Start Small**: Begin with 2-3 models to keep evaluation time reasonable
8. **Export Results**: Save results for documentation and tracking

## Troubleshooting

### "opencode: command not found"

```bash
npm install -g @opencode/cli
```

### Timeout Errors

Increase timeout:

```bash
python test_opencode.py --timeout 300
```

### Model Not Available

Check available models:

```bash
opencode models | grep "gpt-oss"
```

### API Key Issues

Configure authentication:

```bash
opencode auth
```

## Integration with Existing Evaluation

This opencode evaluation complements the existing code generation evaluation:

- **app.py**: Tests direct code generation (input → code output)
- **opencode_app.py**: Tests agent behavior (query → tool usage → response)

Both evaluations together provide a complete picture of model capabilities. Use both to get comprehensive insights!

## Future Enhancements

Potential improvements:
- [ ] Add support for multi-turn conversations
- [ ] Track token usage and costs
- [ ] Add semantic similarity scoring for responses
- [ ] Support for custom tool detection
- [ ] Integration with CI/CD pipelines
- [ ] Benchmark against human developer performance

## License

Same as parent project.
