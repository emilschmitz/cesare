from typing import Dict, List
import os
import yaml
from langchain_together import ChatTogether
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.messages import HumanMessage
from langsmith import Client, traceable


class Agent:
    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek-ai/DeepSeek-V3",
        langsmith_api_key: str = None,
        project_name: str = "cesare-agent",
        prompts_file: str = "cesare/prompts.yaml",
    ):
        """
        Initialize the Actor with API keys.

        Args:
            api_key (str): API key for LLM access
            model_name (str): Name of the model to use
            langsmith_api_key (str, optional): API key for Langsmith
            project_name (str, optional): Name of the Langsmith project
            prompts_file (str, optional): Path to the prompts YAML file
        """
        self.api_key = api_key
        self.model_name = model_name

        # Load prompts from YAML file
        with open(prompts_file, 'r') as file:
            self.prompts = yaml.safe_load(file)

        # Initialize LangSmith for tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

        # Initialize the LangChain model
        self.model = ChatTogether(
            model=self.model_name, together_api_key=self.api_key, temperature=1.0
        )

        # Langsmith setup
        self.project_name = project_name
        self.langsmith_client = (
            Client(api_key=langsmith_api_key) if langsmith_api_key else None
        )

    @traceable(run_type="llm", name="generate_first_instruction")
    def generate_first_instruction(self, start_prompt: str) -> str:
        """
        Generate the first instruction based on the start prompt.

        Args:
            start_prompt (str): The initial prompt to start the simulation

        Returns:
            str: The generated first instruction
        """
        try:
            # Format the prompt
            formatted_prompt = self.prompts['first_instruction_prompt'].format(prompt=start_prompt)
            
            # Create and run a simple chain
            chain = (
                RunnablePassthrough()
                | (lambda x: [HumanMessage(content=x["prompt"])])
                | self.model
                | StrOutputParser()
            )

            # Execute the chain with tracing
            response = chain.invoke(
                {"prompt": formatted_prompt}, {"run_name": "first_instruction"}
            )
            return response
        except Exception as e:
            print(f"Error generating first instruction: {e}")
            return "Error: Could not generate first instruction"

    @traceable(run_type="llm", name="generate_instruction")
    def generate_instruction(self, history: List[Dict]) -> str:
        """
        Generate the next order using the API key for LLM access.

        Args:
            history (List[Dict]): The history of the simulation

        Returns:
            str: The generated order
        """
        context = self._get_context(history)
        try:
            # Format the prompt with context
            formatted_prompt = self.prompts['instruction_prompt'].format(context=context)
            
            # Create and run a simple chain
            chain = (
                RunnablePassthrough()
                | (lambda x: [HumanMessage(content=x["prompt"])])
                | self.model
                | StrOutputParser()
            )

            # Execute the chain with tracing
            response = chain.invoke(
                {"prompt": formatted_prompt}, {"run_name": "agent_instruction"}
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
        return "\n".join(
            [f"{entry['type']}: {entry['content']}" for entry in history]
        )
