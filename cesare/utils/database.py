import duckdb
import os
import json
import pandas as pd
import datetime
from typing import Dict, List
import hashlib


class SimulationDB:
    def __init__(self, db_path: str = "logs/simulations.duckdb"):
        """
        Initialize the simulation database.

        Args:
            db_path (str): Path to the DuckDB database file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect to DuckDB
        self.conn = duckdb.connect(db_path)

        # Initialize database schema
        self._init_schema()

    def _init_schema(self):
        """Initialize the database schema if tables don't exist."""
        # Simulations table - top level info about each simulation run
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                simulation_id VARCHAR PRIMARY KEY,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_steps INTEGER,
                total_instructions INTEGER,
                config JSON,
                metadata JSON
            )
        """)

        # History table - all history entries for all simulations
        self.conn.execute("""
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
        self.conn.execute("""
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
        self.conn.execute("""
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
    ) -> str:
        """
        Save a complete simulation run to the database.

        Args:
            history (List[Dict]): The simulation history
            evaluations (List[Dict], optional): List of ethical evaluations
            config (Dict, optional): The simulation configuration
            metrics (Dict, optional): Metrics from the simulation
            prompts (Dict, optional): Prompts used in the simulation

        Returns:
            str: The simulation ID
        """
        # Generate a unique simulation ID
        simulation_id = self._generate_id(f"sim_{datetime.datetime.now().isoformat()}")

        # Extract start and end time from history if available
        start_time = datetime.datetime.now()
        end_time = datetime.datetime.now()

        # Save simulation metadata
        metadata = {
            "metrics": metrics or {},
        }

        # Insert simulation record
        self.conn.execute(
            """
            INSERT INTO simulations 
            (simulation_id, start_time, end_time, total_steps, total_instructions, config, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                simulation_id,
                start_time,
                end_time,
                metrics.get("total_steps", 0) if metrics else 0,
                metrics.get("total_instructions", 0) if metrics else 0,
                json.dumps(config or {}),
                json.dumps(metadata),
            ),
        )

        # Save history entries
        if history:
            self._save_history(simulation_id, history)

        # Save evaluations if provided
        if evaluations:
            self._save_evaluations(simulation_id, evaluations, history)

        # Save prompts if provided
        if prompts:
            self._save_prompts(simulation_id, prompts)

        return simulation_id

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
            self.conn.execute("INSERT INTO history SELECT * FROM df")

    def _save_evaluations(
        self, simulation_id: str, evaluations: List[Dict], history: List[Dict]
    ):
        """Save evaluations to the database."""
        eval_data = []

        # Create a mapping from step to history_id for instructions
        instruction_map = {}
        for i, entry in enumerate(history):
            if entry.get("type") == "instruction":
                # Generate the same history_id as in _save_history
                history_id = self._generate_id(f"{simulation_id}_history_{i}")
                instruction_map[i] = history_id

        for i, eval_item in enumerate(evaluations):
            evaluation_id = self._generate_id(f"{simulation_id}_eval_{i}")

            # Get corresponding instruction ID
            step = eval_item.get("step", i)
            instruction_id = instruction_map.get(step, None)

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
            self.conn.execute("INSERT INTO evaluations SELECT * FROM df")

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
            self.conn.execute("INSERT INTO prompts SELECT * FROM df")

    def get_simulations(self) -> pd.DataFrame:
        """Get all simulations from the database."""
        return self.conn.execute("SELECT * FROM simulations").fetchdf()

    def get_simulation_history(self, simulation_id: str) -> pd.DataFrame:
        """Get history for a specific simulation."""
        return self.conn.execute(
            "SELECT * FROM history WHERE simulation_id = ? ORDER BY step",
            [simulation_id],
        ).fetchdf()

    def get_simulation_evaluations(self, simulation_id: str) -> pd.DataFrame:
        """Get evaluations for a specific simulation."""
        return self.conn.execute(
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

        return self.conn.execute(f"""
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

        return self.conn.execute(f"""
            SELECT h.*, e.action, e.raw_evaluation
            FROM history h
            JOIN evaluations e ON h.history_id = e.instruction_id
            WHERE e.{violation_type} = true
            ORDER BY h.simulation_id, h.step
        """).fetchdf()

    def get_violation_counts(self) -> pd.DataFrame:
        """Get counts of each violation type across all simulations."""
        return self.conn.execute("""
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
        self.conn.close()

    def _generate_id(self, text: str) -> str:
        """Generate a deterministic ID from text."""
        return hashlib.md5(text.encode()).hexdigest()
