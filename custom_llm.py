"""Custom LLM wrapper - drop-in replacement for Gemini."""

import os
import requests
import json
from typing import Any, List, Optional, Iterator, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun


class CustomLLM(BaseChatModel):
    """
    Custom LLM wrapper for enterprise deployment.
    
    This is designed as a drop-in replacement for ChatGoogleGenerativeAI.
    Configure using environment variables:
    
    - CUSTOM_LLM_ENDPOINT: Your enterprise API endpoint
    - CUSTOM_LLM_API_KEY: API key for authentication (optional)
    - CUSTOM_LLM_MODEL: Model name (default: "custom-enterprise-llm")
    - CUSTOM_LLM_TIMEOUT: Request timeout in seconds (default: 60)
    """
    
    def __init__(self, model: str = None, **kwargs):
        """Initialize the custom LLM."""
        super().__init__(**kwargs)
        
        # Get configuration from environment variables
        self.api_endpoint = os.getenv("CUSTOM_LLM_ENDPOINT")
        self.api_key = os.getenv("CUSTOM_LLM_API_KEY")
        self.model_name = model or os.getenv("CUSTOM_LLM_MODEL", "custom-enterprise-llm")
        self.timeout = int(os.getenv("CUSTOM_LLM_TIMEOUT", "60"))
        
        if not self.api_endpoint:
            raise ValueError(
                "CUSTOM_LLM_ENDPOINT environment variable is required for CustomLLM. "
                "Set it to your enterprise API endpoint URL."
            )
    
    @property
    def _llm_type(self) -> str:
        """Return the type of language model."""
        return "custom-enterprise"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from messages."""
        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)
        
        # Call the enterprise API
        response_text = self._call_api(prompt, stop, **kwargs)
        
        # Wrap response in ChatResult
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate - for now, just call sync version."""
        # In production, you'd want to use an async HTTP client like aiohttp
        return self._generate(messages, stop, run_manager, **kwargs)
    
    def _call_api(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Call the enterprise LLM API."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "prompt": prompt,
            "model": self.model_name,
            "stop": stop,
            **kwargs
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            # Adjust this based on your enterprise API response format
            return result.get("text", result.get("response", ""))
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error calling enterprise LLM API: {str(e)}")
    
    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert messages to a single prompt string."""
        prompt_parts = []
        for message in messages:
            if isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            elif isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            else:
                prompt_parts.append(f"{message.__class__.__name__}: {message.content}")
        
        return "\n\n".join(prompt_parts)
    
    def bind_tools(self, tools, **kwargs):
        """
        Bind tools to the model.
        
        Note: Tool binding is not implemented for custom enterprise LLMs yet.
        This will raise NotImplementedError to maintain compatibility.
        """
        raise NotImplementedError(
            "Tool binding not yet implemented for custom enterprise LLM. "
            "Use the Gemini provider for agents that require tool support."
        )