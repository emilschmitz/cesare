from typing import Dict, List
from utils.config import load_api_key
from modules.agent import Agent
from modules.environment import Environment
from modules.evaluator import Evaluator
from utils.database import SimulationDB
import yaml
import os
from langsmith import Client, traceable


class CESARE:
    def __init__(
        self,
        api_key: str,
        config: dict,
        prompts_file: str = "cesare/prompts-simulation.yaml",
        evaluation_prompts_file: str = "cesare/prompts-evaluation.yaml",
        db_path: str = "logs/simulations.duckdb",
    ):
        self._api_key = api_key

        self.config = config
        models = config["models"]

        # Load prompts
        with open(prompts_file, "r") as file:
            self.prompts = yaml.safe_load(file)

        # Store paths for prompt files
        self.prompts_file = prompts_file
        self.evaluation_prompts_file = evaluation_prompts_file

        self.agent = Agent(
            api_key=self._api_key, model_name=models["agent"], prompts_file=prompts_file
        )
        self.environment = Environment(
            api_key=self._api_key,
            model_name=models["environment"],
            prompts_file=prompts_file,
        )

        # Initialize evaluator if evaluation is enabled
        self.evaluator = None
        if config.get("evaluation", {}).get("enabled", False):
            eval_model = models.get(
                "evaluator", models["agent"]
            )  # Default to agent model if not specified
            eval_config = config.get("evaluation", {})

            self.evaluator = Evaluator(
                api_key=self._api_key,
                model_name=eval_model,
                evaluation_prompts_file=evaluation_prompts_file,
                log_to_file=eval_config.get("log_to_file", True),
                log_path=eval_config.get("log_path", "logs/evaluations/"),
            )

        self.history: List[Dict] = []

        # Initialize metrics tracking
        self.metrics = {
            "total_instructions": 0,
            "total_steps": 0,
            "ethical_violations": {},
        }

        # Initialize LangSmith client for tracing
        self.langsmith_client = Client()

        # Initialize database
        self.db = SimulationDB(db_path)

    def add_to_history(self, entry_type: str, content: str):
        self.history.append({"type": entry_type, "content": content})

    @traceable(run_type="chain", name="full_simulation")
    def run_simulation(self, start_prompt: str | None = None):
        """
        Run the complete simulation with full tracing.

        Args:
            start_prompt (str | None, optional): Initial prompt to start the simulation.
                If None, uses the prompt from the YAML file.
        """
        # Get parent run_id from the callbacks if available
        parent_run_id = self._get_run_id_from_callbacks()

        # Use the start prompt from YAML file if not provided
        if start_prompt is None:
            start_prompt = self.prompts["start_prompt"]

        self.add_to_history("start_prompt", start_prompt)
        instruction = self.agent.generate_first_instruction(start_prompt)
        self.add_to_history("instruction", instruction)

        # Update metrics
        self.metrics["total_instructions"] += 1

        # Evaluate the first instruction if evaluator is enabled
        if self.evaluator:
            evaluation = self.evaluator.evaluate_instruction(
                instruction, self.history, run_id=parent_run_id
            )
            # Add evaluation metrics to simulation metrics
            self._update_metrics_from_evaluation(evaluation)

        # Update parent run with initial metrics
        if parent_run_id:
            self._update_parent_run_metrics(parent_run_id)

        max_steps = self.config["simulation"]["max_steps"]

        for step in range(max_steps):
            # Run a simulation step with its own trace
            self._run_simulation_step(step, parent_run_id)

            # Update parent run with current metrics after each step
            if parent_run_id:
                self._update_parent_run_metrics(parent_run_id)

        # Final update to parent run
        if parent_run_id:
            self._update_parent_run_metrics(parent_run_id, is_final=True)

        # Save simulation to database
        self.save_to_db()

    def save_to_db(self):
        """Save the simulation data to the database."""
        # Collect all prompt contents
        prompt_contents = {}

        # Load simulation prompts
        try:
            with open(self.prompts_file, "r") as f:
                prompt_contents["simulation"] = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading simulation prompts: {e}")
            prompt_contents["simulation"] = {}

        # Load evaluation prompts if available
        if self.evaluation_prompts_file and os.path.exists(
            self.evaluation_prompts_file
        ):
            try:
                with open(self.evaluation_prompts_file, "r") as f:
                    prompt_contents["evaluation"] = yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading evaluation prompts: {e}")
                prompt_contents["evaluation"] = {}

        # Get evaluations if available
        evaluations = []
        if self.evaluator:
            evaluations = self.evaluator.get_evaluations()

        # Save to database
        self.db.save_simulation(
            history=self.history,
            evaluations=evaluations,
            config=self.config,
            metrics=self.metrics,
            prompts=prompt_contents,
        )

        print("Simulation saved to database.")

    def _get_run_id_from_callbacks(self):
        """Get the run ID from the current callbacks if available."""
        try:
            from langchain.callbacks import get_current_run_id

            return get_current_run_id()
        except (ImportError, AttributeError):
            # If the function is not available in the current langchain version
            return None

    @traceable(run_type="chain", name="simulation_step")
    def _run_simulation_step(self, step: int, parent_run_id: str = None):
        """
        Run a single step of the simulation with its own trace.

        Args:
            step (int): The current step number
            parent_run_id (str, optional): The parent run ID for evaluation logging
        """
        # Get current run_id for this step
        step_run_id = self._get_run_id_from_callbacks()

        # Get order from ACTOR
        instruction = self.agent.generate_instruction(self.history)
        self.add_to_history("instruction", instruction)

        # Update metrics
        self.metrics["total_instructions"] += 1
        self.metrics["total_steps"] += 1

        # Evaluate the instruction if evaluator is enabled
        if self.evaluator:
            evaluation = self.evaluator.evaluate_instruction(
                instruction, self.history, run_id=step_run_id or parent_run_id
            )
            # Add evaluation metrics to simulation metrics
            self._update_metrics_from_evaluation(evaluation)

        # Get response from ENVIRONMENT
        env_response = self.environment.generate_response(self.history)
        self.add_to_history("environment", env_response)

        print(f"Step {step + 1}:")
        print(f"Instruction: {instruction}")
        print(f"Environment: {env_response}\n")

    def _update_metrics_from_evaluation(self, evaluation: Dict):
        """
        Update metrics based on evaluation results.

        Args:
            evaluation (Dict): The evaluation result
        """
        if "labels" in evaluation:
            violation_metrics = self.metrics.get("ethical_violations", {})

            for category, value in evaluation["labels"].items():
                if value == 1:
                    violation_metrics[category] = violation_metrics.get(category, 0) + 1

            self.metrics["ethical_violations"] = violation_metrics

    def _update_parent_run_metrics(self, parent_run_id: str, is_final: bool = False):
        """
        Update the parent run with current metrics.

        Args:
            parent_run_id (str): The ID of the parent run to update
            is_final (bool, optional): Whether this is the final update. Defaults to False.
        """
        # Add any final-specific metadata
        metadata = {"metrics": self.metrics, "total_history_length": len(self.history)}

        # Add evaluator metrics if available
        if self.evaluator:
            metadata["evaluator_metrics"] = self.evaluator.get_metrics()

        if is_final:
            metadata["simulation_completed"] = True

            # Add full evaluation history for final update
            if self.evaluator:
                metadata["full_evaluations"] = self.evaluator.get_evaluations()

        # Update the parent run with current metrics
        self.langsmith_client.update_run(run_id=parent_run_id, metadata=metadata)


if __name__ == "__main__":
    with open("config/deepseek-v3.yaml") as f:
        config = yaml.safe_load(f)

    api_key = load_api_key()

    simulator = CESARE(api_key, config, prompts_file="cesare/prompts-simulation.yaml")
    simulator.run_simulation()
