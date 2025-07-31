import logging
from langchain_openai import ChatOpenAI

from config import Config
from rfiprocessor.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
config = Config()

# Model names from config
GEMINI_MODEL_NAME = config.LLM_MODEL_NAME # e.g., 'gemini model'
FAST_LLM_MODEL_NAME = config.FAST_LLM_MODEL_NAME  # e.g., 'gpt-4-turbo'
REASONING_LLM_MODEL_NAME = config.REASONING_LLM_MODEL_NAME  # e.g., 'o3'
ADVANCED_LLM_MODEL_NAME = config.ADVANCED_LLM_MODEL_NAME  # e.g., 'gpt-4o'

def get_gemini_llm():
    """Return either a Google Gemini chat model based on model name."""
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key=config.GOOGLE_API_KEY,
        temperature=0.1,
        max_retries=2
    )

def get_fast_llm():
    """
    Initializes a fast LLM for quick, lightweight tasks (e.g., simple queries, text generation).
    """
    llm = ChatOpenAI(
        model=FAST_LLM_MODEL_NAME,
        temperature=0.1,  # Low temperature for consistent, factual outputs
        openai_api_key=config.OPENAI_API_KEY,
        timeout=10,  # Short timeout for quick responses
        max_retries=2,
    )
    logger.info(f"Initialized Fast LLM Provider: {FAST_LLM_MODEL_NAME}")
    return llm

def get_reasoning_llm():
    """
    Initializes a reasoning LLM for tasks requiring logical reasoning or problem-solving.
    """
    llm = ChatOpenAI(
        model=REASONING_LLM_MODEL_NAME,
        openai_api_key=config.OPENAI_API_KEY,
        max_retries=2,
    )
    logger.info(f"Initialized Reasoning LLM Provider: {REASONING_LLM_MODEL_NAME}")
    return llm

def get_advanced_llm():
    """
    Initializes an advanced LLM for complex reasoning tasks (e.g., multi-step reasoning, advanced analysis).
    """
    llm = ChatOpenAI(
        model=ADVANCED_LLM_MODEL_NAME,
        temperature=0.5,  # Moderate temperature for complex reasoning tasks
        openai_api_key=config.OPENAI_API_KEY,
        max_tokens=None,  # No token limit for comprehensive outputs
        timeout=None,
        max_retries=3,  # Higher retries for robustness
    )
    logger.info(f"Initialized Advanced LLM Provider: {ADVANCED_LLM_MODEL_NAME}")
    return llm