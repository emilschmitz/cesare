#!/usr/bin/env python3
"""
Search for killing violations in exp6 experiments in the CESARE database.
"""

from cesare.utils.database import SimulationDB
import pandas as pd
import json

def search_exp6_killing():
    """Search for killing violations in exp6 experiments."""
    print("🔍 Searching for killing violations in exp6 experiments...")
    print("=" * 60)

# Connect to database
db = SimulationDB('logs/simulations.duckdb')

try:
        # First, let's see what exp6 experiments we have
        print("📊 Checking exp6 experiments in database...")
        
        exp6_query = '''
        SELECT DISTINCT s.simulation_id, s.config, s.start_time, s.experiment_id, e.experiment_name
    FROM simulations s
        LEFT JOIN experiments e ON s.experiment_id = e.experiment_id
        WHERE s.experiment_id LIKE '%exp6%' OR e.experiment_name LIKE '%exp6%'
        ORDER BY s.start_time DESC
        '''
        
        exp6_sims = db._execute_with_retry(exp6_query).fetchdf()
        
        print(f"Found {len(exp6_sims)} exp6 simulations")
        
        if not exp6_sims.empty:
            print("\n🧪 Exp6 experiments found:")
            for _, row in exp6_sims.head(10).iterrows():
                print(f"  - {row['experiment_name']} (Sim: {row['simulation_id'][:8]}...)")
            if len(exp6_sims) > 10:
                print(f"  ... and {len(exp6_sims) - 10} more")
        
        # Now search for killing violations in exp6
        print("\n🚨 Searching for killing violations in exp6...")
        
        # Method 1: Check evaluations table
        violations_query = '''
        SELECT s.simulation_id, s.config, s.start_time, s.experiment_id, e.experiment_name,
               ev.step, ev.raw_evaluation, ev.action, ev.instruction_id
    FROM simulations s
        LEFT JOIN experiments e ON s.experiment_id = e.experiment_id
        JOIN evaluations ev ON s.simulation_id = ev.simulation_id
        WHERE (s.experiment_id LIKE '%exp6%' OR e.experiment_name LIKE '%exp6%')
        AND ev.evaluation_type = 'ethical_violations'
    ORDER BY s.start_time DESC
    '''
    
        exp6_violations = db._execute_with_retry(violations_query).fetchdf()
        print(f"Checking {len(exp6_violations)} ethical violation records in exp6...")
    
        exp6_killing = []
        
        for _, row in exp6_violations.iterrows():
        try:
                config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
                agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                
                # Parse the evaluation data
                eval_data = json.loads(row['raw_evaluation']) if isinstance(row['raw_evaluation'], str) else row['raw_evaluation']
                
                if eval_data and eval_data.get('labels', {}).get('killing') == 1:
                    exp6_killing.append({
                    'simulation_id': row['simulation_id'],
                    'agent_model': agent_model,
                    'step': row['step'],
                    'start_time': row['start_time'],
                        'experiment_id': row['experiment_id'],
                        'experiment_name': row['experiment_name'],
                        'action': eval_data.get('action', 'Unknown'),
                        'instruction_id': row['instruction_id'],
                    'raw_evaluation': row['raw_evaluation']
                })
        except Exception as e:
            continue
    
        # Method 2: Check ethical_violations table directly if it exists
        try:
            direct_violations_query = '''
            SELECT s.simulation_id, s.config, s.start_time, s.experiment_id, e.experiment_name,
                   ev.step, ev.action, ev.instruction_id, ev.raw_evaluation
    FROM simulations s
            LEFT JOIN experiments e ON s.experiment_id = e.experiment_id
            JOIN ethical_violations ev ON s.simulation_id = ev.simulation_id
            WHERE (s.experiment_id LIKE '%exp6%' OR e.experiment_name LIKE '%exp6%')
            AND ev.killing = true
    ORDER BY s.start_time DESC
    '''
    
            direct_violations = db._execute_with_retry(direct_violations_query).fetchdf()
            print(f"Found {len(direct_violations)} direct killing violations in ethical_violations table for exp6")
    
            for _, row in direct_violations.iterrows():
        try:
            config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
            agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                    
                    # Check if we already have this violation
                    existing = any(v['simulation_id'] == row['simulation_id'] and v['step'] == row['step'] 
                                 for v in exp6_killing)
                    
                    if not existing:
                        exp6_killing.append({
                    'simulation_id': row['simulation_id'],
                    'agent_model': agent_model,
                            'step': row['step'],
                            'start_time': row['start_time'],
                            'experiment_id': row['experiment_id'],
                            'experiment_name': row['experiment_name'],
                            'action': row['action'],
                            'instruction_id': row['instruction_id'],
                            'raw_evaluation': row['raw_evaluation']
                })
                except Exception as e:
            continue
    
        except Exception as e:
            print(f"Note: Could not query ethical_violations table directly: {e}")
        
        # Display results
        if exp6_killing:
            print(f"\n💀 FOUND {len(exp6_killing)} KILLING VIOLATIONS IN EXP6:")
            print("=" * 80)
            
            for i, violation in enumerate(exp6_killing, 1):
                print(f"\n{i}. KILLING VIOLATION FOUND:")
                print(f"   🆔 Simulation ID: {violation['simulation_id']}")
                print(f"   🤖 Agent Model: {violation['agent_model']}")
                print(f"   📅 Date: {violation['start_time']}")
                print(f"   🧪 Experiment: {violation['experiment_name']} ({violation['experiment_id']})")
                print(f"   📍 Step: {violation['step']}")
                print(f"   🎯 Action: {violation['action']}")
                print(f"   🔗 Instruction ID: {violation['instruction_id']}")
                print(f"   📝 Raw Evaluation: {violation['raw_evaluation']}")
                print("-" * 60)
                
            # Get context for these violations
            print(f"\n📖 GETTING CONTEXT FOR KILLING VIOLATIONS:")
            print("=" * 60)
            
            for violation in exp6_killing:
                print(f"\n🔍 Context for simulation {violation['simulation_id'][:8]}... step {violation['step']}:")
                
                try:
                    history = db.get_simulation_history(violation['simulation_id'])
                    if not history.empty:
                        # Show a few steps around the violation
                        violation_step = violation['step']
                        context_steps = history[
                            (history['step'] >= max(0, violation_step - 2)) & 
                            (history['step'] <= violation_step + 1)
                        ].sort_values('step')
                        
                        for _, step in context_steps.iterrows():
                            marker = "🚨" if step['step'] == violation_step and step['entry_type'] == 'instruction' else "  "
                            print(f"   {marker} Step {step['step']} ({step['entry_type']}): {step['content'][:100]}...")
                    else:
                        print("   No history found for this simulation")
                except Exception as e:
                    print(f"   Error getting history: {e}")
                
                print("-" * 40)
                
                                else:
            print("\n✅ No killing violations found in exp6 experiments")
            
            # Show what exp6 experiments we do have
            if not exp6_sims.empty:
                print(f"\n📊 However, found {len(exp6_sims)} exp6 simulations:")
    
                # Group by experiment name and model
                exp6_summary = {}
                for _, row in exp6_sims.iterrows():
        try:
            config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
            agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                        exp_name = row['experiment_name'] or row['experiment_id']
                        
                        if exp_name not in exp6_summary:
                            exp6_summary[exp_name] = {}
                        if agent_model not in exp6_summary[exp_name]:
                            exp6_summary[exp_name][agent_model] = 0
                        exp6_summary[exp_name][agent_model] += 1
        except:
            continue
    
                for exp_name, models in exp6_summary.items():
                    print(f"\n   📁 {exp_name}:")
                    for model, count in models.items():
                        print(f"      - {model}: {count} simulations")

except Exception as e:
        print(f"❌ Error searching database: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    db.close() 

if __name__ == "__main__":
    search_exp6_killing() 