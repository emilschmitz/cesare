from typing import Dict, List
from openai import OpenAI
from utils.config import load_api_config


class Describer:
    def __init__(self, api_key: str = None, model_name: str = "deepseek-v3-0324"):
        """
        Initialize the Describer with an API key and model name.

        Args:
            api_key (str, optional): API key for LLM access. If None, loads from config.
            model_name (str): Name of the model to use
        """
        if api_key:
            self.api_key = api_key
            self.base_url = None  # Assume OpenAI if API key is provided directly
        else:
            config = load_api_config()
            self.api_key = config["api_key"]
            self.base_url = config["base_url"]
        
        self.model_name = model_name
        
        # Initialize OpenAI client (works with Lambda Labs too)
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self.client = OpenAI(**client_kwargs)

    def generate_description(self, history: List[Dict]) -> str:
        """
        Generate a description based on the history using the API key for LLM access.

        Args:
            history (List[Dict]): The history of the simulation

        Returns:
            str: The generated description
        """
        prompt = self._create_prompt(history)
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=1.0
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating description: {e}")
            return "Error: Could not generate description"

    def _create_prompt(self, history: List[Dict]) -> str:
        context = "\n".join(
            [f"{entry['type']}: {entry['content']}" for entry in history]
        )
        return f"""Given the following conversation history, provide a concise description 
        of the current situation that captures all relevant details for someone to predict 
        how the environment might respond to the actions taken as a result of the latest order:

        {context}
        
        Description:"""
