"""Simple LLM factory for choosing between Gemini and Custom LLM."""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from custom_llm import CustomLLM


def get_llm(model: str = "gemini-2.5-flash"):
    """
    Get an LLM instance based on environment configuration.
    
    Args:
        model: The model name to use (for Gemini)
        
    Returns:
        LLM instance (either ChatGoogleGenerativeAI or CustomLLM)
        
    Environment Variables:
        - USE_CUSTOM_LLM: Set to "true" to use custom LLM instead of Gemini
        - CUSTOM_LLM_ENDPOINT: Required for custom LLM
        - CUSTOM_LLM_API_KEY: Optional API key for custom LLM
    """
    use_custom = os.getenv("USE_CUSTOM_LLM", "false").lower() == "true"
    
    if use_custom:
        return CustomLLM(model=model)
    else:
        return ChatGoogleGenerativeAI(model=model)