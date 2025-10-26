# gpt-oss-120b: vLLM vs OpenRouter Inference Comparison

This application compares the same model (gpt-oss-120b) running on two different inference providers: local vLLM and OpenRouter. This allows you to evaluate if issues (like tool calling problems) are caused by the inference provider or the model itself. The app uses the same evaluation harness (DeepEval) for both providers to ensure fair comparison.

**Use Case:** If you're seeing tool call issues on local vLLM, this benchmark helps determine whether it's an inference provider issue or a model/harness issue by comparing the same model on different providers.

We use:
- vLLM for local inference
- OpenRouter for cloud inference
- LiteLLM for OpenRouter orchestration
- DeepEval for evaluation
- Streamlit for the UI
- **NEW:** Opencode for agent evaluation

---

## 🎯 Two Evaluation Modes

This project now supports **two complementary evaluation approaches**:

### 1. **Code Generation Evaluation** (`app.py`)
Direct code generation testing: prompt → code output
- Tests raw code generation quality
- Evaluates correctness, readability, and best practices
- Uses DeepEval for scoring
- Side-by-side comparison of vLLM vs OpenRouter

### 2. **Agent Evaluation** (`opencode_app.py`) 🆕
Coding agent behavior testing: query → tool usage → response
- Tests how models perform as coding agents using [opencode](https://github.com/sst/opencode)
- Evaluates tool usage, search capabilities, and task completion
- Measures execution time and error rates
- Supports multiple models beyond gpt-oss

**Use both evaluations together for a complete picture of model capabilities!**

---

## Setup and Installation

Ensure you have Python 3.12 or later installed on your system.

Install dependencies:
```bash
uv sync
```

### Setting up vLLM Server

Start your local vLLM server with gpt-oss-120b:
```bash
vllm serve gpt-oss/gpt-oss-120b --port 8000
```

Copy `.env.example` to `.env` and configure the following environment variables:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=gpt-oss/gpt-oss-120b
VLLM_API_KEY=EMPTY
```

Run the Streamlit app:
```bash
streamlit run app.py
```

## Usage

1. Enter your code generation prompt in the sidebar and click "Generate Code"
2. (Optional) Provide reference code in the sidebar to benchmark against
3. Review the generated outputs from both providers side by side
4. Click "Evaluate Generated Code" to score the results with DeepEval
5. Inspect the detailed evaluation metrics for each provider

## Evaluation Metrics

The app evaluates generated code using three comprehensive metrics powered by DeepEval:

- **Code Correctness**: Evaluates the functional correctness of the generated code

- **Code Readability**: Measures how easy the code is to understand and maintain

- **Best Practices**: Assesses adherence to coding standards and coding best practices

Each metric is scored on a scale of 0-10, with the following general interpretation:
- 0-2: Major issues or non-functional code
- 3-5: Basic implementation with significant gaps
- 6-8: Good implementation with minor issues
- 9-10: Excellent implementation meeting all criteria

The overall score is calculated as an average of these three metrics.

---
