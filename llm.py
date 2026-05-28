"""LLM Abstraction Layer

Provides unified interface for different LLM providers.
Supports: OpenAI, Anthropic, Alibaba Qwen, DeepSeek
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
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class BaseLLM(ABC):
    """Base class for LLM implementations"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv(f"{config.provider.upper()}_API_KEY")
        if not self.api_key:
            raise ValueError(f"API key not found for {config.provider}")
    
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
    """OpenAI GPT implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai library not installed. Install with: pip install openai")
    
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
    """Anthropic Claude implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic library not installed. Install with: pip install anthropic")
    
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


class LLMFactory:
    """Factory for creating LLM instances"""
    
    _providers = {
        "openai": OpenAILLM,
        "anthropic": AnthropicLLM,
        # Can add more providers here: qwen, deepseek, etc.
    }
    
    @classmethod
    def create(cls, provider: str, **kwargs) -> BaseLLM:
        """Create an LLM instance
        
        Args:
            provider: LLM provider name
            **kwargs: Configuration arguments
            
        Returns:
            LLM instance
            
        Raises:
            ValueError: If provider not supported
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
        """
        if provider is None:
            provider = os.getenv("NOVEL_LLM_PROVIDER", "openai")
        
        return cls.create(provider)
