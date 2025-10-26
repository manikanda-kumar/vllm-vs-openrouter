# gpt-oss-120b: vLLM vs OpenRouter Inference Comparison

This application compares the same model (gpt-oss-120b) running on two different inference providers: local vLLM and OpenRouter. This allows you to evaluate if issues (like tool calling problems) are caused by the inference provider or the model itself. The app uses the same evaluation harness (DeepEval) for both providers to ensure fair comparison.

**Use Case:** If you're seeing tool call issues on local vLLM, this benchmark helps determine whether it's an inference provider issue or a model/harness issue by comparing the same model on different providers.

We use:
- vLLM for local inference
- OpenRouter for cloud inference
- LiteLLM for OpenRouter orchestration
- DeepEval for evaluation
- Gitingest for ingesting code
- Streamlit for the UI

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

1. Enter a GitHub repository URL in the sidebar
2. Click "Ingest Repository" to load the repository context
3. Enter your code generation prompt in the chat
4. View the generated code from both models side by side
5. Click on "Evaluate Code" to evaluate code using DeepEval
6. View the evaluation metrics comparing both models' performance

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

## 📬 Stay Updated with Our Newsletter!
**Get a FREE Data Science eBook** 📖 with 150+ essential lessons in Data Science when you subscribe to our newsletter! Stay in the loop with the latest tutorials, insights, and exclusive resources. [Subscribe now!](https://join.dailydoseofds.com)

[![Daily Dose of Data Science Newsletter](https://github.com/patchy631/ai-engineering/blob/main/resources/join_ddods.png)](https://join.dailydoseofds.com)

---

## Contribution

Contributions are welcome! Please fork the repository and submit a pull request with your improvements. 