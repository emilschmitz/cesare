import os
import sys
import yaml
import typer
from pathlib import Path
from typing import List, Dict
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
import glob

# Add the cesare directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CESARE

# Initialize Typer app and console
app = typer.Typer(help="Run CESARE experiments with multiple models")
console = Console()


class ExperimentRunner:
    def __init__(self, experiment_folder: str, max_workers: int = 3, prompts_file: str = "cesare/prompts-simulation-factory.yaml"):
        self.experiment_folder = experiment_folder
        self.max_workers = max_workers
        self.prompts_file = prompts_file
        self.experiment_name = os.path.basename(experiment_folder)
        self.config_files = [
            str(p) for p in Path(experiment_folder).glob("*.yaml") if p.is_file()
        ]
        
    def get_config_files(self) -> List[str]:
        """Get all YAML config files in the experiment folder."""
        config_path = Path(self.experiment_folder)
        if not config_path.exists():
            raise ValueError(f"Experiment folder {self.experiment_folder} does not exist")
        
        config_files = list(config_path.glob("*.yaml"))
        if not config_files:
            raise ValueError(f"No YAML config files found in {self.experiment_folder}")
        
        return [str(f) for f in config_files]
    
    def run_single_simulation(self, config_file: str, progress_callback=None) -> Dict:
        """Run a single simulation with the given config."""
        start_time = time.time()
        config_name = Path(config_file).stem
        
        if progress_callback:
            progress_callback(f"Starting simulation: {config_name}", 0)
        
        try:
            # Load configuration
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Add experiment metadata to config
            config['experiment'] = {
                'name': self.experiment_name,
                'config_file': os.path.basename(config_file)
            }
            
            # Extract agent model name for reporting (new format only)
            agent_model_name = config.get('models', {}).get('agent', {}).get('name', 'unknown')
            
            # Use local prompt files from the experiment folder
            experiment_path = Path(self.experiment_folder)
            prompts_file = str(experiment_path / "prompts" / "simulation.yaml")
            evaluation_prompts_file = str(experiment_path / "prompts" / "evaluations.yaml")
            
            # Use main database path instead of experiment-specific path
            db_path = "logs/simulations.duckdb"
            
            if progress_callback:
                progress_callback(f"Initializing {config_name}", 10)
            
            # Create CESARE instance with the local prompts files
            simulator = CESARE(
                config,
                prompts_file=prompts_file,
                evaluation_prompts_file=evaluation_prompts_file,
                db_path=db_path
            )
            
            if progress_callback:
                progress_callback(f"Running simulation {config_name}", 20)
            
            # Run simulation with progress tracking
            max_steps = config.get('simulation', {}).get('max_steps', 5)
            
            # Monkey patch the simulation step to report progress
            original_run_step = simulator._run_simulation_step
            def progress_run_step(step, parent_run_id=None):
                if progress_callback:
                    progress = 20 + (step + 1) * (70 / max_steps)  # 20-90% for simulation steps
                    progress_callback(f"{config_name} - Step {step + 1}/{max_steps}", progress)
                return original_run_step(step, parent_run_id)
            
            simulator._run_simulation_step = progress_run_step
            
            simulator.run_simulation()
            
            if progress_callback:
                progress_callback(f"Completed simulation: {config_name}", 100)
            
            duration = time.time() - start_time
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Completed simulation: {config_name} ({duration:.1f}s)")
            
            return {
                'status': 'success',
                'config_file': config_file,
                'config_name': config_name,
                'model': agent_model_name,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            if progress_callback:
                progress_callback(f"Failed {config_name}: {str(e)}", 100)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed simulation: {config_name} - {str(e)}")
            return {
                'status': 'error',
                'config_file': config_file,
                'config_name': config_name,
                'error': str(e),
                'model': 'unknown',
                'duration': duration
            }
    
    def run_experiment(self, parallel: bool = True) -> List[Dict]:
        """Run all simulations in the experiment."""
        config_files = self.get_config_files()
        
        if not config_files:
            print("No configuration files found!")
            return []
        
        print(f"\nStarting experiment: {self.experiment_name}")
        print(f"Found {len(config_files)} configurations")
        print(f"Parallel execution: {parallel}")
        print("-" * 50)
        
        start_time = time.time()
        
        if parallel:
            # Use ThreadPoolExecutor for parallel execution with progress tracking
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            # Create progress tracking
            progress_data = {}
            progress_lock = threading.Lock()
            
            def update_progress(config_file, message, percent):
                with progress_lock:
                    progress_data[config_file] = {'message': message, 'percent': percent}
                    # Print progress update
                    config_name = Path(config_file).stem
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {config_name}: {message} ({percent:.0f}%)")
            
            def run_with_progress(config_file):
                return self.run_single_simulation(
                    config_file, 
                    progress_callback=lambda msg, pct: update_progress(config_file, msg, pct)
                )
            
            with ThreadPoolExecutor(max_workers=min(len(config_files), 6)) as executor:
                # Submit all tasks
                future_to_config = {
                    executor.submit(run_with_progress, config_file): config_file 
                    for config_file in config_files
                }
                
                results = []
                completed = 0
                total = len(config_files)
                
                # Process completed tasks
                for future in as_completed(future_to_config):
                    config_file = future_to_config[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        
                        # Print completion status
                        status = "✓" if result['status'] == 'success' else "✗"
                        model = result.get('model', 'unknown')
                        duration = result.get('duration', 0)
                        print(f"{status} {result['config_name']} ({model}) - {duration:.1f}s [{completed}/{total}]")
                        
                    except Exception as e:
                        print(f"✗ {Path(config_file).stem} - Exception: {e}")
                        results.append({
                            'status': 'error',
                            'config_file': config_file,
                            'config_name': Path(config_file).stem,
                            'error': str(e),
                            'model': 'unknown',
                            'duration': 0
                        })
                        completed += 1
        else:
            # Sequential execution with progress
            results = []
            total = len(config_files)
            
            for i, config_file in enumerate(config_files, 1):
                config_name = Path(config_file).stem
                print(f"\n[{i}/{total}] Starting {config_name}")
                
                def progress_callback(message, percent):
                    print(f"  {message} ({percent:.0f}%)")
                
                result = self.run_single_simulation(config_file, progress_callback)
                results.append(result)
                
                status = "✓" if result['status'] == 'success' else "✗"
                duration = result.get('duration', 0)
                print(f"{status} Completed {config_name} - {duration:.1f}s")
        
        # Print summary
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        
        print("\n" + "=" * 50)
        print(f"Experiment completed: {self.experiment_name}")
        print(f"Total time: {total_time:.1f}s")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\nFailed simulations:")
            for result in results:
                if result['status'] == 'error':
                    print(f"  - {result['config_name']}: {result.get('error', 'Unknown error')}")
        
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
            duration_str = f"{result['duration']:.1f}s" if "duration" in result else "N/A"
            agent_model = result.get("model", "Unknown")
            
            table.add_row(
                f"[{status_color}]{status}[/]",
                result["config_name"],
                agent_model,
                duration_str
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
            console.print(f"\n⚠️  [bold red]{len(failed)}[/] simulation(s) failed. Check logs for details.")


@app.command(name="run")
def run_experiment(
    experiment_folder: str = typer.Argument(..., help="Path to experiment folder containing YAML configs"),
    sequential: bool = typer.Option(False, "--sequential", help="Run simulations sequentially instead of in parallel"),
    max_workers: int = typer.Option(3, "--max-workers", help="Maximum number of parallel workers"),
    validate_only: bool = typer.Option(False, "--validate", help="Only validate configs without running the experiment"),
    prompts_file: str = typer.Option("cesare/prompts-simulation-factory.yaml", "--prompts-file", help="Path to the simulation prompts YAML file")
):
    """Run a CESARE experiment with multiple models."""
    # Validate experiment folder
    if not Path(experiment_folder).exists():
        console.print(f"[bold red]Error:[/] Experiment folder '{experiment_folder}' does not exist")
        raise typer.Exit(code=1)
    
    # Create experiment runner
    runner = ExperimentRunner(
        experiment_folder=experiment_folder,
        max_workers=max_workers,
        prompts_file=prompts_file
    )
    
    try:
        # Get config files
        config_files = runner.get_config_files()
        
        # Print experiment info
        console.print(f"[bold green]Experiment:[/] {Path(experiment_folder).name}")
        console.print(f"[bold]Found [cyan]{len(config_files)}[/] configurations")
        console.print(f"[bold]Parallel execution:[/] {'[green]Yes[/]' if not sequential else '[yellow]No[/]'}")
        console.print(f"[bold]Max workers:[/] {max_workers if not sequential else 1}")
        
        # If validate only, check configs and exit
        if validate_only:
            with console.status("[bold green]Validating configs...[/]"):
                errors = []
                for config_file in config_files:
                    try:
                        with open(config_file) as f:
                            config = yaml.safe_load(f)
                        
                        # Validation for new flexible format only
                        if "models" not in config:
                            errors.append((config_file, "Missing 'models' section"))
                        else:
                            models = config["models"]
                            required_models = ["agent", "environment", "evaluator"]
                            missing_models = [m for m in required_models if m not in models]
                            if missing_models:
                                errors.append((config_file, f"Missing required models: {', '.join(missing_models)}"))
                            
                            # Validate model format (must have name and provider)
                            for model_key, model_config in models.items():
                                if not isinstance(model_config, dict):
                                    errors.append((config_file, f"Model '{model_key}' must be a dict with 'name' and 'provider' fields"))
                                else:
                                    if "name" not in model_config:
                                        errors.append((config_file, f"Model '{model_key}' missing 'name' field"))
                                    if "provider" not in model_config:
                                        errors.append((config_file, f"Model '{model_key}' missing 'provider' field"))
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
        with console.status("[bold green]Running experiment...[/]"):
            start_time = time.time()
            results = runner.run_experiment(parallel=not sequential)
            end_time = time.time()
        
        # Print summary 
        runner.print_summary(results)
        
        console.print(f"\nTotal experiment time: [bold cyan]{end_time - start_time:.1f}s[/]")
        
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
    table.add_column("Configs")
    table.add_column("Models")
    
    for folder in sorted(experiment_folders):
        name = os.path.basename(folder)
        configs = glob.glob(f"{folder}/*.yaml")
        
        # Extract unique models (new format only)
        models = set()
        for config_file in configs:
            try:
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                if "models" in config and "agent" in config["models"]:
                    agent_config = config["models"]["agent"]
                    # New format only: {name: "model_name", provider: "provider_name"}
                    models.add(agent_config.get('name', 'unknown'))
            except (KeyError, TypeError, yaml.YAMLError):
                pass
        
        table.add_row(
            name,
            str(len(configs)),
            ", ".join(sorted(models)) if models else "Unknown"
        )
    
    console.print("[bold]Available Experiments:[/]")
    console.print(table)
    console.print("\nRun an experiment with: [bold cyan]python -m cesare.main_experiment run <experiment_folder>[/]")


if __name__ == "__main__":
    app() 