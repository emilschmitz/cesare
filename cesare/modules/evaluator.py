from typing import Dict, List, Any
import os
import yaml
import json
import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.messages import HumanMessage
from langsmith import Client, traceable
from utils.config import load_api_config


class Evaluator:
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "deepseek-v3-0324",
        langsmith_api_key: str = None,
        project_name: str = "cesare-evaluator",
        evaluation_prompts_file: str = "cesare/prompts-evaluation.yaml",
        log_to_file: bool = True,
        log_path: str = "logs/evaluations/",
        provider: str = None,
    ):
        """
        Initialize the Evaluator.

        Args:
            api_key (str, optional): API key for LLM access. If None, loads from config.
            model_name (str): Name of the model to use
            langsmith_api_key (str, optional): API key for Langsmith
            project_name (str, optional): Name of the Langsmith project
            evaluation_prompts_file (str, optional): Path to the evaluation prompts YAML file
            log_to_file (bool, optional): Whether to log evaluations to a file
            log_path (str, optional): Path to save evaluation logs
            provider (str, optional): Provider to use ('together', 'openai', etc.)
        """
        if api_key:
            self.api_key = api_key
            self.base_url = None  # Assume OpenAI if API key is provided directly
        else:
            config = load_api_config(provider)
            self.api_key = config["api_key"]
            self.base_url = config["base_url"]
        
        self.model_name = model_name
        self.log_to_file = log_to_file
        self.log_path = log_path

        # Create log directory if it doesn't exist
        if self.log_to_file and not os.path.exists(self.log_path):
            os.makedirs(self.log_path, exist_ok=True)

        # Generate unique log filename based on timestamp
        self.log_filename = self._generate_log_filename()

        # Load prompts from YAML file
        with open(evaluation_prompts_file, "r") as file:
            self.prompts = yaml.safe_load(file)

        # Initialize LangSmith for tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

        # Initialize the LangChain model for evaluation
        model_kwargs = {
            "model": self.model_name, 
            "api_key": self.api_key, 
            "temperature": 0.0,
            "streaming": False
        }
        if self.base_url:
            model_kwargs["base_url"] = self.base_url
        
        self.model = ChatOpenAI(**model_kwargs)

        # Langsmith setup
        self.project_name = project_name
        self.langsmith_client = (
            Client(api_key=langsmith_api_key) if langsmith_api_key else None
        )

        # Initialize metrics tracking
        self.violation_metrics = {
            "killing": 0,
            "physical_harm": 0,
            "non_physical_harm": 0,
            "intending_harm": 0,
            "deception": 0,
            "manipulation": 0,
            "betrayal": 0,
            "stealing": 0,
            "trespassing": 0,
            "spying": 0,
            "vandalism": 0,
            "unfairness": 0,
            "other": 0,
        }

        # List to store all evaluations
        self.evaluations = []

    def _generate_log_filename(self) -> str:
        """Generate a unique log filename based on timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"evaluation_log_{timestamp}.json"

    def _get_run_id_from_callbacks(self):
        """Get the run ID from the current callbacks if available."""
        try:
            from langchain.callbacks import get_current_run_id

            return get_current_run_id()
        except (ImportError, AttributeError):
            # If the function is not available in the current langchain version
            return None

    @traceable(run_type="llm", name="evaluate_instruction")
    def evaluate_instruction(
        self, instruction: str, history: List[Dict], run_id: str = None, step: int = None
    ) -> Dict[str, Any]:
        """
        Evaluate an instruction for ethical violations.

        Args:
            instruction (str): The instruction to evaluate
            history (List[Dict]): The history context
            run_id (str, optional): The LangSmith run ID to associate this evaluation with
            step (int, optional): The step number in the simulation

        Returns:
            Dict[str, Any]: The evaluation result
        """
        # Get current run ID if not provided
        if run_id is None:
            run_id = self._get_run_id_from_callbacks()

        try:
            # Format context for evaluation
            context = self._format_context_for_evaluation(instruction, history)

            # Create and run a simple chain
            chain = (
                RunnablePassthrough()
                | (lambda x: [HumanMessage(content=x["prompt"])])
                | self.model
                | StrOutputParser()
            )

            # Build prompt with the ethical violations template
            evaluation_prompt = (
                self.prompts["ethical_violations"] + "\n\nScene: " + context
            )

            # Execute the chain with tracing
            response = chain.invoke(
                {"prompt": evaluation_prompt}, {"run_name": "ethical_evaluation"}
            )

            # Parse the evaluation result
            try:
                # Extract JSON from response, handling potential text before/after the JSON
                json_str = self._extract_json(response)
                evaluation_result = json.loads(json_str)

                # Add timestamp and instruction to the evaluation
                evaluation_result["timestamp"] = datetime.datetime.now().isoformat()
                evaluation_result["instruction"] = instruction

                # Update violation metrics
                self._update_metrics(evaluation_result)

                # Add step information
                evaluation_result["step"] = step if step is not None else len(self.evaluations)

                # Store the evaluation
                self.evaluations.append(evaluation_result)

                # Save to log file if enabled
                if self.log_to_file:
                    self._save_to_log()

                # If a run_id is provided, add this evaluation as metadata to that run
                if run_id and self.langsmith_client:
                    self.langsmith_client.update_run(
                        run_id=run_id,
                        metadata={
                            "ethical_evaluation": evaluation_result,
                            "current_violation_metrics": self.violation_metrics,
                        },
                    )

                return evaluation_result

            except json.JSONDecodeError:
                print(f"Error parsing evaluation result: {response}")
                error_result = {
                    "error": "Could not parse evaluation result",
                    "raw_response": response,
                }

                # Still log the error
                if self.log_to_file:
                    self._save_to_log()

                return error_result

        except Exception as e:
            print(f"Error evaluating instruction: {e}")
            return {"error": f"Could not evaluate instruction: {str(e)}"}

    def _save_to_log(self):
        """Save the current evaluations and metrics to the log file."""
        log_data = {"evaluations": self.evaluations, "metrics": self.get_metrics()}

        log_path = os.path.join(self.log_path, self.log_filename)

        try:
            with open(log_path, "w") as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Error saving evaluation log: {e}")

    def _format_context_for_evaluation(
        self, instruction: str, history: List[Dict]
    ) -> str:
        """Format the context for evaluation."""
        # Include the current instruction and relevant history
        context = f"The AI system is instructed to: {instruction}\n\n"
        context += "Previous context:\n"

        # Add relevant history entries (limit to last few entries to keep context manageable)
        for entry in history[-5:]:
            context += f"{entry['type'].upper()}: {entry['content']}\n"

        return context

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain non-JSON content."""
        # Find the first '{' and the last '}'
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        else:
            raise ValueError("No valid JSON found in the response")

    def _update_metrics(self, evaluation_result: Dict[str, Any]) -> None:
        """Update violation metrics based on evaluation result."""
        if "labels" in evaluation_result:
            for category, value in evaluation_result["labels"].items():
                if value == 1 and category in self.violation_metrics:
                    self.violation_metrics[category] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get the current metrics."""
        return {
            "violation_metrics": self.violation_metrics,
            "total_evaluations": len(self.evaluations),
            "total_violations": sum(self.violation_metrics.values()),
        }

    def get_evaluations(self) -> List[Dict[str, Any]]:
        """Get all evaluations."""
        return self.evaluations
