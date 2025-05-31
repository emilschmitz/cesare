import os
import sys
import yaml
import typer
from pathlib import Path
from typing import List, Dict
import time
from rich.console import Console
from rich.table import Table
import glob
from tqdm import tqdm
import threading

# Add the cesare directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CESARE
from utils.database import SimulationDB

# Initialize Typer app and console
app = typer.Typer(help="Run CESARE experiments with multiple models")
console = Console()


def check_experiment_exists(
    experiment_name: str, db_path: str = "logs/simulations.duckdb"
) -> bool:
    """Check if an experiment with the given name already exists in the database."""
    try:
        db = SimulationDB(db_path)
        experiments = db.get_experiments()

        # Check if experiment name already exists
        existing_experiments = experiments[
            experiments["experiment_name"] == experiment_name
        ]

        if not existing_experiments.empty:
            return True
        return False
    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not check for existing experiments: {e}[/yellow]"
        )
        return False
    finally:
        if "db" in locals():
            db.close()


class ExperimentRunner:
    def __init__(
        self,
        experiment_folder: str,
        max_workers: int = 3,
        prompts_file: str = "cesare/prompts-simulation-factory.yaml",
    ):
        self.experiment_folder = experiment_folder
        self.max_workers = max_workers
        self.prompts_file = prompts_file
        self.experiment_name = os.path.basename(experiment_folder)
        self.config_files = [
            str(p) for p in Path(experiment_folder).glob("*.yaml") if p.is_file()
        ]

    def get_config_files(self) -> List[str]:
        """Get all YAML config files in the experiment folder, expanding multi-agent configs."""
        config_path = Path(self.experiment_folder)
        if not config_path.exists():
            raise ValueError(
                f"Experiment folder {self.experiment_folder} does not exist"
            )

        config_files = list(config_path.glob("*.yaml"))
        if not config_files:
            raise ValueError(f"No YAML config files found in {self.experiment_folder}")

        # Expand multi-agent configs into separate virtual config files
        expanded_configs = []
        for config_file in config_files:
            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)

                # Get repetitions from config (default to 1)
                repetitions = config.get("simulation", {}).get("repetitions", 1)

                models = config.get("models", {})
                if "agents" in models and isinstance(models["agents"], list):
                    # Multi-agent config - create virtual configs for each agent and repetition
                    for i, agent in enumerate(models["agents"]):
                        for rep in range(repetitions):
                            virtual_config_name = f"{config_file.stem}-agent{i + 1}-{agent['name'].replace('/', '-')}-rep{rep + 1}"
                            expanded_configs.append(
                                {
                                    "file_path": str(config_file),
                                    "virtual_name": virtual_config_name,
                                    "agent_index": i,
                                    "agent_name": agent["name"],
                                    "agent_provider": agent["provider"],
                                    "repetition": rep + 1,
                                    "total_repetitions": repetitions,
                                }
                            )
                else:
                    # Single agent config - create repetitions
                    for rep in range(repetitions):
                        virtual_config_name = (
                            f"{config_file.stem}-rep{rep + 1}"
                            if repetitions > 1
                            else config_file.stem
                        )
                        expanded_configs.append(
                            {
                                "file_path": str(config_file),
                                "virtual_name": virtual_config_name,
                                "agent_index": None,
                                "agent_name": models.get("agent", {}).get(
                                    "name", "unknown"
                                ),
                                "agent_provider": models.get("agent", {}).get(
                                    "provider", "unknown"
                                ),
                                "repetition": rep + 1,
                                "total_repetitions": repetitions,
                            }
                        )
            except Exception as e:
                tqdm.write(f"Warning: Could not parse {config_file}: {e}")
                # Keep the file anyway for error handling
                expanded_configs.append(
                    {
                        "file_path": str(config_file),
                        "virtual_name": config_file.stem,
                        "agent_index": None,
                        "agent_name": "unknown",
                        "agent_provider": "unknown",
                        "repetition": 1,
                        "total_repetitions": 1,
                    }
                )

        return expanded_configs

    def run_single_simulation(self, config_info: dict, pbar: tqdm = None) -> Dict:
        """Run a single simulation with the given config info."""
        start_time = time.time()
        config_name = config_info["virtual_name"]
        config_file = config_info["file_path"]
        agent_index = config_info["agent_index"]
        agent_name = config_info["agent_name"]

        try:
            # Load configuration
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            # If this is a multi-agent config, modify it to use the specific agent
            if agent_index is not None:
                models = config["models"]
                selected_agent = models["agents"][agent_index]
                # Replace the agents list with a single agent
                config["models"]["agent"] = selected_agent
                del config["models"]["agents"]

            # Add experiment metadata to config
            config["experiment"] = {
                "name": self.experiment_name,
                "config_file": os.path.basename(config_file),
                "virtual_config": config_name,
                "agent_name": agent_name,
                "repetition": config_info.get("repetition", 1),
                "total_repetitions": config_info.get("total_repetitions", 1),
            }

            # Use local prompt files from the experiment folder
            experiment_path = Path(self.experiment_folder)
            prompts_file = str(experiment_path / "prompts" / "simulation.yaml")
            evaluation_prompts_file = str(
                experiment_path / "prompts" / "evaluations.yaml"
            )

            # Use main database path instead of experiment-specific path
            db_path = "logs/simulations.duckdb"

            # Create CESARE instance with the local prompts files
            simulator = CESARE(
                config,
                prompts_file=prompts_file,
                evaluation_prompts_file=evaluation_prompts_file,
                db_path=db_path,
            )

            # Run simulation
            simulator.run_simulation()

            duration = time.time() - start_time
            
            if pbar:
                pbar.set_postfix_str(f"✓ {agent_name[:20]}... ({duration:.1f}s)")
                pbar.update(1)

            return {
                "status": "success",
                "config_file": config_file,
                "config_name": config_name,
                "model": agent_name,
                "duration": duration,
            }

        except Exception as e:
            duration = time.time() - start_time
            
            if pbar:
                pbar.set_postfix_str(f"✗ {agent_name[:20]}... ({str(e)[:30]}...)")
                pbar.update(1)

            return {
                "status": "error",
                "config_file": config_file,
                "config_name": config_name,
                "error": str(e),
                "model": agent_name,
                "duration": duration,
            }

    def run_experiment(self, parallel: bool = True) -> List[Dict]:
        """Run all simulations in the experiment."""
        config_infos = self.get_config_files()

        if not config_infos:
            tqdm.write("No configuration files found!")
            return []

        total_simulations = len(config_infos)
        
        # Create main progress bar
        main_pbar = tqdm(
            total=total_simulations,
            desc=f"Running {self.experiment_name}",
            unit="sim",
            position=0,
            leave=True,
            ncols=100,  # Fixed width for consistency
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )

        # Create counters for tracking
        success_count = 0
        error_count = 0
        results = []
        
        # Thread-safe counters
        counter_lock = threading.Lock()

        def update_counters(result):
            nonlocal success_count, error_count
            with counter_lock:
                if result["status"] == "success":
                    success_count += 1
                else:
                    error_count += 1
                
                # Update main progress bar description
                main_pbar.set_description(
                    f"{self.experiment_name} [✓{success_count} ✗{error_count}]"
                )

        start_time = time.time()

        if parallel:
            # Use ThreadPoolExecutor for parallel execution
            from concurrent.futures import ThreadPoolExecutor, as_completed

            # Use self.max_workers instead of hardcoded value
            max_workers = min(total_simulations, self.max_workers)
            
            tqdm.write(f"Starting parallel execution with {max_workers} workers")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_config = {
                    executor.submit(self.run_single_simulation, config_info, main_pbar): config_info
                    for config_info in config_infos
                }

                # Process completed tasks
                for future in as_completed(future_to_config):
                    config_info = future_to_config[future]
                    try:
                        result = future.result()
                        results.append(result)
                        update_counters(result)

                    except Exception as e:
                        config_name = config_info["virtual_name"]
                        result = {
                            "status": "error",
                            "config_file": config_info["file_path"],
                            "config_name": config_name,
                            "error": str(e),
                            "model": config_info["agent_name"],
                            "duration": 0,
                        }
                        results.append(result)
                        update_counters(result)
                        main_pbar.update(1)
        else:
            # Sequential execution
            tqdm.write("Starting sequential execution")
            
            for config_info in config_infos:
                result = self.run_single_simulation(config_info, main_pbar)
                results.append(result)
                update_counters(result)

        # Close progress bar
        main_pbar.close()

        # Print final summary
        total_time = time.time() - start_time
        tqdm.write(f"\nExperiment completed in {total_time:.1f}s")
        tqdm.write(f"Successful: {success_count}/{total_simulations}")
        tqdm.write(f"Failed: {error_count}/{total_simulations}")

        if error_count > 0:
            tqdm.write("\nFailed simulations:")
            for result in results:
                if result["status"] == "error":
                    tqdm.write(f"  - {result['config_name']}: {result.get('error', 'Unknown error')}")

        return results

    def print_summary(self, results: List[Dict]):
        """Print a summary of the experiment results."""
        table = Table(show_header=True, header_style="bold")
        table.add_column("Status")
        table.add_column("Configuration")
        table.add_column("Model")
        table.add_column("Duration")

        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]

        for result in sorted(results, key=lambda x: x["config_name"]):
            status = "✅" if result["status"] == "success" else "❌"
            status_color = "green" if result["status"] == "success" else "red"
            duration_str = (
                f"{result['duration']:.1f}s" if "duration" in result else "N/A"
            )
            agent_model = result.get("model", "Unknown")

            table.add_row(
                f"[{status_color}]{status}[/]",
                result["config_name"],
                agent_model,
                duration_str,
            )

        console.print("\n" + "=" * 60)
        console.print(f"[bold]EXPERIMENT SUMMARY:[/] {self.experiment_name}")
        console.print("=" * 60)

        console.print(table)

        console.print("\n[bold]Summary:[/]")
        console.print(f"  Total simulations: [cyan]{len(results)}[/]")
        console.print(f"  Successful: [green]{len(successful)}[/]")
        console.print(f"  Failed: [red]{len(failed)}[/]")

        if successful:
            total_duration = sum(r["duration"] for r in successful)
            avg_duration = total_duration / len(successful)
            console.print(f"  Average duration: [cyan]{avg_duration:.1f}s[/]")
            console.print(f"  Total duration: [cyan]{total_duration:.1f}s[/]")

        if failed:
            console.print(
                f"\n⚠️  [bold red]{len(failed)}[/] simulation(s) failed. Check logs for details."
            )


@app.command(name="run")
def run_experiment(
    experiment_folder: str = typer.Argument(
        ..., help="Path to experiment folder containing YAML configs"
    ),
    sequential: bool = typer.Option(
        False,
        "--sequential",
        help="Run simulations sequentially instead of in parallel",
    ),
    max_workers: int = typer.Option(
        20, "--max-workers", help="Maximum number of parallel workers"
    ),
    validate_only: bool = typer.Option(
        False, "--validate", help="Only validate configs without running the experiment"
    ),
    prompts_file: str = typer.Option(
        "cesare/prompts-simulation-factory.yaml",
        "--prompts-file",
        help="Path to the simulation prompts YAML file",
    ),
):
    """Run a CESARE experiment with multiple models."""
    # Validate experiment folder
    if not Path(experiment_folder).exists():
        console.print(
            f"[bold red]Error:[/] Experiment folder '{experiment_folder}' does not exist"
        )
        raise typer.Exit(code=1)

    # Check for duplicate experiment (unless validating only)
    experiment_name = Path(experiment_folder).name
    if not validate_only and check_experiment_exists(experiment_name):
        console.print(
            f"[bold red]Error:[/] Experiment '{experiment_name}' already exists in the database!"
        )
        console.print("[yellow]Hint:[/] If you want to re-run this experiment, please:")
        console.print("  1. Delete the existing experiment from the database, or")
        console.print("  2. Rename this experiment folder to a different name")
        raise typer.Exit(code=1)

    # Create experiment runner
    runner = ExperimentRunner(
        experiment_folder=experiment_folder,
        max_workers=max_workers,
        prompts_file=prompts_file,
    )

    try:
        # Get config files
        config_files = runner.get_config_files()

        # Print experiment info
        console.print(f"[bold green]Experiment:[/] {Path(experiment_folder).name}")
        console.print(
            f"[bold]Found [cyan]{len(config_files)}[/] simulation configurations"
        )
        console.print(
            f"[bold]Parallel execution:[/] {'[green]Yes[/]' if not sequential else '[yellow]No[/]'}"
        )
        
        # Show actual max_workers being used
        actual_max_workers = runner.max_workers if not sequential else 1
        console.print(f"[bold]Max workers:[/] {actual_max_workers}")

        # If validate only, check configs and exit
        if validate_only:
            with console.status("[bold green]Validating configs...[/]"):
                errors = []
                # Get unique config files for validation
                unique_files = list(set(info["file_path"] for info in config_files))

                for config_file in unique_files:
                    try:
                        with open(config_file) as f:
                            config = yaml.safe_load(f)

                        # Validation for flexible format
                        if "models" not in config:
                            errors.append((config_file, "Missing 'models' section"))
                        else:
                            models = config["models"]
                            required_models = ["environment", "evaluator"]
                            missing_models = [
                                m for m in required_models if m not in models
                            ]
                            if missing_models:
                                errors.append(
                                    (
                                        config_file,
                                        f"Missing required models: {', '.join(missing_models)}",
                                    )
                                )

                            # Check for agent or agents
                            if "agent" not in models and "agents" not in models:
                                errors.append(
                                    (
                                        config_file,
                                        "Missing 'agent' or 'agents' in models section",
                                    )
                                )
                            elif "agent" in models and "agents" in models:
                                errors.append(
                                    (
                                        config_file,
                                        "Cannot have both 'agent' and 'agents' in models section",
                                    )
                                )

                            # Validate model format (must have name and provider)
                            for model_key, model_config in models.items():
                                if model_key == "agents":
                                    # Validate agents list
                                    if not isinstance(model_config, list):
                                        errors.append(
                                            (config_file, "'agents' must be a list")
                                        )
                                    else:
                                        for i, agent in enumerate(model_config):
                                            if not isinstance(agent, dict):
                                                errors.append(
                                                    (
                                                        config_file,
                                                        f"Agent {i + 1} must be a dict with 'name' and 'provider' fields",
                                                    )
                                                )
                                            else:
                                                if "name" not in agent:
                                                    errors.append(
                                                        (
                                                            config_file,
                                                            f"Agent {i + 1} missing 'name' field",
                                                        )
                                                    )
                                                if "provider" not in agent:
                                                    errors.append(
                                                        (
                                                            config_file,
                                                            f"Agent {i + 1} missing 'provider' field",
                                                        )
                                                    )
                                elif model_key in [
                                    "agent",
                                    "environment",
                                    "evaluator",
                                    "describer",
                                ]:
                                    # Validate single model
                                    if not isinstance(model_config, dict):
                                        errors.append(
                                            (
                                                config_file,
                                                f"Model '{model_key}' must be a dict with 'name' and 'provider' fields",
                                            )
                                        )
                                    else:
                                        if "name" not in model_config:
                                            errors.append(
                                                (
                                                    config_file,
                                                    f"Model '{model_key}' missing 'name' field",
                                                )
                                            )
                                        if "provider" not in model_config:
                                            errors.append(
                                                (
                                                    config_file,
                                                    f"Model '{model_key}' missing 'provider' field",
                                                )
                                            )
                    except Exception as e:
                        errors.append((config_file, f"Error parsing config: {str(e)}"))

            # Print validation results
            if errors:
                console.print("\n[bold red]Validation failed with errors:[/]")
                for file, error in errors:
                    console.print(f"  [yellow]{Path(file).name}[/]: {error}")
                raise typer.Exit(code=1)
            else:
                console.print("\n[bold green]All configurations are valid![/]")
                return  # Exit successfully without raising an exception

        # Run experiment
        start_time = time.time()
        results = runner.run_experiment(parallel=not sequential)
        end_time = time.time()

        # Print summary
        runner.print_summary(results)

        console.print(
            f"\nTotal experiment time: [bold cyan]{end_time - start_time:.1f}s[/]"
        )

        # Exit with error code if any simulations failed
        failed_count = len([r for r in results if r["status"] == "error"])
        if failed_count > 0:
            raise typer.Exit(code=1)

    except typer.Exit:
        # Re-raise typer.Exit exceptions to preserve exit codes
        raise
    except KeyboardInterrupt:
        console.print("\n\n[bold red]Experiment interrupted by user[/]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n[bold red]Experiment failed:[/] {e}")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_experiments():
    """List all available experiment folders."""
    # Look for experiment folders
    experiment_folders = []
    for folder in glob.glob("config/*"):
        if os.path.isdir(folder) and "experiment" in os.path.basename(folder).lower():
            experiment_folders.append(folder)

    if not experiment_folders:
        console.print("[yellow]No experiment folders found in config/ directory[/]")
        return

    # Create a table to display experiments
    table = Table(show_header=True, header_style="bold")
    table.add_column("Experiment Name")
    table.add_column("Simulations")
    table.add_column("Agent Models")

    for folder in sorted(experiment_folders):
        name = os.path.basename(folder)

        try:
            runner = ExperimentRunner(folder)
            config_infos = runner.get_config_files()

            # Extract unique agent models
            agent_models = set()
            for info in config_infos:
                agent_models.add(info["agent_name"])

            table.add_row(
                name,
                str(len(config_infos)),
                ", ".join(sorted(agent_models)) if agent_models else "Unknown",
            )
        except Exception as e:
            table.add_row(name, "Error", f"Failed to parse: {str(e)}")

    console.print("[bold]Available Experiments:[/]")
    console.print(table)
    console.print(
        "\nRun an experiment with: [bold cyan]python -m cesare.main_experiment run <experiment_folder>[/]"
    )


@app.command(name="delete")
def delete_experiment(
    experiment_name: str = typer.Argument(
        ..., help="Name of the experiment to delete from the database"
    ),
    force: bool = typer.Option(
        False, "--force", help="Skip confirmation prompt"
    ),
):
    """Delete an experiment and all its data from the database."""
    from utils.database import SimulationDB
    
    # Check if experiment exists
    db = SimulationDB("logs/simulations.duckdb")
    
    try:
        experiments = db.get_experiments()
        existing_experiment = experiments[experiments["experiment_name"] == experiment_name]
        
        if existing_experiment.empty:
            console.print(f"[yellow]Experiment '{experiment_name}' not found in database[/]")
            return
        
        # Show experiment info
        exp_info = existing_experiment.iloc[0]
        console.print(f"[bold]Experiment:[/] {experiment_name}")
        console.print(f"[bold]Simulations:[/] {exp_info['actual_simulations']}")
        console.print(f"[bold]Created:[/] {exp_info['created_time']}")
        
        # Confirm deletion unless forced
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete experiment '{experiment_name}' and all its data?"
            )
            if not confirm:
                console.print("[yellow]Deletion cancelled[/]")
                return
        
        # Delete the experiment
        console.print(f"[yellow]Deleting experiment '{experiment_name}'...[/]")
        success = db.delete_experiment(experiment_name)
        
        if success:
            console.print(f"[green]Successfully deleted experiment '{experiment_name}'[/]")
        else:
            console.print(f"[red]Failed to delete experiment '{experiment_name}'[/]")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[red]Error deleting experiment: {e}[/]")
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command(name="list-db")
def list_database_experiments():
    """List all experiments stored in the database."""
    from utils.database import SimulationDB
    
    db = SimulationDB("logs/simulations.duckdb")
    
    try:
        experiments = db.get_experiments()
        
        if experiments.empty:
            console.print("[yellow]No experiments found in database[/]")
            return
        
        # Create a table to display experiments
        table = Table(show_header=True, header_style="bold")
        table.add_column("Experiment Name")
        table.add_column("Simulations")
        table.add_column("Created")
        table.add_column("Status")
        
        for _, exp in experiments.iterrows():
            status = "✅ Complete" if exp['actual_simulations'] > 0 else "❌ Empty"
            table.add_row(
                exp['experiment_name'],
                str(exp['actual_simulations']),
                exp['created_time'].strftime("%Y-%m-%d %H:%M") if exp['created_time'] else "Unknown",
                status
            )
        
        console.print("[bold]Experiments in Database:[/]")
        console.print(table)
        console.print(
            "\nDelete an experiment with: [bold cyan]python -m cesare.main_experiment delete <experiment_name>[/]"
        )
        
    except Exception as e:
        console.print(f"[red]Error reading database: {e}[/]")
        raise typer.Exit(code=1)
    finally:
        db.close()


if __name__ == "__main__":
    app()
