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

# Global lock for experiment creation to prevent concurrent schema conflicts
_experiment_creation_lock = threading.Lock()

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
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = duckdb.connect(self.db_path)
        return self._local.conn

    @contextmanager
    def _file_lock(self, timeout=60):
        """Context manager for file-based locking with better error handling."""
        lock_file = None
        acquired = False
        try:
            # Create lock file
            lock_file = open(self.lock_path, "w")
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

            raise TimeoutError(
                f"Could not acquire database lock within {timeout} seconds"
            )

        finally:
            if lock_file:
                try:
                    if acquired:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    # Only remove lock file if we created it
                    if acquired and os.path.exists(self.lock_path):
                        os.remove(self.lock_path)
                except OSError:
                    pass

    def _execute_with_retry(self, query, params=None, max_retries=500):
        """Execute a query with retry logic and exponential backoff with jitter."""
        last_exception = None
        query_type = query.strip().split()[0].upper() if query.strip() else "UNKNOWN"

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

                # Check if it's a retryable error - enhanced for DuckDB conflicts
                if any(
                    keyword in error_str
                    for keyword in [
                        "database is locked",
                        "conflict",
                        "busy",
                        "io error",
                        "could not set lock",
                        "conflicting lock",
                        "write-write conflict",
                        "catalog write-write conflict",
                        "transactioncontext error",
                        "transaction conflict",
                        "alter with",
                        "concurrent modification",
                        "schema modification",
                    ]
                ):
                    if attempt == max_retries - 1:
                        # Log the final failure with details
                        print(f"DB RETRY FAILED: {query_type} query failed after {max_retries} attempts")
                        print(f"Query: {query[:100]}...")
                        print(f"Error: {str(e)}")
                        break

                    # Log retry attempts for conflicts (but not too frequently)
                    if attempt % 20 == 0 and attempt > 0:
                        print(f"DB RETRY: {query_type} attempt {attempt+1}/{max_retries} - {str(e)[:50]}...")

                    # Exponential backoff with random jitter - longer delays for conflicts
                    base_delay = 0.5 * (2**min(attempt, 8))  # Cap exponential growth at 2^8
                    jitter = random.uniform(0.8, 3.0)  # Increased jitter range
                    delay = min(base_delay * jitter, 30.0)  # Cap at 30 seconds
                    time.sleep(delay)

                    # Close and recreate connection on lock errors
                    if hasattr(self._local, "conn") and self._local.conn:
                        try:
                            self._local.conn.close()
                        except Exception:
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
            except Exception:
                schema_current = False

            if not schema_current:
                # Drop and recreate tables to ensure proper schema
                try:
                    conn.execute("DROP TABLE IF EXISTS evaluations")
                    conn.execute("DROP TABLE IF EXISTS history")
                    conn.execute("DROP TABLE IF EXISTS prompts")
                    conn.execute("DROP TABLE IF EXISTS simulations")
                    conn.execute("DROP TABLE IF EXISTS experiments")
                except Exception:
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
                metadata JSON,
                ai_key VARCHAR DEFAULT 'instruction',
                environment_key VARCHAR DEFAULT 'environment'
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
                evaluation_type VARCHAR,
                action TEXT,
                raw_evaluation JSON,
                timestamp TIMESTAMP,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id),
                FOREIGN KEY (instruction_id) REFERENCES history(history_id)
            )
        """)

        # Ethical violations table - specific to ethical violations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ethical_violations (
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

        # Power seeking table - specific to power seeking evaluations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS power_seeking (
                evaluation_id VARCHAR PRIMARY KEY,
                simulation_id VARCHAR,
                step INTEGER,
                instruction_id VARCHAR,
                action TEXT,
                raw_evaluation JSON,
                physical_power BOOLEAN,
                economic_power BOOLEAN,
                informational_power BOOLEAN,
                social_power BOOLEAN,
                other_power BOOLEAN,
                timestamp TIMESTAMP,
                FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id),
                FOREIGN KEY (instruction_id) REFERENCES history(history_id)
            )
        """)

        # Disutility table - specific to disutility evaluations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS disutility (
                evaluation_id VARCHAR PRIMARY KEY,
                simulation_id VARCHAR,
                step INTEGER,
                instruction_id VARCHAR,
                action TEXT,
                raw_evaluation JSON,
                utility_change INTEGER,
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
        environment_key: str = "environment",
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
            environment_key (str, optional): The key used for environment entries in history (default: "environment")

        Returns:
            str: The simulation ID
        """
        # Use file lock for the entire save operation to prevent conflicts
        with self._file_lock():
            # Generate a unique simulation ID
            simulation_id = self._generate_id(
                f"sim_{datetime.datetime.now().isoformat()}_{random.randint(1000, 9999)}"
            )

            # Handle experiment
            experiment_id = None
            if experiment_name:
                try:
                    experiment_id = self._ensure_experiment_exists(experiment_name, config)
                except Exception as e:
                    print(f"DB CONFLICT: Failed to ensure experiment exists for {experiment_name}: {e}")
                    raise

            # Extract start and end time from history if available
            start_time = datetime.datetime.now()
            end_time = datetime.datetime.now()

            # Save simulation metadata
            metadata = {
                "metrics": metrics or {},
            }

            # Insert simulation record
            try:
                self._execute_with_retry(
                    """
                    INSERT INTO simulations 
                    (simulation_id, experiment_id, start_time, end_time, total_steps, total_instructions, config, metadata, ai_key, environment_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        ai_key,
                        environment_key,
                    ),
                )
            except Exception as e:
                print(f"DB CONFLICT: Failed to insert simulation {simulation_id}: {e}")
                raise

            # Update experiment completion count
            if experiment_id:
                try:
                    self._execute_with_retry(
                        """
                        UPDATE experiments 
                        SET completed_simulations = completed_simulations + 1
                        WHERE experiment_id = ?
                        """,
                        (experiment_id,),
                    )
                except Exception as e:
                    print(f"DB CONFLICT: Failed to update experiment completion count for {experiment_name}: {e}")
                    raise

            # Save history entries
            if history:
                try:
                    self._save_history(simulation_id, history)
                except Exception as e:
                    print(f"DB CONFLICT: Failed to save history for {simulation_id}: {e}")
                    raise

            # Save evaluations if provided
            if evaluations:
                try:
                    self._save_evaluations(simulation_id, evaluations, history, ai_key)
                except Exception as e:
                    print(f"DB CONFLICT: Failed to save evaluations for {simulation_id}: {e}")
                    raise

            # Save prompts if provided
            if prompts:
                try:
                    self._save_prompts(simulation_id, prompts)
                except Exception as e:
                    print(f"DB CONFLICT: Failed to save prompts for {simulation_id}: {e}")
                    raise

            return simulation_id

    def _ensure_experiment_exists(
        self, experiment_name: str, config: Dict = None
    ) -> str:
        """
        Ensure an experiment exists in the database, create if it doesn't.
        Uses global lock to prevent concurrent creation conflicts.

        Args:
            experiment_name (str): Name of the experiment
            config (Dict, optional): Configuration to extract metadata from

        Returns:
            str: The experiment ID
        """
        experiment_id = self._generate_id(f"exp_{experiment_name}")

        # Use global lock to prevent concurrent experiment creation
        with _experiment_creation_lock:
            # First, check if experiment already exists
            try:
                existing = self._execute_with_retry(
                    "SELECT experiment_id FROM experiments WHERE experiment_name = ?",
                    (experiment_name,)
                ).fetchall()
                
                if existing:
                    return existing[0][0]
            except Exception as e:
                print(f"DB CONFLICT: Error checking existing experiment {experiment_name}: {e}")
                # Continue to try creating it

            # Extract metadata from config if available
            metadata = {}
            if config:
                metadata = {
                    "provider": config.get("provider"),
                    "environment_model": config.get("models", {}).get("environment"),
                    "evaluator_model": config.get("models", {}).get("evaluator"),
                    "max_steps": config.get("simulation", {}).get("max_steps"),
                }

            # Try to create the experiment with higher retry count for this critical operation
            try:
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
                        json.dumps(metadata),
                    ),
                    max_retries=800  # Even higher retry count for experiment creation
                )
            except Exception as e:
                print(f"DB CONFLICT: Failed to create experiment {experiment_name} after 800 retries: {e}")
                # Try one more time to get the experiment ID in case another thread created it
                try:
                    existing = self._execute_with_retry(
                        "SELECT experiment_id FROM experiments WHERE experiment_name = ?",
                        (experiment_name,)
                    ).fetchall()
                    
                    if existing:
                        return existing[0][0]
                except Exception:
                    pass
                
                # If all else fails, raise the original error
                raise

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
            conn.register("df_temp", df)
            self._execute_with_retry("INSERT INTO history SELECT * FROM df_temp")
            conn.unregister("df_temp")

    def _save_evaluations(
        self,
        simulation_id: str,
        evaluations: List[Dict],
        history: List[Dict],
        ai_key: str = "instruction",
    ):
        """Save evaluations to the appropriate tables based on evaluation type."""
        # Create a mapping from step to history_id for AI entries (instructions/responses)
        ai_entry_map = {}
        for i, entry in enumerate(history):
            if entry.get("type") == ai_key:
                # Generate the same history_id as in _save_history
                history_id = self._generate_id(f"{simulation_id}_history_{i}")
                ai_entry_map[i] = history_id

        # Group evaluations by type
        ethical_violations_data = []
        power_seeking_data = []
        disutility_data = []
        general_evaluations_data = []

        for i, eval_item in enumerate(evaluations):
            evaluation_id = self._generate_id(f"{simulation_id}_eval_{i}")
            evaluation_type = eval_item.get("evaluation_type", "unknown")

            # Get corresponding AI entry ID
            step = eval_item.get("step", i)
            instruction_id = ai_entry_map.get(step, None)

            # Common data for all evaluation types
            common_data = {
                "evaluation_id": evaluation_id,
                "simulation_id": simulation_id,
                "step": step,
                "instruction_id": instruction_id,
                "action": eval_item.get("action", ""),
                "raw_evaluation": json.dumps(eval_item),
                "timestamp": datetime.datetime.now(),
            }

            # Add to general evaluations table
            general_evaluations_data.append(
                {
                    **common_data,
                    "evaluation_type": evaluation_type,
                }
            )

            # Handle specific evaluation types
            if evaluation_type == "ethical_violations":
                labels = eval_item.get("labels", {})
                ethical_violations_data.append(
                    {
                        **common_data,
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
                    }
                )

            elif evaluation_type == "power_seeking":
                labels = eval_item.get("labels", {})
                power_seeking_data.append(
                    {
                        **common_data,
                        "physical_power": bool(labels.get("physical_power", 0)),
                        "economic_power": bool(labels.get("economic_power", 0)),
                        "informational_power": bool(
                            labels.get("informational_power", 0)
                        ),
                        "social_power": bool(labels.get("social_power", 0)),
                        "other_power": bool(labels.get("other_power", 0)),
                    }
                )

            elif evaluation_type == "disutility":
                disutility_data.append(
                    {
                        **common_data,
                        "utility_change": int(eval_item.get("utility_change", 0)),
                    }
                )

        # Insert data into respective tables
        conn = self._get_connection()

        # General evaluations table
        if general_evaluations_data:
            df = pd.DataFrame(general_evaluations_data)
            # Ensure column order matches table schema
            df = df[
                [
                    "evaluation_id",
                    "simulation_id",
                    "step",
                    "instruction_id",
                    "evaluation_type",
                    "action",
                    "raw_evaluation",
                    "timestamp",
                ]
            ]
            conn.register("df_evaluations", df)
            self._execute_with_retry(
                "INSERT INTO evaluations SELECT * FROM df_evaluations"
            )
            conn.unregister("df_evaluations")

        # Ethical violations table
        if ethical_violations_data:
            df = pd.DataFrame(ethical_violations_data)
            # Ensure column order matches table schema
            df = df[
                [
                    "evaluation_id",
                    "simulation_id",
                    "step",
                    "instruction_id",
                    "action",
                    "raw_evaluation",
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
                    "timestamp",
                ]
            ]
            conn.register("df_ethical", df)
            self._execute_with_retry(
                "INSERT INTO ethical_violations SELECT * FROM df_ethical"
            )
            conn.unregister("df_ethical")

        # Power seeking table
        if power_seeking_data:
            df = pd.DataFrame(power_seeking_data)
            # Ensure column order matches table schema
            df = df[
                [
                    "evaluation_id",
                    "simulation_id",
                    "step",
                    "instruction_id",
                    "action",
                    "raw_evaluation",
                    "physical_power",
                    "economic_power",
                    "informational_power",
                    "social_power",
                    "other_power",
                    "timestamp",
                ]
            ]
            conn.register("df_power", df)
            self._execute_with_retry("INSERT INTO power_seeking SELECT * FROM df_power")
            conn.unregister("df_power")

        # Disutility table
        if disutility_data:
            df = pd.DataFrame(disutility_data)
            # Ensure column order matches table schema
            df = df[
                [
                    "evaluation_id",
                    "simulation_id",
                    "step",
                    "instruction_id",
                    "action",
                    "raw_evaluation",
                    "utility_change",
                    "timestamp",
                ]
            ]
            conn.register("df_disutility", df)
            self._execute_with_retry(
                "INSERT INTO disutility SELECT * FROM df_disutility"
            )
            conn.unregister("df_disutility")

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
            conn.register("df_temp", df)
            self._execute_with_retry("INSERT INTO prompts SELECT * FROM df_temp")
            conn.unregister("df_temp")

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

    def get_simulation_ethical_violations(self, simulation_id: str) -> pd.DataFrame:
        """Get ethical violations evaluations for a specific simulation."""
        return self._execute_with_retry(
            "SELECT * FROM ethical_violations WHERE simulation_id = ? ORDER BY step",
            [simulation_id],
        ).fetchdf()

    def get_simulation_power_seeking(self, simulation_id: str) -> pd.DataFrame:
        """Get power seeking evaluations for a specific simulation."""
        return self._execute_with_retry(
            "SELECT * FROM power_seeking WHERE simulation_id = ? ORDER BY step",
            [simulation_id],
        ).fetchdf()

    def get_simulation_disutility(self, simulation_id: str) -> pd.DataFrame:
        """Get disutility evaluations for a specific simulation."""
        return self._execute_with_retry(
            "SELECT * FROM disutility WHERE simulation_id = ? ORDER BY step",
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
            JOIN ethical_violations e ON s.simulation_id = e.simulation_id
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
            JOIN ethical_violations e ON h.history_id = e.instruction_id
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
            FROM ethical_violations
        """).fetchdf()

    def close(self):
        """Close the database connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
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
        return self._execute_with_retry(
            """
            SELECT s.*, e.experiment_name
            FROM simulations s
            JOIN experiments e ON s.experiment_id = e.experiment_id
            WHERE e.experiment_name = ?
            ORDER BY s.start_time DESC
        """,
            (experiment_name,),
        ).fetchdf()

    def delete_experiment(self, experiment_name: str) -> bool:
        """
        Delete an experiment and all its associated data from the database.
        
        Args:
            experiment_name (str): Name of the experiment to delete
            
        Returns:
            bool: True if experiment was found and deleted, False if not found
        """
        with self._file_lock(timeout=60):
            try:
                # First check if experiment exists
                experiments = self._execute_with_retry(
                    "SELECT experiment_id FROM experiments WHERE experiment_name = ?",
                    (experiment_name,)
                ).fetchall()
                
                if not experiments:
                    return False
                
                experiment_id = experiments[0][0]
                
                # Get all simulation IDs for this experiment
                simulations = self._execute_with_retry(
                    "SELECT simulation_id FROM simulations WHERE experiment_id = ?",
                    (experiment_id,)
                ).fetchall()
                
                simulation_ids = [sim[0] for sim in simulations]
                
                # Delete in reverse order of dependencies
                for sim_id in simulation_ids:
                    # Delete evaluations
                    self._execute_with_retry(
                        "DELETE FROM evaluations WHERE simulation_id = ?",
                        (sim_id,)
                    )
                    
                    # Delete ethical violations
                    self._execute_with_retry(
                        "DELETE FROM ethical_violations WHERE simulation_id = ?",
                        (sim_id,)
                    )
                    
                    # Delete power seeking
                    self._execute_with_retry(
                        "DELETE FROM power_seeking WHERE simulation_id = ?",
                        (sim_id,)
                    )
                    
                    # Delete disutility
                    self._execute_with_retry(
                        "DELETE FROM disutility WHERE simulation_id = ?",
                        (sim_id,)
                    )
                    
                    # Delete history
                    self._execute_with_retry(
                        "DELETE FROM history WHERE simulation_id = ?",
                        (sim_id,)
                    )
                    
                    # Delete prompts
                    self._execute_with_retry(
                        "DELETE FROM prompts WHERE simulation_id = ?",
                        (sim_id,)
                    )
                
                # Delete simulations
                self._execute_with_retry(
                    "DELETE FROM simulations WHERE experiment_id = ?",
                    (experiment_id,)
                )
                
                # Delete experiment
                self._execute_with_retry(
                    "DELETE FROM experiments WHERE experiment_id = ?",
                    (experiment_id,)
                )
                
                return True
                
            except Exception as e:
                print(f"Error deleting experiment {experiment_name}: {e}")
                return False
