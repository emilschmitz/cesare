#!/usr/bin/env python3
"""
Search for DeepSeek V3 models with killing violations in the CESARE database.
"""

from cesare.utils.database import SimulationDB
import pandas as pd
import json

def search_deepseek_v3_killing():
    """Search for DeepSeek V3 models with killing violations."""
    print("🔍 Searching for DeepSeek V3 models with killing violations...")
    print("=" * 60)
    
    # Connect to database
    db = SimulationDB('logs/simulations.duckdb')
    
    try:
        # First, let's see what DeepSeek models we have in the database
        print("📊 Checking all DeepSeek models in database...")
        
        all_sims_query = '''
        SELECT DISTINCT s.simulation_id, s.config, s.start_time, s.experiment_id
        FROM simulations s
        ORDER BY s.start_time DESC
        '''
        
        all_sims = db._execute_with_retry(all_sims_query).fetchdf()
        
        deepseek_models = []
        deepseek_v3_models = []
        
        for _, row in all_sims.iterrows():
            try:
                config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
                agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                
                if 'deepseek' in agent_model.lower():
                    deepseek_models.append({
                        'simulation_id': row['simulation_id'],
                        'agent_model': agent_model,
                        'start_time': row['start_time'],
                        'experiment_id': row['experiment_id']
                    })
                    
                    if 'v3' in agent_model.lower():
                        deepseek_v3_models.append({
                            'simulation_id': row['simulation_id'],
                            'agent_model': agent_model,
                            'start_time': row['start_time'],
                            'experiment_id': row['experiment_id']
                        })
            except Exception as e:
                continue
        
        print(f"Found {len(deepseek_models)} DeepSeek model simulations total")
        print(f"Found {len(deepseek_v3_models)} DeepSeek V3 model simulations")
        
        if deepseek_v3_models:
            print("\n🤖 DeepSeek V3 models found:")
            for model in deepseek_v3_models:
                print(f"  - {model['agent_model']} (Sim: {model['simulation_id'][:8]}...)")
        
        # Now search for killing violations specifically in DeepSeek V3 models
        print("\n🚨 Searching for killing violations in DeepSeek V3 models...")
        
        # Get all ethical violations and check for killing in DeepSeek V3 models
        violations_query = '''
        SELECT s.simulation_id, s.config, s.start_time, s.experiment_id, 
               e.step, e.raw_evaluation, e.action, e.instruction_id
        FROM simulations s
        JOIN evaluations e ON s.simulation_id = e.simulation_id
        WHERE e.evaluation_type = 'ethical_violations'
        ORDER BY s.start_time DESC
        '''
        
        all_violations = db._execute_with_retry(violations_query).fetchdf()
        print(f"Checking {len(all_violations)} ethical violation records...")
        
        deepseek_v3_killing = []
        
        for _, row in all_violations.iterrows():
            try:
                config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
                agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                
                # Check if this is a DeepSeek V3 model
                if 'deepseek' in agent_model.lower() and 'v3' in agent_model.lower():
                    # Parse the evaluation data
                    eval_data = json.loads(row['raw_evaluation']) if isinstance(row['raw_evaluation'], str) else row['raw_evaluation']
                    
                    if eval_data and eval_data.get('labels', {}).get('killing') == 1:
                        deepseek_v3_killing.append({
                            'simulation_id': row['simulation_id'],
                            'agent_model': agent_model,
                            'step': row['step'],
                            'start_time': row['start_time'],
                            'experiment_id': row['experiment_id'],
                            'action': eval_data.get('action', 'Unknown'),
                            'instruction_id': row['instruction_id'],
                            'raw_evaluation': row['raw_evaluation']
                        })
            except Exception as e:
                continue
        
        # Also check the ethical_violations table directly if it exists
        try:
            direct_violations_query = '''
            SELECT s.simulation_id, s.config, s.start_time, s.experiment_id,
                   ev.step, ev.action, ev.instruction_id, ev.raw_evaluation
            FROM simulations s
            JOIN ethical_violations ev ON s.simulation_id = ev.simulation_id
            WHERE ev.killing = true
            ORDER BY s.start_time DESC
            '''
            
            direct_violations = db._execute_with_retry(direct_violations_query).fetchdf()
            print(f"Found {len(direct_violations)} direct killing violations in ethical_violations table")
            
            for _, row in direct_violations.iterrows():
                try:
                    config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
                    agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                    
                    if 'deepseek' in agent_model.lower() and 'v3' in agent_model.lower():
                        # Check if we already have this violation
                        existing = any(v['simulation_id'] == row['simulation_id'] and v['step'] == row['step'] 
                                     for v in deepseek_v3_killing)
                        
                        if not existing:
                            deepseek_v3_killing.append({
                                'simulation_id': row['simulation_id'],
                                'agent_model': agent_model,
                                'step': row['step'],
                                'start_time': row['start_time'],
                                'experiment_id': row['experiment_id'],
                                'action': row['action'],
                                'instruction_id': row['instruction_id'],
                                'raw_evaluation': row['raw_evaluation']
                            })
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Note: Could not query ethical_violations table directly: {e}")
        
        # Display results
        if deepseek_v3_killing:
            print(f"\n💀 FOUND {len(deepseek_v3_killing)} KILLING VIOLATIONS BY DEEPSEEK V3 MODELS:")
            print("=" * 80)
            
            for i, violation in enumerate(deepseek_v3_killing, 1):
                print(f"\n{i}. KILLING VIOLATION FOUND:")
                print(f"   🆔 Simulation ID: {violation['simulation_id']}")
                print(f"   🤖 Agent Model: {violation['agent_model']}")
                print(f"   📅 Date: {violation['start_time']}")
                print(f"   🧪 Experiment: {violation['experiment_id']}")
                print(f"   📍 Step: {violation['step']}")
                print(f"   🎯 Action: {violation['action']}")
                print(f"   🔗 Instruction ID: {violation['instruction_id']}")
                print(f"   📝 Raw Evaluation: {violation['raw_evaluation']}")
                print("-" * 60)
                
            # Get the history for these violations to see the context
            print(f"\n📖 GETTING CONTEXT FOR KILLING VIOLATIONS:")
            print("=" * 60)
            
            for violation in deepseek_v3_killing:
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
            print("\n✅ No killing violations found for DeepSeek V3 models")
            
            # Show what DeepSeek models we do have
            if deepseek_models:
                print(f"\n📊 However, found {len(deepseek_models)} other DeepSeek model simulations:")
                for model in deepseek_models[:10]:  # Show first 10
                    print(f"   - {model['agent_model']} (Sim: {model['simulation_id'][:8]}...)")
                if len(deepseek_models) > 10:
                    print(f"   ... and {len(deepseek_models) - 10} more")
    
    except Exception as e:
        print(f"❌ Error searching database: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    search_deepseek_v3_killing() 