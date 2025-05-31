from cesare.utils.database import SimulationDB
import pandas as pd
import json

# Connect to database
db = SimulationDB('logs/simulations.duckdb')

try:
    # Let's look at the structure of raw_evaluation data and config
    sample_query = '''
    SELECT s.config, e.evaluation_type, e.raw_evaluation, e.step
    FROM simulations s
    JOIN evaluations e ON s.simulation_id = e.simulation_id
    WHERE e.evaluation_type = 'ethical_violations'
    LIMIT 3
    '''
    
    sample_data = db._execute_with_retry(sample_query).fetchdf()
    print("Sample evaluation data structure:")
    for _, row in sample_data.iterrows():
        try:
            config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
            agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
            print(f"Agent Model: {agent_model}")
            print(f"Step: {row['step']}")
            print(f"Raw evaluation: {row['raw_evaluation']}")
            print("-" * 30)
        except Exception as e:
            print(f"Error parsing config: {e}")
    print()
    
    # Get all ethical violations and parse JSON in Python to find killing violations
    all_violations_query = '''
    SELECT s.simulation_id, s.config, s.start_time, e.step, e.raw_evaluation
    FROM simulations s
    JOIN evaluations e ON s.simulation_id = e.simulation_id
    WHERE e.evaluation_type = 'ethical_violations'
    ORDER BY s.start_time DESC
    '''
    
    all_violations = db._execute_with_retry(all_violations_query).fetchdf()
    print(f'Checking {len(all_violations)} ethical violation records for killing...')
    
    killing_found = []
    for _, row in all_violations.iterrows():
        try:
            eval_data = json.loads(row['raw_evaluation']) if isinstance(row['raw_evaluation'], str) else row['raw_evaluation']
            if eval_data and eval_data.get('killing') == 1:
                config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
                agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
                killing_found.append({
                    'simulation_id': row['simulation_id'],
                    'agent_model': agent_model,
                    'step': row['step'],
                    'start_time': row['start_time'],
                    'raw_evaluation': row['raw_evaluation']
                })
        except Exception as e:
            continue
    
    if killing_found:
        print(f'\n🚨 Found {len(killing_found)} KILLING VIOLATIONS:')
        print("=" * 60)
        for violation in killing_found:
            print(f'Simulation ID: {violation["simulation_id"]}')
            print(f'Agent Model: {violation["agent_model"]}')
            print(f'Step Number: {violation["step"]}')
            print(f'Date: {violation["start_time"]}')
            print(f'Raw evaluation: {violation["raw_evaluation"]}')
            print('-' * 50)
    else:
        print('No killing violations found.')
        
    # Check for deepseek-v3 models specifically
    all_sims_query = '''
    SELECT DISTINCT s.simulation_id, s.config, s.start_time
    FROM simulations s
    ORDER BY s.start_time DESC
    '''
    
    all_sims = db._execute_with_retry(all_sims_query).fetchdf()
    
    v3_sims = []
    for _, row in all_sims.iterrows():
        try:
            config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
            agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
            if 'v3' in agent_model.lower() or 'deepseek-v3' in agent_model.lower():
                v3_sims.append({
                    'simulation_id': row['simulation_id'],
                    'agent_model': agent_model,
                    'start_time': row['start_time']
                })
        except:
            continue
    
    print(f'\nFound {len(v3_sims)} simulations with v3 models:')
    for sim in v3_sims:
        print(f'- {sim["agent_model"]} (ID: {sim["simulation_id"]})')
        
    # Get detailed violation info for v3 models
    if len(v3_sims) > 0:
        print('\nDetailed violation analysis for v3 models:')
        for sim in v3_sims:
            sim_id = sim['simulation_id']
            violations_query = f'''
            SELECT step, raw_evaluation
            FROM evaluations
            WHERE simulation_id = '{sim_id}' AND evaluation_type = 'ethical_violations'
            ORDER BY step
            '''
            violations = db._execute_with_retry(violations_query).fetchdf()
            
            print(f'\nModel: {sim["agent_model"]} (ID: {sim_id})')
            total_violations = 0
            violation_types = set()
            
            for _, viol in violations.iterrows():
                try:
                    eval_data = json.loads(viol['raw_evaluation']) if isinstance(viol['raw_evaluation'], str) else viol['raw_evaluation']
                    if eval_data:
                        for vtype, value in eval_data.items():
                            if value == 1:
                                violation_types.add(vtype)
                                total_violations += 1
                                if vtype == 'killing':
                                    print(f'  🚨 Step {viol["step"]}: {vtype} ⚠️ KILLING VIOLATION!')
                                else:
                                    print(f'  Step {viol["step"]}: {vtype}')
                except:
                    continue
            
            if total_violations == 0:
                print('  No violations found')
            else:
                print(f'  Total violations: {total_violations}')
                print(f'  Violation types: {", ".join(sorted(violation_types))}')
    
    # Summary of all models with violations
    print(f'\n=== SUMMARY OF ALL MODELS WITH VIOLATIONS ===')
    model_violations = {}
    
    for _, row in all_violations.iterrows():
        try:
            config = json.loads(row['config']) if isinstance(row['config'], str) else row['config']
            agent_model = config.get('models', {}).get('agent', {}).get('name', 'Unknown')
            
            eval_data = json.loads(row['raw_evaluation']) if isinstance(row['raw_evaluation'], str) else row['raw_evaluation']
            if eval_data:
                if agent_model not in model_violations:
                    model_violations[agent_model] = {'total': 0, 'types': set()}
                
                for vtype, value in eval_data.items():
                    if value == 1:
                        model_violations[agent_model]['total'] += 1
                        model_violations[agent_model]['types'].add(vtype)
        except:
            continue
    
    # Sort by total violations
    sorted_models = sorted(model_violations.items(), key=lambda x: x[1]['total'], reverse=True)
    
    print(f'Top 10 models by violation count:')
    for i, (model, data) in enumerate(sorted_models[:10], 1):
        has_killing = 'killing' in data['types']
        killing_marker = ' 🚨 KILLING' if has_killing else ''
        print(f'{i:2d}. {model}: {data["total"]} violations{killing_marker}')
        if has_killing:
            print(f'    Types: {", ".join(sorted(data["types"]))}')

except Exception as e:
    print(f'Error querying database: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close() 