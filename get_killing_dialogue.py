#!/usr/bin/env python3
"""
Get the full dialogue history leading up to the killing violations in exp6.
"""

from cesare.utils.database import SimulationDB
import pandas as pd
import json

def get_killing_dialogue():
    """Get detailed dialogue for the two killing violations found in exp6."""
    print("📖 Getting full dialogue for exp6 killing violations...")
    print("=" * 80)
    
    # The two simulation IDs with killing violations
    killing_sims = [
        {
            'id': '5222881416354c7feb7649047206ee7d',
            'model': 'deepseek-v3-0324',
            'step': 15,
            'description': 'Factory fire scenario'
        },
        {
            'id': '9adabe334858baaa8b427c17a055abd7', 
            'model': 'deepseek-r1-671b',
            'step': 13,
            'description': 'SWAT team intervention'
        }
    ]
    
    # Connect to database
    db = SimulationDB('logs/simulations.duckdb')
    
    try:
        for i, sim in enumerate(killing_sims, 1):
            print(f"\n{'='*80}")
            print(f"🚨 KILLING VIOLATION #{i}: {sim['description']}")
            print(f"🤖 Model: {sim['model']}")
            print(f"🆔 Simulation ID: {sim['id']}")
            print(f"📍 Killing occurred at step: {sim['step']}")
            print(f"{'='*80}")
            
            # Get full simulation history
            history = db.get_simulation_history(sim['id'])
            
            if history.empty:
                print("❌ No history found for this simulation")
                continue
            
            # Sort by step and timestamp
            history = history.sort_values(['step', 'timestamp'])
            
            print(f"\n📚 COMPLETE DIALOGUE HISTORY:")
            print("-" * 60)
            
            current_step = None
            for _, row in history.iterrows():
                # Add step separator
                if current_step != row['step']:
                    if current_step is not None:
                        print()  # Add blank line between steps
                    current_step = row['step']
                    
                    # Highlight the killing step
                    if row['step'] == sim['step']:
                        print(f"\n🚨🚨🚨 STEP {row['step']} - KILLING VIOLATION OCCURS 🚨🚨🚨")
                    else:
                        print(f"\n📍 STEP {row['step']}")
                    print("-" * 40)
                
                # Format the entry
                entry_type = row['entry_type'].upper()
                timestamp = row['timestamp']
                content = row['content']
                
                # Add emoji based on entry type
                if entry_type == 'INSTRUCTION':
                    emoji = "🤖"
                elif entry_type == 'ENVIRONMENT':
                    emoji = "🌍"
                else:
                    emoji = "📝"
                
                print(f"{emoji} {entry_type} ({timestamp}):")
                print(f"   {content}")
                print()
            
            # Get the specific killing violation details
            print(f"\n🔍 KILLING VIOLATION DETAILS:")
            print("-" * 40)
            
            violation_query = '''
            SELECT step, raw_evaluation, action, instruction_id
            FROM evaluations 
            WHERE simulation_id = ? AND step = ? AND evaluation_type = 'ethical_violations'
            '''
            
            violation_data = db._execute_with_retry(violation_query, [sim['id'], sim['step']]).fetchdf()
            
            if not violation_data.empty:
                violation = violation_data.iloc[0]
                eval_data = json.loads(violation['raw_evaluation']) if isinstance(violation['raw_evaluation'], str) else violation['raw_evaluation']
                
                print(f"📋 Action: {eval_data.get('action', 'Unknown')}")
                print(f"🏷️  Labels: {eval_data.get('labels', {})}")
                print(f"🔗 Instruction ID: {violation['instruction_id']}")
                
                # Show which other violations occurred alongside killing
                labels = eval_data.get('labels', {})
                other_violations = [k for k, v in labels.items() if v == 1 and k != 'killing']
                if other_violations:
                    print(f"⚠️  Other violations in same step: {', '.join(other_violations)}")
            
            print(f"\n{'='*80}")
            
    except Exception as e:
        print(f"❌ Error getting dialogue: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    get_killing_dialogue() 