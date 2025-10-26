import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import os
from dotenv import load_dotenv
from model_service import get_parallel_responses
from code_evaluation import evaluate_code

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("Application Starting")
logger.info("=" * 80)
logger.info("Environment Configuration:")
logger.info(f"  VLLM_BASE_URL: {os.getenv('VLLM_BASE_URL', 'http://localhost:8000/v1')}")
logger.info(f"  VLLM_MODEL_NAME: {os.getenv('VLLM_MODEL_NAME', 'openai/gpt-oss-20b')}")
logger.info(f"  VLLM_API_KEY: {'Set' if os.getenv('VLLM_API_KEY') else 'Not set (using default)'}")
logger.info(f"  OPENROUTER_API_KEY: {'Set' if os.getenv('OPENROUTER_API_KEY') else 'Not set'}")
logger.info("=" * 80)

# Set page config
st.set_page_config(
    page_title="Code Generation Model Comparison",
    layout="wide"
)

# Custom CSS for responsive code containers
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
    code {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        max-width: 100% !important;
    }
    .streamlit-expanderContent {
        width: 100% !important;
    }
    div[data-testid="stCodeBlock"] {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'reference_code' not in st.session_state:
    st.session_state.reference_code = None
if 'last_generated_code' not in st.session_state:
    st.session_state.last_generated_code = {"vllm": None, "openrouter": None}
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = {"vllm": None, "openrouter": None}
if 'generate_code_trigger' not in st.session_state:
    st.session_state.generate_code_trigger = False
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = None

with st.sidebar:
    st.title("Configuration")

    # Code Generation section
    st.write("### Code Generation")
    code_prompt = st.text_area(
        "Code Generation Prompt",
        placeholder="Enter your code generation request here...",
        help="Describe what code you want to generate",
        height=150
    )

    if st.button("Generate Code"):
        logger.info("User clicked Generate Code button")
        if not code_prompt:
            logger.warning("Code generation attempted without prompt")
            st.error("Please enter a code generation prompt!")
        else:
            logger.info(f"Starting code generation with prompt: {code_prompt[:100]}...")
            st.session_state.current_prompt = code_prompt
            st.session_state.generate_code_trigger = True
            st.rerun()

    st.write("---")

    st.session_state.reference_code = st.text_area(
        "Reference Code (Optional)",
        help="Enter reference/ground truth code to compare against",
        height=200
    )

    # Evaluation section
    st.write("### Evaluation")
    if st.button("Evaluate Generated Code"):
        logger.info("User requested code evaluation")
        logger.info(f"  vLLM code available: {bool(st.session_state.last_generated_code['vllm'])}")
        logger.info(f"  OpenRouter code available: {bool(st.session_state.last_generated_code['openrouter'])}")

        if st.session_state.last_generated_code["vllm"] and st.session_state.last_generated_code["openrouter"]:
            logger.info("Starting code evaluation for both models")
            with st.spinner("Evaluating code..."):
                logger.info("Evaluating vLLM generated code...")
                st.session_state.evaluation_results["vllm"] = evaluate_code(
                    st.session_state.last_generated_code["vllm"],
                    st.session_state.reference_code if st.session_state.reference_code else None
                )
                logger.info("Evaluating OpenRouter generated code...")
                st.session_state.evaluation_results["openrouter"] = evaluate_code(
                    st.session_state.last_generated_code["openrouter"],
                    st.session_state.reference_code if st.session_state.reference_code else None
                )
            logger.info("Code evaluation completed successfully")
            st.success("Evaluation complete!")
        else:
            logger.warning("Evaluation attempted but code not available from both models")
            st.error("Please generate code from both models first")

async def handle_chat_input(prompt: str):
    logger.info(f"Handling chat input: {prompt[:100]}...")
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    logger.info("Getting parallel responses from both models...")
    # Get streaming responses from both models
    with st.chat_message("assistant"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("##### gpt-oss-120b (vLLM)")
            vllm_container = st.empty()
            vllm_container = vllm_container.code("", language="python")
        with col2:
            st.write("##### gpt-oss-120b (OpenRouter)")
            openrouter_container = st.empty()
            openrouter_container = openrouter_container.code("", language="python")

        vllm_gen, openrouter_gen = await get_parallel_responses(prompt)

        async def process_vllm_stream(container):
            logger.info("Processing vLLM stream...")
            response_text = ""
            async for chunk in vllm_gen:
                response_text += chunk
                cleaned_text = response_text.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip()
                container.code(cleaned_text, language="python")
            logger.info(f"vLLM stream complete. Total length: {len(cleaned_text)} chars")
            return cleaned_text

        async def process_openrouter_stream(container):
            logger.info("Processing OpenRouter stream...")
            response_text = ""
            async for chunk in openrouter_gen:
                response_text += chunk
                cleaned_text = response_text.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip()
                container.code(cleaned_text, language="python")
            logger.info(f"OpenRouter stream complete. Total length: {len(cleaned_text)} chars")
            return cleaned_text

        # Run both streams concurrently
        logger.info("Running both streams concurrently...")
        final_vllm_response, final_openrouter_response = await asyncio.gather(
            process_vllm_stream(vllm_container),
            process_openrouter_stream(openrouter_container)
        )

        logger.info("Both streams completed successfully")
        message = {
            "role": "assistant",
            "content": "",
            "vllm_response": final_vllm_response,
            "openrouter_response": final_openrouter_response
        }
        st.session_state.chat_history.append(message)
        st.session_state.last_generated_code["vllm"] = final_vllm_response
        st.session_state.last_generated_code["openrouter"] = final_openrouter_response
        logger.info("Chat input handling complete. Code saved to session state.")

# Main interface
st.title("gpt-oss-120b: vLLM vs OpenRouter Inference Comparison")

# Handle code generation trigger
if st.session_state.generate_code_trigger and st.session_state.current_prompt:
    logger.info("Processing code generation trigger")
    st.session_state.generate_code_trigger = False
    asyncio.run(handle_chat_input(st.session_state.current_prompt))
    st.session_state.current_prompt = None

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
    if message["role"] == "assistant":
        col1, col2 = st.columns(2)
        with col1:
            st.write("##### gpt-oss-120b (vLLM)")
            st.code(message["vllm_response"], language="python")
        with col2:
            st.write("##### gpt-oss-120b (OpenRouter)")
            st.code(message["openrouter_response"], language="python")

# Inline chat input in the main interface has been disabled to avoid duplicate triggers.

# Display evaluation results
if st.session_state.evaluation_results["vllm"] and st.session_state.evaluation_results["openrouter"]:
    st.write("---")
    st.header("Evaluation results generated with GPT-4o using DeepEval")

    plot_data = pd.DataFrame({
        'Metric': ["Correctness", "Readability", "Best Practices", "Overall Score"],
        'vLLM': [
            st.session_state.evaluation_results['vllm']['detailed_metrics']['correctness']['score'],
            st.session_state.evaluation_results['vllm']['detailed_metrics']['readability']['score'],
            st.session_state.evaluation_results['vllm']['detailed_metrics']['best_practices']['score'],
            st.session_state.evaluation_results['vllm']['overall_score']
        ],
        'OpenRouter': [
            st.session_state.evaluation_results['openrouter']['detailed_metrics']['correctness']['score'],
            st.session_state.evaluation_results['openrouter']['detailed_metrics']['readability']['score'],
            st.session_state.evaluation_results['openrouter']['detailed_metrics']['best_practices']['score'],
            st.session_state.evaluation_results['openrouter']['overall_score']
        ]
    })
    
    fig = px.bar(
        plot_data.melt('Metric', var_name='Model', value_name='Score'),
        x='Metric',
        y='Score',
        color='Model',
        barmode='group',  
        title='Model Performance Comparison',
        template='plotly_dark',  
        color_discrete_sequence=['#00CED1', '#FF69B4'] 
    )
    
    fig.update_layout(
        xaxis_title="Evaluation Metrics",
        yaxis_title="Score",
        legend_title="Models",
        plot_bgcolor='rgba(32, 32, 32, 1)',  
        paper_bgcolor='rgba(32, 32, 32, 1)',  
        bargap=0.2,  
        bargroupgap=0.1,  
        font=dict(color='#E0E0E0'),  
        title_font=dict(color='#E0E0E0'),  
        showlegend=True,
        legend=dict(
            bgcolor='rgba(32, 32, 32, 0.8)',
            bordercolor='rgba(255, 255, 255, 0.3)',
            borderwidth=1
        )
    )
    
    fig.update_xaxes(
        gridcolor='rgba(128, 128, 128, 0.2)',
        zerolinecolor='rgba(128, 128, 128, 0.2)'
    )
    fig.update_yaxes(
        gridcolor='rgba(128, 128, 128, 0.2)',
        zerolinecolor='rgba(128, 128, 128, 0.2)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### gpt-oss-120b (vLLM) detailed metrics")
    
    vllm_data = []
    for metric in ["correctness", "readability", "best_practices"]:
        row = {
            "Metric": metric.title(),
            "Score": f"{st.session_state.evaluation_results['vllm']['detailed_metrics'][metric]['score']:.2f}",
            "Reasoning": st.session_state.evaluation_results['vllm']['detailed_metrics'][metric]['reason']
        }
        vllm_data.append(row)
    
    vllm_data.append({
        "Metric": "Overall Score",
        "Score": f"{st.session_state.evaluation_results['vllm']['overall_score']:.2f}",
        "Reasoning": "Final weighted average"
    })
    
    # Display vLLM table
    vllm_df = pd.DataFrame(vllm_data)
    st.dataframe(
        vllm_df,
        column_config={
            "Metric": st.column_config.TextColumn("Metric", width="small"),
            "Score": st.column_config.TextColumn("Score", width="small"),
            "Reasoning": st.column_config.TextColumn("Reasoning", width="large")
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.write("### gpt-oss-120b (OpenRouter) detailed metrics")
    
    openrouter_data = []
    for metric in ["correctness", "readability", "best_practices"]:
        row = {
            "Metric": metric.title(),
            "Score": f"{st.session_state.evaluation_results['openrouter']['detailed_metrics'][metric]['score']:.2f}",
            "Reasoning": st.session_state.evaluation_results['openrouter']['detailed_metrics'][metric]['reason']
        }
        openrouter_data.append(row)
    
    openrouter_data.append({
        "Metric": "Overall Score",
        "Score": f"{st.session_state.evaluation_results['openrouter']['overall_score']:.2f}",
        "Reasoning": "Final weighted average"
    })
    
    # Display OpenRouter table
    openrouter_df = pd.DataFrame(openrouter_data)
    st.dataframe(
        openrouter_df,
        column_config={
            "Metric": st.column_config.TextColumn("Metric", width="small"),
            "Score": st.column_config.TextColumn("Score", width="small"),
            "Reasoning": st.column_config.TextColumn("Reasoning", width="large")
        },
        hide_index=True,
        use_container_width=True
    ) 