# vLLM vs OpenRouter Evaluations

This repository contains two complementary evaluation flows for comparing model behavior across local vLLM and OpenRouter providers.

## Code Generation Evaluation
- Location: `codegen/`
- Primary entrypoint: `streamlit run codegen/app.py`
- Utilities: `model_service.py`, `code_evaluation.py`, `code_ingestion.py`
- Reference: [CODE_EVALUATION.md](codegen/CODE_EVALUATION.md) (@CODE_EVALUATION.md)

## Opencode Agent Evaluation
- Location: `opencode/`
- Primary entrypoint: `streamlit run opencode/opencode_app.py`
- Dashboards and CLIs: `opencode_app.py`, `test_opencode.py`, `run_opencode_eval.py`
- Configuration and artifacts: `opencode_test_config.json`, `opencode_test_results.*`
- Reference: [OPENCODE_EVALUATION.md](opencode/OPENCODE_EVALUATION.md) (@OPENCODE_EVALUATION.md)

Each evaluation can be run independently; see the linked documents for full setup and usage guidance.
