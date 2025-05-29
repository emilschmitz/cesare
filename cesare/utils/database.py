import duckdb
import os
import json
import pandas as pd
import datetime
from typing import Dict, List
import hashlib
import time
import threading
import fcntl
import random
from contextlib import contextmanager


class SimulationDB:
    def __init__(self, db_path: str = "logs/simulations.duckdb"):
        """
        Initialize the simulation database.

        Args:
            db_path (str): Path to the DuckDB database file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.lock_path = db_path + ".lock"
        self._local = threading.local()

        # Initialize database schema with migration
        self._init_schema_with_migration()

    def _get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = duckdb.connect(self.db_path)
        return self._local.conn

    @contextmanager
    def _file_lock(self, timeout=60):
        """Context manager for file-based locking with better error handling."""
        lock_file = None
        acquired = False
        try:
            # Create lock file
            lock_file = open(self.lock_path, 'w')
            lock_file.write(f"{os.getpid()}\n")
            lock_file.flush()
            
            # Try to acquire lock with timeout and random jitter
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    yield
                    return
                except (IOError, OSError):
                    # Random jitter between 50ms and 500ms
                    jitter = random.uniform(0.05, 0.5)
                    time.sleep(jitter)
            
            raise TimeoutError(f"Could not acquire database lock within {timeout} seconds")
            
        finally:
            if lock_file:
                try:
                    if acquired:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    # Only remove lock file if we created it
                    if acquired and os.path.exists(self.lock_path):
                        os.remove(self.lock_path)
                except:
                    pass

    def _execute_with_retry(self, query, params=None, max_retries=5):
        """Execute a query with retry logic and exponential backoff with jitter."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                conn = self._get_connection()
                if params:
                    return conn.execute(query, params)
                else:
                    return conn.execute(query)
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check if it's a retryable error
                if any(keyword in error_str for keyword in [
                    "database is locked", "conflict", "busy", "io error", 
                    "could not set lock", "conflicting lock"
                ]):
                    if attempt == max_retries - 1:
                        break
                    
                    # Exponential backoff with random jitter
                    base_delay = 0.1 * (2 ** attempt)
                    jitter = random.uniform(0.5, 1.5)
                    delay = base_delay * jitter
                    time.sleep(delay)
                    
                    # Close and recreate connection on lock errors
                    if hasattr(self._local, 'conn') and self._local.conn:
                        try:
                            self._local.conn.close()
                        except:
                            pass
                        self._local.conn = None
                    continue
                else:
                    # Non-retryable error, raise immediately
                    raise
        
        # If we get here, all retries failed
        raise last_exception

    def _init_schema_with_migration(self):
        """Initialize the database schema with migration support."""
        with self._file_lock(timeout=30):
            conn = self._get_connection()
            
            # Check if we need to migrate existing database
            try:
                # Try to query simulations table to see if experiment_id exists
                conn.execute("SELECT experiment_id FROM simulations LIMIT 1")
                schema_current = True
            except:
                schema_current = False
            
            if not schema_current:
                # Drop and recreate tables to ensure proper schema
                try:
                    conn.execute("DROP TABLE IF EXISTS evaluations")
                    conn.execute("DROP TABLE IF EXISTS history") 
                    conn.execute("DROP TABLE IF EXISTS prompts")
                    conn.execute("DROP TABLE IF EXISTS simulations")
                    conn.execute("DROP TABLE IF EXISTS experiments")
                except:
                    pass
            
            self._init_schema()

    def _init_schema(self):
        """Initialize the database schema if tables don't exist."""
        conn = self._get_connection()
        
        # Experiments table - top level info about experiments
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id VARCHAR PRIMARY KEY,
                experiment_name VARCHAR,
                description TEXT,
                created_time TIMESTAMP,
                total_simulations INTEGER DEFAULT 0,
                completed_simulations INTEGER DEFAULT 0,
                metadata JSON
            )
        """)

        # Simulations table - top level info about each simulation run
        conn.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                simulation_id VARCHAR PRIMARY KEY,
                experiment_id VARCHAR,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_steps INTEGER,
                total_instructions INTEGER,
                config JSON,
                metadata JSON
            )
        """)

        # History table - all history entries for all simulations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                history_id VARCHAR PRIMARY KEY,
                simulation_id VARCHAR,
                step INTEGER,
                entry_type VARCHAR,
                content TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
            )
        """)

        # Evaluations table - all ethical evaluations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                evaluation_id VARCHAR PRIMARY KEY,
                simulation_id VARCHAR,
                step INTEGER,
                instruction_id VARCHAR,
                action TEXT,
                raw_evaluation JSON,
                killing BOOLEAN,
                physical_harm BOOLEAN,
                non_physical_harm BOOLEAN,
                intending_harm BOOLEAN,
                deception BOOLEAN,
                manipulation BOOLEAN,
                betrayal BOOLEAN,
                stealing BOOLEAN,
                trespassing BOOLEAN,
                spying BOOLEAN,
                vandalism BOOLEAN,
                unfairness BOOLEAN,
                other BOOLEAN,
                timestamp TIMESTAMP,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id),
                FOREIGN KEY (instruction_id) REFERENCES history(history_id)
            )
        """)

        # Prompts table - store prompts used in each simulation
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                prompt_id VARCHAR PRIMARY KEY,
                simulation_id VARCHAR,
                prompt_type VARCHAR,
                prompt_content TEXT,
                prompt_file VARCHAR,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
            )
        """)

    def save_simulation(
        self,
        history: List[Dict],
        evaluations: List[Dict] = None,
        config: Dict = None,
        metrics: Dict = None,
        prompts: Dict = None,
        experiment_name: str = None,
        ai_key: str = "instruction",
    ) -> str:
        """
        Save a complete simulation run to the database.

        Args:
            history (List[Dict]): The simulation history
            evaluations (List[Dict], optional): List of ethical evaluations
            config (Dict, optional): The simulation configuration
            metrics (Dict, optional): Metrics from the simulation
            prompts (Dict, optional): Prompts used in the simulation
            experiment_name (str, optional): Name of the experiment this simulation belongs to
            ai_key (str, optional): The key used for AI entries in history (default: "instruction")

        Returns:
            str: The simulation ID
        """
        # Use file lock for the entire save operation to prevent conflicts
        with self._file_lock():
            # Generate a unique simulation ID
            simulation_id = self._generate_id(f"sim_{datetime.datetime.now().isoformat()}_{random.randint(1000, 9999)}")

            # Handle experiment
            experiment_id = None
            if experiment_name:
                experiment_id = self._ensure_experiment_exists(experiment_name, config)

            # Extract start and end time from history if available
            start_time = datetime.datetime.now()
            end_time = datetime.datetime.now()

            # Save simulation metadata
            metadata = {
                "metrics": metrics or {},
            }

            # Insert simulation record
            self._execute_with_retry(
                """
                INSERT INTO simulations 
                (simulation_id, experiment_id, start_time, end_time, total_steps, total_instructions, config, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    simulation_id,
                    experiment_id,
                    start_time,
                    end_time,
                    metrics.get("total_steps", 0) if metrics else 0,
                    metrics.get("total_instructions", 0) if metrics else 0,
                    json.dumps(config or {}),
                    json.dumps(metadata),
                ),
            )

            # Update experiment completion count
            if experiment_id:
                self._execute_with_retry(
                    """
                    UPDATE experiments 
                    SET completed_simulations = completed_simulations + 1
                    WHERE experiment_id = ?
                    """,
                    (experiment_id,)
                )

            # Save history entries
            if history:
                self._save_history(simulation_id, history)

            # Save evaluations if provided
            if evaluations:
                self._save_evaluations(simulation_id, evaluations, history, ai_key)

            # Save prompts if provided
            if prompts:
                self._save_prompts(simulation_id, prompts)

            return simulation_id

    def _ensure_experiment_exists(self, experiment_name: str, config: Dict = None) -> str:
        """
        Ensure an experiment exists in the database, create if it doesn't.
        Note: This method assumes it's called within a file lock context.
        
        Args:
            experiment_name (str): Name of the experiment
            config (Dict, optional): Configuration to extract metadata from
            
        Returns:
            str: The experiment ID
        """
        experiment_id = self._generate_id(f"exp_{experiment_name}")
        
        # Extract metadata from config if available
        metadata = {}
        if config:
            metadata = {
                "provider": config.get("provider"),
                "environment_model": config.get("models", {}).get("environment"),
                "evaluator_model": config.get("models", {}).get("evaluator"),
                "max_steps": config.get("simulation", {}).get("max_steps"),
            }
        
        # Use INSERT OR IGNORE to handle concurrent creation
        self._execute_with_retry(
            """
            INSERT OR IGNORE INTO experiments 
            (experiment_id, experiment_name, description, created_time, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                experiment_id,
                experiment_name,
                f"Experiment: {experiment_name}",
                datetime.datetime.now(),
                json.dumps(metadata)
            )
        )
        
        return experiment_id

    def _save_history(self, simulation_id: str, history: List[Dict]):
        """Save history entries to the database."""
        history_data = []

        for i, entry in enumerate(history):
            history_id = self._generate_id(f"{simulation_id}_history_{i}")

            history_data.append(
                {
                    "history_id": history_id,
                    "simulation_id": simulation_id,
                    "step": i,
                    "entry_type": entry.get("type", "unknown"),
                    "content": entry.get("content", ""),
                    "timestamp": datetime.datetime.now(),
                }
            )

        # Convert to DataFrame and insert
        if history_data:
            df = pd.DataFrame(history_data)
            conn = self._get_connection()
            conn.register('df_temp', df)
            self._execute_with_retry("INSERT INTO history SELECT * FROM df_temp")
            conn.unregister('df_temp')

    def _save_evaluations(
        self, simulation_id: str, evaluations: List[Dict], history: List[Dict], ai_key: str = "instruction"
    ):
        """Save evaluations to the database."""
        eval_data = []

        # Create a mapping from step to history_id for AI entries (instructions/responses)
        ai_entry_map = {}
        for i, entry in enumerate(history):
            if entry.get("type") == ai_key:
                # Generate the same history_id as in _save_history
                history_id = self._generate_id(f"{simulation_id}_history_{i}")
                ai_entry_map[i] = history_id

        for i, eval_item in enumerate(evaluations):
            evaluation_id = self._generate_id(f"{simulation_id}_eval_{i}")

            # Get corresponding AI entry ID
            step = eval_item.get("step", i)
            instruction_id = ai_entry_map.get(step, None)

            # Extract labels
            labels = eval_item.get("labels", {})

            eval_data.append(
                {
                    "evaluation_id": evaluation_id,
                    "simulation_id": simulation_id,
                    "step": step,
                    "instruction_id": instruction_id,
                    "action": eval_item.get("action", ""),
                    "raw_evaluation": json.dumps(eval_item),
                    "killing": bool(labels.get("killing", 0)),
                    "physical_harm": bool(labels.get("physical_harm", 0)),
                    "non_physical_harm": bool(labels.get("non_physical_harm", 0)),
                    "intending_harm": bool(labels.get("intending_harm", 0)),
                    "deception": bool(labels.get("deception", 0)),
                    "manipulation": bool(labels.get("manipulation", 0)),
                    "betrayal": bool(labels.get("betrayal", 0)),
                    "stealing": bool(labels.get("stealing", 0)),
                    "trespassing": bool(labels.get("trespassing", 0)),
                    "spying": bool(labels.get("spying", 0)),
                    "vandalism": bool(labels.get("vandalism", 0)),
                    "unfairness": bool(labels.get("unfairness", 0)),
                    "other": bool(labels.get("other", 0)),
                    "timestamp": datetime.datetime.now(),
                }
            )

        # Convert to DataFrame and insert
        if eval_data:
            df = pd.DataFrame(eval_data)
            conn = self._get_connection()
            conn.register('df_temp', df)
            self._execute_with_retry("INSERT INTO evaluations SELECT * FROM df_temp")
            conn.unregister('df_temp')

    def _save_prompts(self, simulation_id: str, prompts: Dict):
        """Save prompts to the database."""
        prompt_data = []

        for prompt_type, content in prompts.items():
            prompt_id = self._generate_id(f"{simulation_id}_prompt_{prompt_type}")

            prompt_data.append(
                {
                    "prompt_id": prompt_id,
                    "simulation_id": simulation_id,
                    "prompt_type": prompt_type,
                    "prompt_content": content,
                    "prompt_file": f"cesare/prompts-{prompt_type}.yaml",
                }
            )

        # Convert to DataFrame and insert
        if prompt_data:
            df = pd.DataFrame(prompt_data)
            conn = self._get_connection()
            conn.register('df_temp', df)
            self._execute_with_retry("INSERT INTO prompts SELECT * FROM df_temp")
            conn.unregister('df_temp')

    def get_simulations(self) -> pd.DataFrame:
        """Get all simulations from the database."""
        return self._execute_with_retry("SELECT * FROM simulations").fetchdf()

    def get_simulation_history(self, simulation_id: str) -> pd.DataFrame:
        """Get history for a specific simulation."""
        return self._execute_with_retry(
            "SELECT * FROM history WHERE simulation_id = ? ORDER BY step",
            [simulation_id],
        ).fetchdf()

    def get_simulation_evaluations(self, simulation_id: str) -> pd.DataFrame:
        """Get evaluations for a specific simulation."""
        return self._execute_with_retry(
            "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY step",
            [simulation_id],
        ).fetchdf()

    def get_simulations_with_violation(self, violation_type: str) -> pd.DataFrame:
        """Get all simulations containing a specific violation type."""
        if violation_type not in [
            "killing",
            "physical_harm",
            "non_physical_harm",
            "intending_harm",
            "deception",
            "manipulation",
            "betrayal",
            "stealing",
            "trespassing",
            "spying",
            "vandalism",
            "unfairness",
            "other",
        ]:
            raise ValueError(f"Invalid violation type: {violation_type}")

        return self._execute_with_retry(f"""
            SELECT DISTINCT s.* 
            FROM simulations s
            JOIN evaluations e ON s.simulation_id = e.simulation_id
            WHERE e.{violation_type} = true
        """).fetchdf()

    def get_instructions_with_violation(self, violation_type: str) -> pd.DataFrame:
        """Get all instructions with a specific violation type."""
        if violation_type not in [
            "killing",
            "physical_harm",
            "non_physical_harm",
            "intending_harm",
            "deception",
            "manipulation",
            "betrayal",
            "stealing",
            "trespassing",
            "spying",
            "vandalism",
            "unfairness",
            "other",
        ]:
            raise ValueError(f"Invalid violation type: {violation_type}")

        return self._execute_with_retry(f"""
            SELECT h.*, e.action, e.raw_evaluation
            FROM history h
            JOIN evaluations e ON h.history_id = e.instruction_id
            WHERE e.{violation_type} = true
            ORDER BY h.simulation_id, h.step
        """).fetchdf()

    def get_violation_counts(self) -> pd.DataFrame:
        """Get counts of each violation type across all simulations."""
        return self._execute_with_retry("""
            SELECT 
                SUM(killing) as killing_count,
                SUM(physical_harm) as physical_harm_count,
                SUM(non_physical_harm) as non_physical_harm_count,
                SUM(intending_harm) as intending_harm_count,
                SUM(deception) as deception_count,
                SUM(manipulation) as manipulation_count,
                SUM(betrayal) as betrayal_count,
                SUM(stealing) as stealing_count,
                SUM(trespassing) as trespassing_count,
                SUM(spying) as spying_count,
                SUM(vandalism) as vandalism_count,
                SUM(unfairness) as unfairness_count,
                SUM(other) as other_count
            FROM evaluations
        """).fetchdf()

    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def _generate_id(self, text: str) -> str:
        """Generate a deterministic ID from text."""
        return hashlib.md5(text.encode()).hexdigest()

    def get_experiments(self) -> pd.DataFrame:
        """Get all experiments from the database."""
        return self._execute_with_retry("""
            SELECT 
                e.*,
                COUNT(s.simulation_id) as actual_simulations
            FROM experiments e
            LEFT JOIN simulations s ON e.experiment_id = s.experiment_id
            GROUP BY e.experiment_id, e.experiment_name, e.description, e.created_time, e.total_simulations, e.completed_simulations, e.metadata
            ORDER BY e.created_time DESC
        """).fetchdf()

    def get_experiment_simulations(self, experiment_name: str) -> pd.DataFrame:
        """Get all simulations for a specific experiment."""
        return self._execute_with_retry("""
            SELECT s.*, e.experiment_name
            FROM simulations s
            JOIN experiments e ON s.experiment_id = e.experiment_id
            WHERE e.experiment_name = ?
            ORDER BY s.start_time DESC
        """, (experiment_name,)).fetchdf()
