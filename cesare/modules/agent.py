from typing import Dict, List
import os
import yaml
from langchain_openai import ChatOpenAI
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.messages import HumanMessage
from langsmith import Client, traceable
from utils.config import load_api_config


class Agent:
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "deepseek-v3-0324",
        langsmith_api_key: str = None,
        project_name: str = "cesare-agent",
        prompts_file: str = "cesare/prompts-simulation.yaml",
    ):
        """
        Initialize the Actor with API keys.

        Args:
            api_key (str, optional): API key for LLM access. If None, loads from config.
            model_name (str): Name of the model to use
            langsmith_api_key (str, optional): API key for Langsmith
            project_name (str, optional): Name of the Langsmith project
            prompts_file (str, optional): Path to the prompts YAML file
        """
        if api_key:
            self.api_key = api_key
            self.base_url = None  # Assume OpenAI if API key is provided directly
        else:
            config = load_api_config()
            self.api_key = config["api_key"]
            self.base_url = config["base_url"]
        
        self.model_name = model_name

        # Load prompts from YAML file
        with open(prompts_file, "r") as file:
            self.prompts = yaml.safe_load(file)

        # Initialize LangSmith for tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

        # Initialize the LangChain model
        model_kwargs = {
            "model": self.model_name, 
            "api_key": self.api_key, 
            "temperature": 1.0
        }
        if self.base_url:
            model_kwargs["base_url"] = self.base_url
        
        self.model = ChatOpenAI(**model_kwargs)

        # Langsmith setup
        self.project_name = project_name
        self.langsmith_client = (
            Client(api_key=langsmith_api_key) if langsmith_api_key else None
        )

    @traceable(run_type="llm", name="generate_instruction")
    def generate_instruction(self, history: List[Dict] = None) -> str:
        """
        Generate the next instruction based on history.
        If history is None, this is the first instruction.

        Args:
            history (List[Dict], optional): The history of the simulation.
                If None, generates the first instruction.

        Returns:
            str: The generated instruction
        """
        try:
            # If history is None or empty, this is the first instruction
            if not history:
                # Use start prompt for the first instruction
                formatted_prompt = self.prompts["start_prompt"]
                run_name = "first_instruction"
            else:
                # Format context from history for subsequent instructions
                context = self._get_context(history)
                formatted_prompt = self.prompts["instruction_prompt"].format(
                    context=context
                )
                run_name = "agent_instruction"

            # Create and run a simple chain
            chain = (
                RunnablePassthrough()
                | (lambda x: [HumanMessage(content=x["prompt"])])
                | self.model
                | StrOutputParser()
            )

            # Execute the chain with tracing
            response = chain.invoke(
                {"prompt": formatted_prompt}, {"run_name": run_name}
            )
            return response
        except Exception as e:
            print(f"Error generating instruction: {e}")
            return "Error: Could not generate instruction"

    def _get_context(self, history: List[Dict]) -> str:
        """
        Format conversation history into context string.

        Args:
            history (List[Dict]): The history of the simulation

        Returns:
            str: Formatted context string
        """
        return "\n".join([f"{entry['type']}: {entry['content']}" for entry in history])
