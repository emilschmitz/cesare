import os
from dotenv import load_dotenv


def load_api_config(provider=None):
    """Load API configuration for LLM providers
    
    Args:
        provider (str, optional): Specific provider to use ('together', 'openai', 'lambda', 'anthropic').
                                 If None, auto-detects based on available API keys.
    """
    load_dotenv(".env")
    
    # Provider-specific configurations
    provider_configs = {
        "together": {
            "env_key": "TOGETHER_API_KEY",
            "base_url": "https://api.together.xyz/v1"
        },
        "openai": {
            "env_key": "OPENAI_API_KEY",
            "base_url": None  # Use default OpenAI base URL
        },
        "lambda": {
            "env_key": "LAMBDA_API_KEY",
            "base_url": "https://api.lambda.ai/v1"
        },
        "anthropic": {
            "env_key": "ANTHROPIC_API_KEY",
            "base_url": "https://api.anthropic.com/v1"
        }
    }
    
    if provider:
        # Use specific provider
        if provider not in provider_configs:
            raise ValueError(f"Unknown provider: {provider}. Supported providers: {list(provider_configs.keys())}")
        
        config = provider_configs[provider]
        api_key = os.getenv(config["env_key"])
        
        if not api_key:
            raise ValueError(f"API key not found for provider '{provider}'. Please set {config['env_key']} in .env")
        
        return {
            "api_key": api_key,
            "base_url": config["base_url"],
            "provider": provider
        }
    
    # Auto-detect provider based on available API keys (legacy behavior)
    for provider_name, config in provider_configs.items():
        api_key = os.getenv(config["env_key"])
        if api_key:
            return {
                "api_key": api_key,
                "base_url": config["base_url"],
                "provider": provider_name
            }
    
    raise ValueError("No API key found. Please set one of: " + 
                    ", ".join([config["env_key"] for config in provider_configs.values()]) + " in .env")


def load_api_key():
    """Backward compatibility function"""
    config = load_api_config()
    return config["api_key"]
