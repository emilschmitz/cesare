#!/usr/bin/env python3
"""
Generate ethical analysis summary CSVs for all exp12 experiments.

This script fetches the ethical analysis summaries from the CESARE API
and saves them as CSV files in the ethical-analysis-tables folder.
"""

import requests
import json
import csv
import os
from pathlib import Path
import sys

# API base URL
API_BASE_URL = "http://localhost:5000/api"

# Exp12 experiment names
EXP12_EXPERIMENTS = [
    "exp12-lambda-only-conversation-temp-0",
    "exp12-lambda-only-conversation-temp-0.6", 
    "exp12-lambda-only-conversation-temp-1.2",
    "exp12-lambda-only-factory-temp-0",
    "exp12-lambda-only-factory-temp-0.6",
    "exp12-lambda-only-factory-temp-1.2",
    "exp12-lambda-only-space-temp-0",
    "exp12-lambda-only-space-temp-0.6",
    "exp12-lambda-only-space-temp-1.2"
]

# Violation types for CSV headers
VIOLATION_TYPES = [
    'killing', 'physical_harm', 'non_physical_harm', 'intending_harm',
    'deception', 'manipulation', 'betrayal', 'stealing',
    'trespassing', 'spying', 'vandalism', 'unfairness', 'other'
]

def format_violation_type(type_name):
    """Format violation type name for CSV header."""
    return type_name.replace('_', ' ').title() + ' %'

def fetch_experiment_summary(experiment_name):
    """Fetch ethical analysis summary for a specific experiment."""
    url = f"{API_BASE_URL}/experiments/{experiment_name}/violations-summary"
    
    try:
        print(f"Fetching data for {experiment_name}...")
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {experiment_name}: {e}")
        return None

def convert_to_csv_format(data, experiment_name):
    """Convert API response to CSV format matching the webapp export."""
    if not data or 'aggregated_stats' not in data:
        print(f"No aggregated stats found for {experiment_name}")
        return None
    
    # CSV headers matching the webapp format
    headers = [
        'Agent Model',
        'Total Simulations', 
        'Total Instructions',
        'Avg Instructions/Sim',
        'Positive Utility %',
        'Neutral Utility %',
        'Negative Utility %', 
        'Avg Net Utility/Sim',
        'Net Utility Std Dev',
        'Avg Utility/Sim'
    ]
    
    # Add violation type headers
    for violation_type in VIOLATION_TYPES:
        headers.append(format_violation_type(violation_type))
    
    # Convert aggregated stats to CSV rows
    csv_rows = []
    for stat in data['aggregated_stats']:
        row = [
            stat['agent_model'],
            stat['total_simulations'],
            stat['total_instructions'],
            round(stat['avg_instructions_per_simulation'], 1),
            round(stat['positive_utility_percentage'], 2),
            round(stat['neutral_utility_percentage'], 2),
            round(stat['negative_utility_percentage'], 2),
            stat['avg_net_utility_per_simulation'],
            stat['net_utility_std_dev'],
            stat['avg_utility_per_simulation']
        ]
        
        # Add violation percentages
        for violation_type in VIOLATION_TYPES:
            percentage = stat.get(f'{violation_type}_percentage', 0)
            row.append(round(percentage, 3))
        
        csv_rows.append(row)
    
    return headers, csv_rows

def save_csv(headers, rows, filepath):
    """Save data to CSV file."""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"✅ Saved: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error saving {filepath}: {e}")
        return False

def main():
    """Main function to generate all exp12 ethical analysis summaries."""
    print("🔄 Generating exp12 ethical analysis summaries...")
    
    # Create output directory
    output_dir = Path("ethical-analysis-tables")
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    successful_exports = 0
    failed_exports = 0
    
    for experiment_name in EXP12_EXPERIMENTS:
        print(f"\n📊 Processing {experiment_name}...")
        
        # Fetch data from API
        data = fetch_experiment_summary(experiment_name)
        if not data:
            print(f"❌ Failed to fetch data for {experiment_name}")
            failed_exports += 1
            continue
        
        # Convert to CSV format
        csv_data = convert_to_csv_format(data, experiment_name)
        if not csv_data:
            print(f"❌ Failed to convert data for {experiment_name}")
            failed_exports += 1
            continue
        
        headers, rows = csv_data
        
        # Save CSV file
        csv_filename = f"{experiment_name}_ethical_analysis.csv"
        csv_filepath = output_dir / csv_filename
        
        if save_csv(headers, rows, csv_filepath):
            successful_exports += 1
            print(f"📈 Exported {len(rows)} agent configurations")
        else:
            failed_exports += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 EXPORT SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful exports: {successful_exports}")
    print(f"❌ Failed exports: {failed_exports}")
    print(f"📁 Files saved to: {output_dir.absolute()}")
    
    if successful_exports > 0:
        print(f"\n📋 Generated files:")
        for experiment_name in EXP12_EXPERIMENTS:
            csv_filename = f"{experiment_name}_ethical_analysis.csv"
            csv_filepath = output_dir / csv_filename
            if csv_filepath.exists():
                print(f"   📄 {csv_filename}")
    
    if failed_exports > 0:
        print(f"\n⚠️  Note: {failed_exports} experiments failed to export.")
        print("   Make sure the CESARE API is running on localhost:5000")
        print("   and that the experiments have been completed.")

if __name__ == "__main__":
    main() 