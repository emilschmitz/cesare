import os
from dotenv import load_dotenv


def load_api_config():
    """Load API configuration for LLM providers"""
    load_dotenv(".env")
    
    # Try different API providers in order of preference
    api_key = None
    base_url = None
    provider = None
    
    # Lambda Labs
    if os.getenv("LAMBDA_API_KEY"):
        api_key = os.getenv("LAMBDA_API_KEY")
        base_url = "https://api.lambda.ai/v1"
        provider = "lambda"
    # Together AI
    elif os.getenv("TOGETHER_API_KEY"):
        api_key = os.getenv("TOGETHER_API_KEY")
        base_url = "https://api.together.xyz/v1"
        provider = "together"
    # OpenAI
    elif os.getenv("OPENAI_API_KEY"):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = None  # Use default OpenAI base URL
        provider = "openai"
    # Anthropic (for future use)
    elif os.getenv("ANTHROPIC_API_KEY"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        base_url = "https://api.anthropic.com/v1"
        provider = "anthropic"
    else:
        raise ValueError("No API key found. Please set LAMBDA_API_KEY, TOGETHER_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env")
    
    return {
        "api_key": api_key,
        "base_url": base_url,
        "provider": provider
    }


def load_api_key():
    """Backward compatibility function"""
    config = load_api_config()
    return config["api_key"]
