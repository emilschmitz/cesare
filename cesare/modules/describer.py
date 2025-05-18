from typing import Dict, List
from together import Together


class Describer:
    def __init__(self, api_key: str, model_name: str):
        """
        Initialize the Describer with an API key and model name.

        Args:
            api_key (str): API key for LLM access
            model_name (str): Name of the model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.client = Together(api_key=api_key)

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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
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
