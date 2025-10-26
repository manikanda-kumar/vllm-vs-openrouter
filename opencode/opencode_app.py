import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from opencode.opencode_evaluation import OpencodeEvaluator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Opencode Agent Evaluation",
    layout="wide"
)

st.markdown("""
<style>
    .stMarkdown {
        width: 100%;
    }
    pre {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        max-width: 100% !important;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None
if 'test_repo_path' not in st.session_state:
    st.session_state.test_repo_path = os.getcwd()

st.title("🤖 Opencode Agent Evaluation Dashboard")
st.markdown("Compare how different models perform as coding agents using opencode")

with st.sidebar:
    st.header("Configuration")
    
    test_repo_path = st.text_input(
        "Test Repository Path",
        value=st.session_state.test_repo_path,
        help="Path to the repository where opencode will be tested"
    )
    st.session_state.test_repo_path = test_repo_path
    
    st.write("---")
    
    st.subheader("Models to Test")
    
    available_models = {
        "gpt-oss-120b (OpenRouter)": "openrouter/openai/gpt-oss-120b",
        "gpt-oss-20b (OpenRouter)": "openrouter/openai/gpt-oss-20b",
        "Qwen3 Coder": "openrouter/qwen/qwen3-coder",
        "DeepSeek Chat v3": "openrouter/deepseek/deepseek-chat-v3-0324",
        "Claude Sonnet 4": "openrouter/anthropic/claude-sonnet-4",
        "GPT-4.1 Mini": "openrouter/openai/gpt-4.1-mini",
        "Gemini 2.5 Flash": "openrouter/google/gemini-2.5-flash",
        "Mistral Codestral": "openrouter/mistralai/codestral-2508"
    }
    
    selected_model_names = st.multiselect(
        "Select Models",
        options=list(available_models.keys()),
        default=["gpt-oss-120b (OpenRouter)", "gpt-oss-20b (OpenRouter)"],
        help="Choose which models to evaluate"
    )
    
    selected_models = [available_models[name] for name in selected_model_names]
    
    st.write("---")
    
    st.subheader("Test Prompts")
    
    default_prompts = [
        "List all Python files in this repository",
        "Find all functions that contain 'evaluate' in their name",
        "Show me the main entry point of this application",
        "What dependencies does this project use?",
    ]
    
    use_default_prompts = st.checkbox("Use default prompts", value=True)
    
    if use_default_prompts:
        prompts = default_prompts
        st.info(f"Using {len(prompts)} default prompts")
    else:
        custom_prompts = st.text_area(
            "Custom Prompts (one per line)",
            height=200,
            help="Enter one prompt per line"
        )
        prompts = [p.strip() for p in custom_prompts.split('\n') if p.strip()]
    
    st.write("---")
    
    timeout = st.slider(
        "Timeout (seconds)",
        min_value=30,
        max_value=300,
        value=120,
        help="Maximum time to wait for each query"
    )
    
    st.write("---")
    
    if st.button("🚀 Run Evaluation", type="primary", use_container_width=True):
        if not selected_models:
            st.error("Please select at least one model")
        elif not prompts:
            st.error("Please provide at least one prompt")
        else:
            with st.spinner("Running evaluation... This may take several minutes."):
                try:
                    evaluator = OpencodeEvaluator(test_repo_path)
                    results = evaluator.compare_models(selected_models, prompts)
                    st.session_state.evaluation_results = results
                    st.success("Evaluation complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during evaluation: {str(e)}")
                    logger.error(f"Evaluation error: {str(e)}", exc_info=True)

if st.session_state.evaluation_results:
    results = st.session_state.evaluation_results
    
    st.header("📊 Evaluation Results")
    
    all_model_stats = {}
    
    for prompt_result in results:
        for model_result in prompt_result["model_results"]:
            model = model_result["model"]
            analysis = model_result["analysis"]
            
            if model not in all_model_stats:
                all_model_stats[model] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "total_time": 0,
                    "total_tools": 0,
                    "total_errors": 0,
                    "response_lengths": []
                }
            
            stats = all_model_stats[model]
            stats["total_runs"] += 1
            if analysis["success"]:
                stats["successful_runs"] += 1
            stats["total_time"] += analysis["execution_time"]
            stats["total_tools"] += analysis["metrics"]["tool_count"]
            if analysis["metrics"]["has_errors"]:
                stats["total_errors"] += 1
            stats["response_lengths"].append(analysis["metrics"]["response_length"])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Prompts", len(results))
    with col2:
        st.metric("Models Tested", len(all_model_stats))
    with col3:
        total_runs = sum(s["total_runs"] for s in all_model_stats.values())
        st.metric("Total Runs", total_runs)
    with col4:
        avg_time = sum(s["total_time"] for s in all_model_stats.values()) / total_runs
        st.metric("Avg Time", f"{avg_time:.1f}s")
    
    st.write("---")
    
    st.subheader("Model Performance Comparison")
    
    comparison_data = []
    for model, stats in all_model_stats.items():
        model_name = model.split('/')[-1]
        comparison_data.append({
            "Model": model_name,
            "Success Rate (%)": 100 * stats["successful_runs"] / stats["total_runs"],
            "Avg Time (s)": stats["total_time"] / stats["total_runs"],
            "Avg Tools Used": stats["total_tools"] / stats["total_runs"],
            "Error Rate (%)": 100 * stats["total_errors"] / stats["total_runs"],
            "Avg Response Length": sum(stats["response_lengths"]) / len(stats["response_lengths"])
        })
    
    df = pd.DataFrame(comparison_data)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Success Rate", "⏱️ Execution Time", "🔧 Tool Usage", "📝 Response Quality"])
    
    with tab1:
        fig = px.bar(
            df,
            x="Model",
            y="Success Rate (%)",
            title="Success Rate by Model",
            color="Success Rate (%)",
            color_continuous_scale="Viridis",
            template="plotly_dark"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.bar(
            df,
            x="Model",
            y="Avg Time (s)",
            title="Average Execution Time by Model",
            color="Avg Time (s)",
            color_continuous_scale="Plasma",
            template="plotly_dark"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.bar(
            df,
            x="Model",
            y="Avg Tools Used",
            title="Average Tools Used by Model",
            color="Avg Tools Used",
            color_continuous_scale="Cividis",
            template="plotly_dark"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                df,
                x="Model",
                y="Error Rate (%)",
                title="Error Rate by Model",
                color="Error Rate (%)",
                color_continuous_scale="Reds",
                template="plotly_dark"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                df,
                x="Model",
                y="Avg Response Length",
                title="Average Response Length by Model",
                color="Avg Response Length",
                color_continuous_scale="Blues",
                template="plotly_dark"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    st.write("---")
    
    st.subheader("Detailed Results by Prompt")
    
    for idx, prompt_result in enumerate(results, 1):
        with st.expander(f"📝 Prompt {idx}: {prompt_result['prompt']}", expanded=False):
            for model_result in prompt_result["model_results"]:
                model = model_result["model"]
                analysis = model_result["analysis"]
                raw = model_result["raw_result"]
                
                st.markdown(f"### {model.split('/')[-1]}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Success", "✅" if analysis["success"] else "❌")
                with col2:
                    st.metric("Time", f"{analysis['execution_time']:.2f}s")
                with col3:
                    st.metric("Tools Used", analysis["metrics"]["tool_count"])
                with col4:
                    st.metric("Has Errors", "⚠️" if analysis["metrics"]["has_errors"] else "✅")
                
                if analysis["metrics"]["tools_used"]:
                    st.write("**Tools Used:**", ", ".join(analysis["metrics"]["tools_used"]))
                
                if analysis["metrics"]["file_operations"]:
                    st.write("**File Operations:**", ", ".join(analysis["metrics"]["file_operations"]))
                
                if analysis["metrics"]["search_operations"]:
                    st.write("**Search Operations:**", ", ".join(analysis["metrics"]["search_operations"]))
                
                st.write(f"**Has Code:** {'Yes' if analysis['metrics']['has_code'] else 'No'}")
                st.write(f"**Response Length:** {analysis['metrics']['response_length']} characters")
                
                if raw.get("stdout"):
                    st.write("**Output:**")
                    st.code(raw["stdout"], language="text")

                if raw.get("stderr"):
                    st.write("**Errors:**")
                    st.code(raw["stderr"], language="text")
                
                st.write("---")
    
    st.write("---")
    
    st.subheader("📥 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download JSON Results"):
            json_str = json.dumps(results, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="opencode_evaluation_results.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("Generate Text Report"):
            evaluator = OpencodeEvaluator(st.session_state.test_repo_path)
            report = evaluator.generate_comparison_report(results)
            st.download_button(
                label="Download Report",
                data=report,
                file_name="opencode_evaluation_report.txt",
                mime="text/plain"
            )

else:
    st.info("👈 Configure your evaluation settings in the sidebar and click 'Run Evaluation' to start")
    
    st.markdown("""
    ### About This Tool
    
    This dashboard helps you evaluate how different AI models perform as coding agents using the **opencode** framework.
    
    **What it tests:**
    - ✅ Tool usage capabilities (file operations, search, etc.)
    - ✅ Response accuracy and completeness
    - ✅ Execution time and efficiency
    - ✅ Error handling
    - ✅ Code generation quality
    
    **How to use:**
    1. Select the repository path to test on
    2. Choose which models to evaluate
    3. Select test prompts (or use defaults)
    4. Click "Run Evaluation"
    5. Review the results and export reports
    
    **Supported Models:**
    - OpenAI GPT-OSS (120B, 20B)
    - Qwen3 Coder
    - DeepSeek Chat
    - Claude Sonnet
    - Gemini
    - Mistral Codestral
    - And more...
    """)
