"""
Test script for the DuckDB integration.

This script creates a simple simulation and saves it to the database.
"""

from utils.database import SimulationDB
import datetime


def create_sample_data():
    """Create sample data for testing."""
    # Sample history
    history = [
        {"type": "start_prompt", "content": "This is a test prompt"},
        {
            "type": "instruction",
            "content": "2023-05-01T10:00:00 This is a test instruction with deception",
        },
        {
            "type": "environment",
            "content": "2023-05-01T10:01:00 This is a test environment response",
        },
        {
            "type": "instruction",
            "content": "2023-05-01T10:02:00 This is another test instruction with physical harm",
        },
        {
            "type": "environment",
            "content": "2023-05-01T10:03:00 This is another test environment response",
        },
    ]

    # Sample evaluations
    evaluations = [
        {
            "step": 1,
            "action": "The AI system instructs with deception",
            "labels": {
                "killing": 0,
                "physical_harm": 0,
                "non_physical_harm": 0,
                "intending_harm": 0,
                "deception": 1,
                "manipulation": 0,
                "betrayal": 0,
                "stealing": 0,
                "trespassing": 0,
                "spying": 0,
                "vandalism": 0,
                "unfairness": 0,
                "other": 0,
            },
            "timestamp": datetime.datetime.now().isoformat(),
        },
        {
            "step": 3,
            "action": "The AI system instructs with physical harm",
            "labels": {
                "killing": 0,
                "physical_harm": 1,
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
            },
            "timestamp": datetime.datetime.now().isoformat(),
        },
    ]

    # Sample config
    config = {
        "models": {"agent": "test-model", "environment": "test-model"},
        "simulation": {"max_steps": 5},
        "evaluation": {"enabled": True},
    }

    # Sample metrics
    metrics = {
        "total_instructions": 2,
        "total_steps": 2,
        "ethical_violations": {"deception": 1, "physical_harm": 1},
    }

    # Sample prompts
    prompts = {
        "simulation": {
            "instruction_prompt": "This is a test instruction prompt",
            "environment_prompt": "This is a test environment prompt",
        },
        "evaluation": {
            "ethical_violations": "This is a test ethical violations prompt"
        },
    }

    return history, evaluations, config, metrics, prompts


def main():
    """Main function to test the database."""
    print("Initializing database...")
    db = SimulationDB("logs/test_simulations.duckdb")

    print("Creating sample data...")
    history, evaluations, config, metrics, prompts = create_sample_data()

    print("Saving to database...")
    simulation_id = db.save_simulation(
        history=history,
        evaluations=evaluations,
        config=config,
        metrics=metrics,
        prompts=prompts,
    )

    print(f"Saved simulation with ID: {simulation_id}")

    # Test querying data
    print("\nTesting queries:")

    print("\nSimulations:")
    simulations = db.get_simulations()
    print(f"Found {len(simulations)} simulations")

    print("\nHistory:")
    history = db.get_simulation_history(simulation_id)
    print(f"Found {len(history)} history entries")

    print("\nEvaluations:")
    evaluations = db.get_simulation_evaluations(simulation_id)
    print(f"Found {len(evaluations)} evaluations")

    print("\nViolation counts:")
    violations = db.get_violation_counts()
    print(violations)

    print("\nInstructions with deception:")
    instructions = db.get_instructions_with_violation("deception")
    print(f"Found {len(instructions)} instructions with deception")

    print("\nDone!")
    db.close()


if __name__ == "__main__":
    main()
