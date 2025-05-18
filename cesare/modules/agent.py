from typing import Dict, List
import os
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
    ):
        """
        Initialize the Actor with API keys.

        Args:
            api_key (str): API key for LLM access
            model_name (str): Name of the model to use
            langsmith_api_key (str, optional): API key for Langsmith
            project_name (str, optional): Name of the Langsmith project
        """
        self.api_key = api_key
        self.model_name = model_name

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
            # Create and run a simple chain
            chain = (
                RunnablePassthrough()
                | (lambda x: [HumanMessage(content=x["prompt"])])
                | self.model
                | StrOutputParser()
            )

            # Execute the chain with tracing
            response = chain.invoke(
                {"prompt": start_prompt}, {"run_name": "first_instruction"}
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
        prompt = self._get_prompt(history)
        try:
            # Create and run a simple chain
            chain = (
                RunnablePassthrough()
                | (lambda x: [HumanMessage(content=x["prompt"])])
                | self.model
                | StrOutputParser()
            )

            # Execute the chain with tracing
            response = chain.invoke(
                {"prompt": prompt}, {"run_name": "agent_instruction"}
            )
            return response
        except Exception as e:
            print(f"Error generating instruction: {e}")
            return "Error: Could not generate instruction"

    def _get_prompt(self, history: List[Dict]) -> str:
        context = "\n".join(
            [f"{entry['type']}: {entry['content']}" for entry in history]
        )
        return f"""Based on the following conversation history, generate the next instruction. 
        Always start with a timestamp in in ISO 8601 format. 
        If information is unclear or uncomplete, you may request more.
        Be concise and clear. Maximum 400 characters:

        {context}
        
        Generate your next instruction:"""
