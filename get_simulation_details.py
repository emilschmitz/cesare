#!/usr/bin/env python3
"""
Get detailed information about the DeepSeek V3 simulation with killing violation.
"""

from cesare.utils.database import SimulationDB
import pandas as pd
import json

def get_simulation_details(simulation_id):
    """Get detailed information about a specific simulation."""
    print(f"🔍 Getting detailed information for simulation: {simulation_id}")
    print("=" * 80)
    
    # Connect to database
    db = SimulationDB('logs/simulations.duckdb')
    
    try:
        # Get simulation metadata
        sim_query = '''
        SELECT s.*, e.experiment_name
        FROM simulations s
        LEFT JOIN experiments e ON s.experiment_id = e.experiment_id
        WHERE s.simulation_id = ?
        '''
        
        sim_data = db._execute_with_retry(sim_query, [simulation_id]).fetchdf()
        
        if sim_data.empty:
            print(f"❌ No simulation found with ID: {simulation_id}")
            return
        
        sim = sim_data.iloc[0]
        config = json.loads(sim['config']) if isinstance(sim['config'], str) else sim['config']
        
        print("📊 SIMULATION METADATA:")
        print(f"   🆔 Simulation ID: {sim['simulation_id']}")
        print(f"   🧪 Experiment: {sim['experiment_name']}")
        print(f"   📅 Start Time: {sim['start_time']}")
        print(f"   ⏱️  End Time: {sim['end_time']}")
        print(f"   📈 Total Steps: {sim['total_steps']}")
        print(f"   📝 Total Instructions: {sim['total_instructions']}")
        
        print(f"\n🤖 MODEL CONFIGURATION:")
        models = config.get('models', {})
        print(f"   🎯 Agent Model: {models.get('agent', {}).get('name', 'Unknown')}")
        print(f"   🌍 Environment Model: {models.get('environment', {}).get('name', 'Unknown')}")
        print(f"   ⚖️  Evaluator Model: {models.get('evaluator', {}).get('name', 'Unknown')}")
        
        # Get full history
        print(f"\n📖 FULL SIMULATION HISTORY:")
        print("=" * 60)
        
        history = db.get_simulation_history(simulation_id)
        if not history.empty:
            for _, step in history.iterrows():
                print(f"\n📍 Step {step['step']} ({step['entry_type']}):")
                print(f"   🕐 {step['timestamp']}")
                print(f"   💬 {step['content']}")
        else:
            print("   No history found")
        
        # Get all ethical violations for this simulation
        print(f"\n🚨 ALL ETHICAL VIOLATIONS:")
        print("=" * 60)
        
        violations = db.get_simulation_ethical_violations(simulation_id)
        if not violations.empty:
            for _, violation in violations.iterrows():
                eval_data = json.loads(violation['raw_evaluation']) if isinstance(violation['raw_evaluation'], str) else violation['raw_evaluation']
                
                print(f"\n⚠️  Step {violation['step']} Violation:")
                print(f"   🎯 Action: {violation['action']}")
                print(f"   💀 Killing: {violation['killing']}")
                print(f"   🤕 Physical Harm: {violation['physical_harm']}")
                print(f"   😢 Non-Physical Harm: {violation['non_physical_harm']}")
                print(f"   🎯 Intending Harm: {violation['intending_harm']}")
                print(f"   🤥 Deception: {violation['deception']}")
                print(f"   🎭 Manipulation: {violation['manipulation']}")
                print(f"   💔 Betrayal: {violation['betrayal']}")
                print(f"   🏴‍☠️ Stealing: {violation['stealing']}")
                print(f"   🚪 Trespassing: {violation['trespassing']}")
                print(f"   👁️  Spying: {violation['spying']}")
                print(f"   💥 Vandalism: {violation['vandalism']}")
                print(f"   ⚖️  Unfairness: {violation['unfairness']}")
                print(f"   ❓ Other: {violation['other']}")
                print(f"   🕐 Timestamp: {violation['timestamp']}")
        else:
            print("   No ethical violations found")
        
        # Get power seeking data
        print(f"\n💪 POWER SEEKING ANALYSIS:")
        print("=" * 60)
        
        try:
            power_seeking = db.get_simulation_power_seeking(simulation_id)
            if not power_seeking.empty:
                for _, power in power_seeking.iterrows():
                    print(f"\n🔋 Step {power['step']} Power Seeking:")
                    print(f"   🎯 Action: {power['action']}")
                    print(f"   💪 Physical Power: {power['physical_power']}")
                    print(f"   💰 Economic Power: {power['economic_power']}")
                    print(f"   📊 Informational Power: {power['informational_power']}")
                    print(f"   👥 Social Power: {power['social_power']}")
                    print(f"   ❓ Other Power: {power['other_power']}")
            else:
                print("   No power seeking data found")
        except Exception as e:
            print(f"   Error getting power seeking data: {e}")
        
        # Get utility data
        print(f"\n💼 UTILITY ANALYSIS:")
        print("=" * 60)
        
        try:
            utility = db.get_simulation_disutility(simulation_id)
            if not utility.empty:
                for _, util in utility.iterrows():
                    print(f"\n📈 Step {util['step']} Utility:")
                    print(f"   🎯 Action: {util['action']}")
                    print(f"   📊 Utility Change: {util['utility_change']}")
            else:
                print("   No utility data found")
        except Exception as e:
            print(f"   Error getting utility data: {e}")
    
    except Exception as e:
        print(f"❌ Error getting simulation details: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    # The simulation ID with the killing violation
    simulation_id = "5222881416354c7feb7649047206ee7d"
    get_simulation_details(simulation_id) 