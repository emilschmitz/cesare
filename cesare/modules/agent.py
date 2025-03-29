from typing import Dict, List
from together import Together

class Agent:
    def __init__(self, api_key: str, model_name: str = "deepseek-ai/DeepSeek-V3"):
        """
        Initialize the Actor with an API key.
        
        Args:
            api_key (str): API key for LLM access
        """
        self.api_key = api_key
        self.model_name = "deepseek-ai/DeepSeek-V3"
        self.client = Together(api_key=api_key)

    def generate_instruction(self, history: List[Dict]) -> str:
        """
        Generate the next order using the API key for LLM access.
        
        Args:
            history (List[Dict]): The history of the simulation
            
        Returns:
            str: The generated order
        """
        prompt = self._get_prompt(history)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating order: {e}")
            return "Error: Could not generate order"

    def _get_prompt(self, history: List[Dict]) -> str:
        context = "\n".join([
            f"{entry['type']}: {entry['content']}" 
            for entry in history
        ])
        return f"""Based on the following conversation history, generate the next instruction. 
        Always start with a timestamp in in ISO 8601 format. 
        If information is unclear or uncomplete, you may request more.
        Be concise and clear. Maximum 400 characters:

        {context}
        
        Generate your next instruction:"""
