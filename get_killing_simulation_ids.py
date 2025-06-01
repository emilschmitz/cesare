#!/usr/bin/env python3
"""
Extract simulation IDs of killing violations in exp6.
"""

from cesare.utils.database import SimulationDB
import pandas as pd
import json

def get_killing_simulation_ids():
    """Get simulation IDs for killing violations in exp6."""
    print("🔍 Extracting simulation IDs for exp6 killing violations...")
    print("=" * 60)
    
    # Connect to database
    db = SimulationDB('logs/simulations.duckdb')
    
    try:
        # Search for killing violations in exp6
        violations_query = '''
        SELECT DISTINCT s.simulation_id, s.config, s.start_time, s.experiment_id, e.experiment_name,
               ev.step, ev.raw_evaluation, ev.action
        FROM simulations s
        LEFT JOIN experiments e ON s.experiment_id = e.experiment_id
        JOIN evaluations ev ON s.simulation_id = ev.simulation_id
        WHERE (s.experiment_id LIKE '%exp6%' OR e.experiment_name LIKE '%exp6%')
        AND ev.evaluation_type = 'ethical_violations'
        ORDER BY s.start_time DESC
        '''
        
        exp6_violations = db._execute_with_retry(violations_query).fetchdf()
        print(f"Checking {len(exp6_violations)} ethical violation records in exp6...")
        
        killing_violations = []
        
        for _, row in exp6_violations.iterrows():
            try:
                config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
                agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                
                # Parse the evaluation data
                eval_data = json.loads(row['raw_evaluation']) if isinstance(row['raw_evaluation'], str) else row['raw_evaluation']
                
                if eval_data and eval_data.get('labels', {}).get('killing') == 1:
                    killing_violations.append({
                        'simulation_id': row['simulation_id'],
                        'agent_model': agent_model,
                        'step': row['step'],
                        'start_time': row['start_time'],
                        'experiment_name': row['experiment_name'],
                        'action': eval_data.get('action', 'Unknown')
                    })
            except Exception as e:
                continue
        
        if killing_violations:
            print(f"\n🚨 FOUND {len(killing_violations)} KILLING VIOLATIONS:")
            print("=" * 60)
            
            for i, violation in enumerate(killing_violations, 1):
                print(f"\n{i}. SIMULATION ID: {violation['simulation_id']}")
                print(f"   Model: {violation['agent_model']}")
                print(f"   Step: {violation['step']}")
                print(f"   Date: {violation['start_time']}")
                print(f"   Experiment: {violation['experiment_name']}")
                print(f"   Action: {violation['action'][:100]}...")
                
            print(f"\n📋 SIMULATION IDS ONLY:")
            print("-" * 30)
            for violation in killing_violations:
                print(violation['simulation_id'])
                
        else:
            print("\n✅ No killing violations found in exp6 experiments")
    
    except Exception as e:
        print(f"❌ Error searching database: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    get_killing_simulation_ids() 