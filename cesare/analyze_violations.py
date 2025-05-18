"""
Analysis tool for exploring ethical violations in simulations.

This script provides functions to analyze and visualize ethical violations
across simulation runs.
"""
import os
import sys
import argparse
import pandas as pd
from utils.database import SimulationDB
import matplotlib.pyplot as plt


def print_violation_summary(db: SimulationDB):
    """Print a summary of all ethical violations."""
    print("===== ETHICAL VIOLATIONS SUMMARY =====")
    
    # Get total violation counts
    violations = db.get_violation_counts()
    
    if violations.empty:
        print("No violations found in the database.")
        return
    
    # Transpose for better display
    violations = violations.T.reset_index()
    violations.columns = ['Violation Type', 'Count']
    
    # Sort by count
    violations = violations.sort_values('Count', ascending=False)
    
    # Print summary
    print(violations.to_string(index=False))
    print("\nTotal Violations:", violations['Count'].sum())
    
    # Get total simulations
    simulations = db.get_simulations()
    print(f"Across {len(simulations)} simulation(s)")


def plot_violations(db: SimulationDB, output_file: str = None):
    """Plot ethical violations and save to file."""
    violations = db.get_violation_counts()
    
    if violations.empty:
        print("No violations found to plot.")
        return
    
    # Transpose and prepare for plotting
    violations = violations.T.reset_index()
    violations.columns = ['Violation Type', 'Count']
    violations = violations.sort_values('Count', ascending=False)
    
    # Create plot
    plt.figure(figsize=(12, 6))
    plt.bar(violations['Violation Type'], violations['Count'])
    plt.xticks(rotation=45, ha='right')
    plt.title('Ethical Violations Across All Simulations')
    plt.xlabel('Violation Type')
    plt.ylabel('Count')
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file)
        print(f"Plot saved to {output_file}")
    else:
        plt.show()


def list_instructions_with_violation(db: SimulationDB, violation_type: str):
    """List all instructions with a specific violation type."""
    try:
        instructions = db.get_instructions_with_violation(violation_type)
        
        if instructions.empty:
            print(f"No instructions found with violation type: {violation_type}")
            return
        
        print(f"===== INSTRUCTIONS WITH {violation_type.upper()} VIOLATIONS =====")
        for _, row in instructions.iterrows():
            print(f"Simulation ID: {row['simulation_id']}")
            print(f"Step: {row['step']}")
            print(f"Action: {row['action']}")
            print(f"Content: {row['content']}")
            print("-" * 80)
            
    except ValueError as e:
        print(f"Error: {e}")


def main():
    """Main function to parse arguments and run analysis."""
    parser = argparse.ArgumentParser(description="Analyze ethical violations in simulations")
    parser.add_argument(
        "--db", "-d", 
        default="logs/simulations.duckdb",
        help="Path to the DuckDB database file"
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Print a summary of all violations"
    )
    parser.add_argument(
        "--plot", "-p",
        action="store_true",
        help="Plot violations and display"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save plot to output file"
    )
    parser.add_argument(
        "--list-type", "-l",
        help="List all instructions with a specific violation type"
    )
    
    args = parser.parse_args()
    
    # Initialize database
    if not os.path.exists(args.db):
        print(f"Error: Database file not found at {args.db}")
        sys.exit(1)
        
    db = SimulationDB(args.db)
    
    # Process commands
    if args.summary:
        print_violation_summary(db)
    
    if args.plot or args.output:
        plot_violations(db, args.output)
    
    if args.list_type:
        list_instructions_with_violation(db, args.list_type)
    
    # If no specific action, print help
    if not (args.summary or args.plot or args.output or args.list_type):
        parser.print_help()
    
    db.close()


if __name__ == "__main__":
    main() 