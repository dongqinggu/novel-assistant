"""LLM Abstraction Layer

Provides unified interface for different LLM providers.
Supports: OpenAI, Anthropic, Alibaba Qwen, DeepSeek
All providers support custom base_url for proxy/self-hosted services.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM Configuration"""
    provider: str  # openai, anthropic, qwen, deepseek
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None  # Custom base URL for API endpoint
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class BaseLLM(ABC):
    """Base class for LLM implementations"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv(f"{config.provider.upper()}_API_KEY")
        if not self.api_key:
            raise ValueError(f"API key not found for {config.provider}")
        
        # Load base_url from config or environment
        self.base_url = config.base_url or os.getenv(f"{config.provider.upper()}_BASE_URL")
    
    @abstractmethod
    def call(self, prompt: str, **kwargs) -> str:
        """Call the LLM with a prompt
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments
            
        Returns:
            LLM response
        """
        pass
    
    @abstractmethod
    def call_with_system(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call the LLM with system and user prompts
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            **kwargs: Additional arguments
            
        Returns:
            LLM response
        """
        pass


class OpenAILLM(BaseLLM):
    """OpenAI GPT implementation with custom base_url support"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai library not installed. Install with: pip install openai")
        
        # Create OpenAI client with optional custom base_url
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = OpenAI(**client_kwargs)
    
    def call(self, prompt: str, **kwargs) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.config.model or "gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **kwargs
        )
        return response.choices[0].message.content
    
    def call_with_system(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call OpenAI API with system prompt"""
        response = self.client.chat.completions.create(
            model=self.config.model or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **kwargs
        )
        return response.choices[0].message.content


class AnthropicLLM(BaseLLM):
    """Anthropic Claude implementation with custom base_url support"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic library not installed. Install with: pip install anthropic")
        
        # Create Anthropic client with optional custom base_url
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = Anthropic(**client_kwargs)
    
    def call(self, prompt: str, **kwargs) -> str:
        """Call Anthropic API"""
        message = self.client.messages.create(
            model=self.config.model or "claude-3-sonnet-20240229",
            max_tokens=self.config.max_tokens or 1024,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return message.content[0].text
    
    def call_with_system(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call Anthropic API with system prompt"""
        message = self.client.messages.create(
            model=self.config.model or "claude-3-sonnet-20240229",
            max_tokens=self.config.max_tokens or 1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            **kwargs
        )
        return message.content[0].text


class QwenLLM(BaseLLM):
    """Alibaba Qwen implementation with custom base_url support"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from dashscope import Generation
        except ImportError:
            raise ImportError("dashscope library not installed. Install with: pip install dashscope")
        
        self.Generation = Generation
        # Note: DashScope doesn't use base_url by default, but we store it for compatibility
        self._setup_custom_endpoint()
    
    def _setup_custom_endpoint(self):
        """Setup custom endpoint if provided"""
        if self.base_url:
            # For Qwen, custom base_url would need additional configuration
            # This is a placeholder for future implementation
            pass
    
    def call(self, prompt: str, **kwargs) -> str:
        """Call Qwen API"""
        response = self.Generation.call(
            api_key=self.api_key,
            model=self.config.model or "qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **kwargs
        )
        if response.status_code == 200:
            return response.output.text
        else:
            raise RuntimeError(f"Qwen API error: {response.message}")
    
    def call_with_system(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call Qwen API with system prompt"""
        response = self.Generation.call(
            api_key=self.api_key,
            model=self.config.model or "qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **kwargs
        )
        if response.status_code == 200:
            return response.output.text
        else:
            raise RuntimeError(f"Qwen API error: {response.message}")


class DeepSeekLLM(BaseLLM):
    """DeepSeek implementation (OpenAI-compatible API)"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai library not installed. Install with: pip install openai")
        
        # Default to DeepSeek API if no custom base_url provided
        base_url = self.base_url or "https://api.deepseek.com/beta"
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
    
    def call(self, prompt: str, **kwargs) -> str:
        """Call DeepSeek API"""
        response = self.client.chat.completions.create(
            model=self.config.model or "deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **kwargs
        )
        return response.choices[0].message.content
    
    def call_with_system(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Call DeepSeek API with system prompt"""
        response = self.client.chat.completions.create(
            model=self.config.model or "deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **kwargs
        )
        return response.choices[0].message.content


class LLMFactory:
    """Factory for creating LLM instances"""
    
    _providers = {
        "openai": OpenAILLM,
        "anthropic": AnthropicLLM,
        "qwen": QwenLLM,
        "deepseek": DeepSeekLLM,
    }
    
    @classmethod
    def create(cls, provider: str, **kwargs) -> BaseLLM:
        """Create an LLM instance
        
        Args:
            provider: LLM provider name (openai, anthropic, qwen, deepseek)
            **kwargs: Configuration arguments
                - api_key: API key
                - model: Model name
                - base_url: Custom API endpoint URL
                - temperature: Temperature (0.0-2.0)
                - max_tokens: Maximum tokens in response
            
        Returns:
            LLM instance
            
        Raises:
            ValueError: If provider not supported
            
        Example:
            # Standard OpenAI
            llm = LLMFactory.create("openai", api_key="sk-xxx", model="gpt-4")
            
            # OpenAI with custom base_url (e.g., Azure, local proxy)
            llm = LLMFactory.create(
                "openai",
                api_key="sk-xxx",
                base_url="https://api.openai.azure.com/v1",
                model="gpt-4"
            )
            
            # DeepSeek with custom endpoint
            llm = LLMFactory.create(
                "deepseek",
                api_key="sk-xxx",
                base_url="http://localhost:8000/v1",
                model="deepseek-chat"
            )
        """
        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(cls._providers.keys())}")
        
        config = LLMConfig(provider=provider, **kwargs)
        return cls._providers[provider](config)
    
    @classmethod
    def from_env(cls, provider: Optional[str] = None) -> BaseLLM:
        """Create LLM from environment variables
        
        Args:
            provider: Provider name (if None, uses NOVEL_LLM_PROVIDER env var)
            
        Returns:
            LLM instance
            
        Environment Variables:
            NOVEL_LLM_PROVIDER: LLM provider (openai, anthropic, qwen, deepseek)
            OPENAI_API_KEY: API key for OpenAI
            OPENAI_BASE_URL: Custom base URL for OpenAI (optional)
            ANTHROPIC_API_KEY: API key for Anthropic
            ANTHROPIC_BASE_URL: Custom base URL for Anthropic (optional)
            QWEN_API_KEY: API key for Qwen
            QWEN_BASE_URL: Custom base URL for Qwen (optional)
            DEEPSEEK_API_KEY: API key for DeepSeek
            DEEPSEEK_BASE_URL: Custom base URL for DeepSeek (optional)
        """
        if provider is None:
            provider = os.getenv("NOVEL_LLM_PROVIDER", "openai")
        
        return cls.create(provider)
