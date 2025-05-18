from typing import Dict, List
from utils.config import load_api_key
from modules.agent import Agent
from modules.environment import Environment
import yaml


class CESARE:
    def __init__(self, api_key: str, config: dict, prompts_file: str = "cesare/prompts.yaml"):
        self._api_key = api_key

        self.config = config
        models = config["models"]
        
        # Load prompts
        with open(prompts_file, 'r') as file:
            self.prompts = yaml.safe_load(file)
            
        self.agent = Agent(api_key=self._api_key, model_name=models["agent"], prompts_file=prompts_file)
        self.environment = Environment(
            api_key=self._api_key, model_name=models["environment"], prompts_file=prompts_file
        )
        self.history: List[Dict] = []

    def add_to_history(self, entry_type: str, content: str):
        self.history.append({"type": entry_type, "content": content})

    def run_simulation(self, start_prompt: str | None = None):
        # Use the start prompt from YAML file if not provided
        if start_prompt is None:
            start_prompt = self.prompts["start_prompt"]
            
        self.add_to_history("start_prompt", start_prompt)
        instruction = self.agent.generate_first_instruction(start_prompt)

        max_steps = self.config["simulation"]["max_steps"]

        for step in range(max_steps):
            # Get order from ACTOR
            instruction = self.agent.generate_instruction(self.history)
            self.add_to_history("instruction", instruction)

            # Get response from ENVIRONMENT
            env_response = self.environment.generate_response(self.history)
            self.add_to_history("environment", env_response)

            print(f"Step {step + 1}:")
            print(f"Instruction: {instruction}")
            print(f"Environment: {env_response}\n")


if __name__ == "__main__":
    with open("config/deepseek-v3.yaml") as f:
        config = yaml.safe_load(f)

    api_key = load_api_key()

    simulator = CESARE(api_key, config, prompts_file="cesare/prompts.yaml")
    simulator.run_simulation()
