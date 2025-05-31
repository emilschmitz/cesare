#!/usr/bin/env python3
"""
Test script to verify LLM provider integration
"""

from dotenv import load_dotenv
from openai import OpenAI
from cesare.utils.config import load_api_config


def test_llm_integration():
    """Test the LLM provider integration"""
    load_dotenv(".env")

    try:
        # Load API configuration
        config = load_api_config()
        print(f"✅ Using provider: {config['provider']}")
        print(f"✅ Base URL: {config['base_url'] or 'Default (OpenAI)'}")

        # Initialize client
        client_kwargs = {"api_key": config["api_key"]}
        if config["base_url"]:
            client_kwargs["base_url"] = config["base_url"]

        client = OpenAI(**client_kwargs)
        print("✅ OpenAI client initialized successfully")

        # Test listing models
        print("\n📋 Available models:")
        models = client.models.list()
        model_list = [model.id for model in models.data]

        if model_list:
            for model in model_list[:5]:  # Show first 5 models
                print(f"  - {model}")
            if len(model_list) > 5:
                print(f"  ... and {len(model_list) - 5} more models")
        else:
            print("  No models found or error occurred")
            return False

        # Test a simple chat completion
        print("\n🤖 Testing chat completion...")
        messages = [
            {
                "role": "user",
                "content": "Say 'Hello from the API!' in exactly those words.",
            }
        ]

        # Choose test model based on provider
        if config["provider"] == "lambda":
            test_model = "deepseek-v3-0324"  # Use the DeepSeek V3 model
        elif config["provider"] == "together":
            test_model = "meta-llama/Llama-3.2-3B-Instruct-Turbo"  # Use a small Together AI model
        elif config["provider"] == "openai":
            test_model = "gpt-3.5-turbo"  # Use a basic OpenAI model
        else:
            test_model = model_list[0] if model_list else "gpt-3.5-turbo"

        if test_model in model_list:
            response = client.chat.completions.create(
                model=test_model, messages=messages, temperature=0.1
            )
            print(f"✅ Response: {response.choices[0].message.content}")
        else:
            print(f"❌ Test model {test_model} not available")
            print(f"Available models: {model_list[:3]}...")
            return False

        print(
            f"\n🎉 {config['provider'].title()} integration test completed successfully!"
        )
        return True

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease add one of the following API keys to your .env file:")
        print("  LAMBDA_API_KEY=your_lambda_labs_api_key")
        print("  TOGETHER_API_KEY=your_together_api_key")
        print("  OPENAI_API_KEY=your_openai_api_key")
        print("  ANTHROPIC_API_KEY=your_anthropic_api_key")
        return False
    except Exception as e:
        print(f"❌ Error testing LLM integration: {e}")
        return False


if __name__ == "__main__":
    test_llm_integration()
