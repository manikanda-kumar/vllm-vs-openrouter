import os
import asyncio
import logging
from litellm import acompletion
from openai import AsyncOpenAI
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_model_response_async(model_name: str, prompt: str):
    logger.info(f"Starting code generation for model: {model_name}")

    user_prompt = f"""
    You are an expert code generator. Your task is to generate high-quality code based on the user's request.

    Instructions:
    1. Generate clean, well-structured code
    2. Use clear and consistent naming conventions
    3. Include clear, concise docstrings and comments explaining key functionality
    4. Follow best practices and coding standards
    5. Focus on maintainability and readability

    User query:
    {prompt}

    Output only the code implementation without explanations or additional text.
    """

    messages = [
        {"role": "user", "content": user_prompt}
    ]

    model_mapping = {
        "openrouter": "openai/gpt-oss-20b",
        "vllm-local": os.getenv("VLLM_MODEL_NAME", "openai/gpt-oss-20b")
    }

    try:
        if model_name == "vllm-local":
            base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
            api_key = os.getenv("VLLM_API_KEY", "EMPTY")
            model = model_mapping[model_name]

            logger.info(f"vLLM Configuration:")
            logger.info(f"  Base URL: {base_url}")
            logger.info(f"  Model: {model}")
            logger.info(f"  API Key: {'*' * len(api_key) if api_key else 'None'}")

            client = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key
            )
            logger.info(f"Sending request to vLLM endpoint...")
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,
                stream=True
            )
            logger.info(f"Receiving streaming response from vLLM...")
            chunk_count = 0
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    chunk_count += 1
                    yield chunk.choices[0].delta.content
            logger.info(f"vLLM response complete. Received {chunk_count} chunks")
        else:
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            model = model_mapping[model_name]

            logger.info(f"OpenRouter Configuration:")
            logger.info(f"  Model: {model}")
            logger.info(f"  API Key: {'*' * 10 if openrouter_key else 'None'}")

            logger.info(f"Sending request to OpenRouter...")
            response = await acompletion(
                model=model,
                messages=messages,
                api_key=openrouter_key,
                api_base="https://openrouter.ai/api/v1",
                max_tokens=2000,
                stream=True,
                custom_llm_provider="openrouter"
            )
            logger.info(f"Receiving streaming response from OpenRouter...")
            chunk_count = 0
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    chunk_count += 1
                    yield chunk.choices[0].delta.content
            logger.info(f"OpenRouter response complete. Received {chunk_count} chunks")

    except Exception as e:
        logger.error(f"Error in {model_name}: {str(e)}", exc_info=True)
        yield f"Error generating response: {str(e)}"

async def get_parallel_responses(prompt: str):
    logger.info("Starting parallel code generation from both models")
    vllm_gen = get_model_response_async("vllm-local", prompt)
    openrouter_gen = get_model_response_async("openrouter", prompt)

    return vllm_gen, openrouter_gen

def get_model_responses(prompt: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(get_parallel_responses(prompt)) 