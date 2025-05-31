from typing import Dict, List
from cesare.modules.agent import Agent
from cesare.modules.environment import Environment
from cesare.modules.evaluator import Evaluator
from cesare.utils.database import SimulationDB
import yaml
import os
from langsmith import Client, traceable


class CESARE:
    def __init__(
        self,
        config: dict,
        prompts_file: str = "cesare/prompts-simulation-factory.yaml",
        evaluation_prompts_file: str = "cesare/prompts-evaluation.yaml",
        db_path: str = "logs/simulations.duckdb",
    ):
        self.config = config
        models = config["models"]

        # Load prompts
        with open(prompts_file, "r") as file:
            self.prompts = yaml.safe_load(file)

        # Store paths for prompt files
        self.prompts_file = prompts_file
        self.evaluation_prompts_file = evaluation_prompts_file

        # Get model configurations (handle both single agent and multi-agent format)
        if "agent" in models:
            # Single agent format
            agent_model = models["agent"]["name"]
            agent_provider = models["agent"]["provider"]
            agent_temperature = models["agent"].get(
                "temperature"
            )  # None if not specified
        elif "agents" in models and len(models["agents"]) > 0:
            # Multi-agent format - take the first agent for single simulation
            agent_model = models["agents"][0]["name"]
            agent_provider = models["agents"][0]["provider"]
            agent_temperature = models["agents"][0].get(
                "temperature"
            )  # None if not specified
        else:
            raise ValueError(
                "No agent configuration found. Use either 'agent' or 'agents' in models section."
            )

        env_model = models["environment"]["name"]
        env_provider = models["environment"]["provider"]
        env_temperature = models["environment"].get(
            "temperature"
        )  # None if not specified

        self.agent = Agent(
            model_name=agent_model,
            prompts_file=prompts_file,
            provider=agent_provider,
            temperature=agent_temperature,
        )
        self.environment = Environment(
            model_name=env_model,
            prompts_file=prompts_file,
            provider=env_provider,
            temperature=env_temperature,
        )

        # Get the configurable keys from the prompt configuration
        self.ai_key = self.agent.get_ai_key()
        self.environment_key = self.environment.get_environment_key()

        # Initialize evaluator if evaluation is enabled
        self.evaluator = None
        if config.get("evaluation", {}).get("enabled", False):
            # Get evaluator model config, default to agent if not specified
            if "evaluator" in models:
                eval_model = models["evaluator"]["name"]
                eval_provider = models["evaluator"]["provider"]
            else:
                eval_model, eval_provider = agent_model, agent_provider

            eval_config = config.get("evaluation", {})

            self.evaluator = Evaluator(
                model_name=eval_model,
                evaluation_prompts_file=evaluation_prompts_file,
                log_to_file=eval_config.get("log_to_file", True),
                log_path=eval_config.get("log_path", "logs/evaluations/"),
                provider=eval_provider,
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

        # Get experiment name from config if available
        experiment_name = None
        if "experiment" in self.config:
            experiment_name = self.config["experiment"]["name"]

        # Save to database
        self.db.save_simulation(
            history=self.history,
            evaluations=evaluations,
            config=self.config,
            metrics=self.metrics,
            prompts=prompt_contents,
            experiment_name=experiment_name,
            ai_key=self.ai_key,
            environment_key=self.environment_key,
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

        # Get instruction from Agent
        instruction = self.agent.generate_instruction(
            self.history if step > 0 else None
        )
        self.add_to_history(self.ai_key, instruction)

        # Update metrics
        self.metrics["total_instructions"] += 1
        self.metrics["total_steps"] += 1

        # Evaluate the instruction if evaluator is enabled
        if self.evaluator:
            evaluation = self.evaluator.evaluate_instruction(
                instruction,
                self.history,
                run_id=step_run_id or parent_run_id,
                step=len(self.history) - 1,
            )
            # Add evaluation metrics to simulation metrics
            self._update_metrics_from_evaluation(evaluation)

        # Get response from ENVIRONMENT
        env_response = self.environment.generate_response(self.history)
        self.add_to_history(self.environment_key, env_response)

        print(f"Step {step + 1}:")
        print(f"{self.ai_key.title()}: {instruction}")
        print(f"{self.environment_key.title()}: {env_response}\n")

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
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='CESARE AI Safety Simulation System')
    parser.add_argument('command', choices=['run', 'validate'], help='Command to execute')
    parser.add_argument('config_path', help='Path to the experiment configuration directory')
    parser.add_argument('--prompts', default='cesare/prompts-simulation-factory.yaml', help='Path to simulation prompts file')
    parser.add_argument('--eval-prompts', default='cesare/prompts-evaluation.yaml', help='Path to evaluation prompts file')
    parser.add_argument('--db', default='logs/simulations.duckdb', help='Path to database file')
    
    args = parser.parse_args()
    
    # Load configuration
    config_file = os.path.join(args.config_path, 'simulation.yaml')
    if not os.path.exists(config_file):
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
        
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    # Determine prompts files based on experiment directory
    simulation_prompts = os.path.join(args.config_path, 'prompts', 'simulation.yaml')
    evaluation_prompts = os.path.join(args.config_path, 'prompts', 'evaluations.yaml')
    
    # Fallback to default prompts if experiment-specific ones don't exist
    if not os.path.exists(simulation_prompts):
        simulation_prompts = args.prompts
    if not os.path.exists(evaluation_prompts):
        evaluation_prompts = args.eval_prompts
    
    if args.command == 'validate':
        print(f"Validating configuration: {config_file}")
        print(f"Simulation prompts: {simulation_prompts}")
        print(f"Evaluation prompts: {evaluation_prompts}")
        
        # Basic validation checks
        required_sections = ['models']
        for section in required_sections:
            if section not in config:
                print(f"Error: Missing required section '{section}' in configuration")
                sys.exit(1)
        
        if 'agents' not in config['models']:
            print("Error: Missing 'agents' in models configuration")
            sys.exit(1)
        
        # Check simulation parameters (can be in 'simulation' section or top-level)
        if 'simulation' in config:
            sim_config = config['simulation']
            steps_key = 'max_steps'
        else:
            sim_config = config
            steps_key = 'steps'
            
        if steps_key not in sim_config:
            print(f"Error: Missing '{steps_key}' in simulation configuration")
            sys.exit(1)
            
        if 'repetitions' not in sim_config:
            print("Error: Missing 'repetitions' in simulation configuration")
            sys.exit(1)
            
        print(f"✓ Configuration is valid")
        print(f"✓ Found {len(config['models']['agents'])} agent configurations")
        print(f"✓ Simulation steps: {sim_config[steps_key]}")
        print(f"✓ Repetitions: {sim_config['repetitions']}")
        
        if 'environment' in config['models']:
            env_model = config['models']['environment']
            temp_info = f" (temp: {env_model.get('temperature', 'default')})" if 'temperature' in env_model else ""
            print(f"✓ Environment model configured: {env_model['name']}{temp_info}")
        if 'evaluator' in config['models']:
            eval_model = config['models']['evaluator']
            temp_info = f" (temp: {eval_model.get('temperature', 'default')})" if 'temperature' in eval_model else ""
            print(f"✓ Evaluator model configured: {eval_model['name']}{temp_info}")
            
        # Calculate total simulations
        total_sims = len(config['models']['agents']) * sim_config['repetitions']
        print(f"✓ Total simulations to run: {total_sims}")
        
    elif args.command == 'run':
        simulator = CESARE(config, 
                          prompts_file=simulation_prompts,
                          evaluation_prompts_file=evaluation_prompts,
                          db_path=args.db)
        simulator.run_simulation()
