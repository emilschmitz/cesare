from flask import Flask, jsonify
from flask_cors import CORS
import duckdb
import os
import json
import glob
import yaml

app = Flask(__name__)
CORS(app)

# Path to the DuckDB database
DB_PATH = "../logs/simulations.duckdb"

def get_db_connection():
    """Get a connection to the DuckDB database."""
    if not os.path.exists(DB_PATH):
        return None
    return duckdb.connect(DB_PATH)

@app.route('/api/simulations', methods=['GET'])
def get_simulations():
    """Get all simulations."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        # Check if experiments table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        if 'experiments' in table_names:
            # Join with experiments table to get experiment_name
            simulations = conn.execute("""
                SELECT s.*, e.experiment_name
                FROM simulations s
                LEFT JOIN experiments e ON s.experiment_id = e.experiment_id
                ORDER BY s.start_time DESC
            """).fetchdf()
        else:
            # Fallback to original query if experiments table doesn't exist
            simulations = conn.execute("SELECT * FROM simulations ORDER BY start_time DESC").fetchdf()
        
        # Convert to records format for JSON serialization
        simulations_list = simulations.to_dict(orient='records')
        
        # Format dates and JSON strings
        for sim in simulations_list:
            if 'start_time' in sim and sim['start_time'] is not None:
                sim['start_time'] = sim['start_time'].isoformat()
            if 'end_time' in sim and sim['end_time'] is not None:
                sim['end_time'] = sim['end_time'].isoformat()
            if 'config' in sim and sim['config'] is not None:
                sim['config'] = json.loads(sim['config'])
            if 'metadata' in sim and sim['metadata'] is not None:
                sim['metadata'] = json.loads(sim['metadata'])
            # Ensure ai_key and environment_key are present with defaults
            if 'ai_key' not in sim or sim['ai_key'] is None:
                sim['ai_key'] = 'instruction'
            if 'environment_key' not in sim or sim['environment_key'] is None:
                sim['environment_key'] = 'environment'
        
        return jsonify(simulations_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/simulations/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id):
    """Get a specific simulation."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        # Get simulation
        simulation = conn.execute(
            "SELECT * FROM simulations WHERE simulation_id = ?", 
            [simulation_id]
        ).fetchdf()
        
        if simulation.empty:
            return jsonify({"error": "Simulation not found"}), 404
        
        # Convert to dictionary and format dates/JSON
        simulation_dict = simulation.iloc[0].to_dict()
        if 'start_time' in simulation_dict and simulation_dict['start_time'] is not None:
            simulation_dict['start_time'] = simulation_dict['start_time'].isoformat()
        if 'end_time' in simulation_dict and simulation_dict['end_time'] is not None:
            simulation_dict['end_time'] = simulation_dict['end_time'].isoformat()
        if 'config' in simulation_dict and simulation_dict['config'] is not None:
            simulation_dict['config'] = json.loads(simulation_dict['config'])
        if 'metadata' in simulation_dict and simulation_dict['metadata'] is not None:
            simulation_dict['metadata'] = json.loads(simulation_dict['metadata'])
        # Ensure ai_key and environment_key are present with defaults
        if 'ai_key' not in simulation_dict or simulation_dict['ai_key'] is None:
            simulation_dict['ai_key'] = 'instruction'
        if 'environment_key' not in simulation_dict or simulation_dict['environment_key'] is None:
            simulation_dict['environment_key'] = 'environment'
        
        return jsonify(simulation_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/simulations/<simulation_id>/history', methods=['GET'])
def get_simulation_history(simulation_id):
    """Get the history for a specific simulation."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        history = conn.execute(
            "SELECT * FROM history WHERE simulation_id = ? ORDER BY step", 
            [simulation_id]
        ).fetchdf()
        
        if history.empty:
            return jsonify([])
        
        # Convert to records format and format dates
        history_list = history.to_dict(orient='records')
        for item in history_list:
            if 'timestamp' in item and item['timestamp'] is not None:
                item['timestamp'] = item['timestamp'].isoformat()
        
        return jsonify(history_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/simulations/<simulation_id>/evaluations', methods=['GET'])
def get_simulation_evaluations(simulation_id):
    """Get all evaluations for a specific simulation (general table)."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        evaluations = conn.execute(
            "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY step", 
            [simulation_id]
        ).fetchdf()
        
        if evaluations.empty:
            return jsonify([])
        
        # Convert to records format and format dates/JSON
        evaluations_list = evaluations.to_dict(orient='records')
        for item in evaluations_list:
            if 'timestamp' in item and item['timestamp'] is not None:
                item['timestamp'] = item['timestamp'].isoformat()
            if 'raw_evaluation' in item and item['raw_evaluation'] is not None:
                item['raw_evaluation'] = json.loads(item['raw_evaluation'])
        
        return jsonify(evaluations_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/simulations/<simulation_id>/ethical-violations', methods=['GET'])
def get_simulation_ethical_violations(simulation_id):
    """Get ethical violations evaluations for a specific simulation."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        evaluations = conn.execute(
            "SELECT * FROM ethical_violations WHERE simulation_id = ? ORDER BY step", 
            [simulation_id]
        ).fetchdf()
        
        if evaluations.empty:
            return jsonify([])
        
        # Convert to records format and format dates/JSON
        evaluations_list = evaluations.to_dict(orient='records')
        for item in evaluations_list:
            if 'timestamp' in item and item['timestamp'] is not None:
                item['timestamp'] = item['timestamp'].isoformat()
            if 'raw_evaluation' in item and item['raw_evaluation'] is not None:
                item['raw_evaluation'] = json.loads(item['raw_evaluation'])
        
        return jsonify(evaluations_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/simulations/<simulation_id>/power-seeking', methods=['GET'])
def get_simulation_power_seeking(simulation_id):
    """Get power seeking evaluations for a specific simulation."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        evaluations = conn.execute(
            "SELECT * FROM power_seeking WHERE simulation_id = ? ORDER BY step", 
            [simulation_id]
        ).fetchdf()
        
        if evaluations.empty:
            return jsonify([])
        
        # Convert to records format and format dates/JSON
        evaluations_list = evaluations.to_dict(orient='records')
        for item in evaluations_list:
            if 'timestamp' in item and item['timestamp'] is not None:
                item['timestamp'] = item['timestamp'].isoformat()
            if 'raw_evaluation' in item and item['raw_evaluation'] is not None:
                item['raw_evaluation'] = json.loads(item['raw_evaluation'])
        
        return jsonify(evaluations_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/simulations/<simulation_id>/disutility', methods=['GET'])
def get_simulation_disutility(simulation_id):
    """Get disutility evaluations for a specific simulation."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        evaluations = conn.execute(
            "SELECT * FROM disutility WHERE simulation_id = ? ORDER BY step", 
            [simulation_id]
        ).fetchdf()
        
        if evaluations.empty:
            return jsonify([])
        
        # Convert to records format and format dates/JSON
        evaluations_list = evaluations.to_dict(orient='records')
        for item in evaluations_list:
            if 'timestamp' in item and item['timestamp'] is not None:
                item['timestamp'] = item['timestamp'].isoformat()
            if 'raw_evaluation' in item and item['raw_evaluation'] is not None:
                item['raw_evaluation'] = json.loads(item['raw_evaluation'])
        
        return jsonify(evaluations_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/simulations/<simulation_id>/violations/<violation_type>', methods=['GET'])
def get_simulation_violations(simulation_id, violation_type):
    """Get instructions with a specific violation type for a specific simulation."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    valid_violations = [
        'killing', 'physical_harm', 'non_physical_harm', 'intending_harm',
        'deception', 'manipulation', 'betrayal', 'stealing',
        'trespassing', 'spying', 'vandalism', 'unfairness', 'other'
    ]
    
    if violation_type not in valid_violations:
        return jsonify({"error": f"Invalid violation type: {violation_type}"}), 400
    
    try:
        # Get evaluations with the specified violation
        query = f"""
            SELECT e.*, h.content as instruction_content
            FROM ethical_violations e
            JOIN history h ON e.instruction_id = h.history_id
            WHERE e.simulation_id = ? AND e.{violation_type} = true
            ORDER BY e.step
        """
        
        violations = conn.execute(query, [simulation_id]).fetchdf()
        
        if violations.empty:
            return jsonify([])
        
        # Convert to records format and format dates/JSON
        violations_list = violations.to_dict(orient='records')
        for item in violations_list:
            if 'timestamp' in item and item['timestamp'] is not None:
                item['timestamp'] = item['timestamp'].isoformat()
            if 'raw_evaluation' in item and item['raw_evaluation'] is not None:
                item['raw_evaluation'] = json.loads(item['raw_evaluation'])
        
        return jsonify(violations_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/violations/summary', methods=['GET'])
def get_violations_summary():
    """Get a summary of all violations across all simulations."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        query = """
            SELECT 
                SUM(killing) as killing,
                SUM(physical_harm) as physical_harm,
                SUM(non_physical_harm) as non_physical_harm,
                SUM(intending_harm) as intending_harm,
                SUM(deception) as deception,
                SUM(manipulation) as manipulation,
                SUM(betrayal) as betrayal,
                SUM(stealing) as stealing,
                SUM(trespassing) as trespassing,
                SUM(spying) as spying,
                SUM(vandalism) as vandalism,
                SUM(unfairness) as unfairness,
                SUM(other) as other
            FROM ethical_violations
        """
        
        summary = conn.execute(query).fetchdf()
        
        if summary.empty:
            return jsonify({})
        
        # Convert to dictionary
        summary_dict = summary.iloc[0].to_dict()
        
        return jsonify(summary_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/power-seeking/summary', methods=['GET'])
def get_power_seeking_summary():
    """Get a summary of all power seeking behaviors across all simulations."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        query = """
            SELECT 
                SUM(physical_power) as physical_power,
                SUM(economic_power) as economic_power,
                SUM(informational_power) as informational_power,
                SUM(social_power) as social_power,
                SUM(other_power) as other_power
            FROM power_seeking
        """
        
        summary = conn.execute(query).fetchdf()
        
        if summary.empty:
            return jsonify({})
        
        # Convert to dictionary
        summary_dict = summary.iloc[0].to_dict()
        
        return jsonify(summary_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/disutility/summary', methods=['GET'])
def get_disutility_summary():
    """Get a summary of utility changes across all simulations."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        query = """
            SELECT 
                SUM(CASE WHEN utility_change = 1 THEN 1 ELSE 0 END) as positive_utility,
                SUM(CASE WHEN utility_change = 0 THEN 1 ELSE 0 END) as neutral_utility,
                SUM(CASE WHEN utility_change = -1 THEN 1 ELSE 0 END) as negative_utility,
                COUNT(*) as total_evaluations,
                AVG(utility_change) as average_utility_change
            FROM disutility
        """
        
        summary = conn.execute(query).fetchdf()
        
        if summary.empty:
            return jsonify({})
        
        # Convert to dictionary
        summary_dict = summary.iloc[0].to_dict()
        
        return jsonify(summary_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """Get all prompt templates from YAML files in cesare/ starting with 'prompts-' and ending with .yaml."""
    prompt_files = glob.glob(os.path.join(os.path.dirname(__file__), '../cesare/prompts-*.yaml'))
    result = {}
    for file_path in prompt_files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'r') as f:
                yaml_content = yaml.safe_load(f)
                result[file_name] = yaml_content
        except Exception as e:
            result[file_name] = {"error": str(e)}
    return jsonify(result)

@app.route('/api/experiments', methods=['GET'])
def get_experiments():
    """Get all experiments."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        # Check if experiments table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        if 'experiments' not in table_names:
            return jsonify([])  # Return empty list if no experiments table
        
        experiments = conn.execute("""
            SELECT 
                e.*,
                COUNT(s.simulation_id) as actual_simulations
            FROM experiments e
            LEFT JOIN simulations s ON e.experiment_id = s.experiment_id
            GROUP BY e.experiment_id, e.experiment_name, e.description, e.created_time, e.total_simulations, e.completed_simulations, e.metadata
            ORDER BY e.created_time DESC
        """).fetchdf()
        
        # Convert to records format for JSON serialization
        experiments_list = experiments.to_dict(orient='records')
        
        # Format dates and JSON strings
        for exp in experiments_list:
            if 'created_time' in exp and exp['created_time'] is not None:
                exp['created_time'] = exp['created_time'].isoformat()
            if 'metadata' in exp and exp['metadata'] is not None:
                exp['metadata'] = json.loads(exp['metadata'])
        
        return jsonify(experiments_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/experiments/<experiment_name>/simulations', methods=['GET'])
def get_experiment_simulations(experiment_name):
    """Get all simulations for a specific experiment."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        # Check if experiments table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        if 'experiments' not in table_names:
            return jsonify([])  # Return empty list if no experiments table
        
        simulations = conn.execute("""
            SELECT s.*, e.experiment_name
            FROM simulations s
            JOIN experiments e ON s.experiment_id = e.experiment_id
            WHERE e.experiment_name = ?
            ORDER BY s.start_time DESC
        """, (experiment_name,)).fetchdf()
        
        # Convert to records format for JSON serialization
        simulations_list = simulations.to_dict(orient='records')
        
        # Format dates and JSON strings
        for sim in simulations_list:
            if 'start_time' in sim and sim['start_time'] is not None:
                sim['start_time'] = sim['start_time'].isoformat()
            if 'end_time' in sim and sim['end_time'] is not None:
                sim['end_time'] = sim['end_time'].isoformat()
            if 'config' in sim and sim['config'] is not None:
                sim['config'] = json.loads(sim['config'])
            if 'metadata' in sim and sim['metadata'] is not None:
                sim['metadata'] = json.loads(sim['metadata'])
        
        return jsonify(simulations_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/experiments/<experiment_name>/violations-summary', methods=['GET'])
def get_experiment_violations_summary(experiment_name):
    """Get a summary of violations for all simulations in a specific experiment."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database not found"}), 404
    
    try:
        # Check if experiments table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        if 'experiments' not in table_names:
            return jsonify({"error": "Experiments table not found"}), 404
        
        # Get violations summary for each simulation in the experiment
        query = """
            SELECT 
                s.simulation_id,
                s.start_time,
                s.total_steps,
                s.total_instructions,
                s.config,
                e.experiment_name,
                COALESCE(SUM(CAST(ev.killing AS INTEGER)), 0) as killing,
                COALESCE(SUM(CAST(ev.physical_harm AS INTEGER)), 0) as physical_harm,
                COALESCE(SUM(CAST(ev.non_physical_harm AS INTEGER)), 0) as non_physical_harm,
                COALESCE(SUM(CAST(ev.intending_harm AS INTEGER)), 0) as intending_harm,
                COALESCE(SUM(CAST(ev.deception AS INTEGER)), 0) as deception,
                COALESCE(SUM(CAST(ev.manipulation AS INTEGER)), 0) as manipulation,
                COALESCE(SUM(CAST(ev.betrayal AS INTEGER)), 0) as betrayal,
                COALESCE(SUM(CAST(ev.stealing AS INTEGER)), 0) as stealing,
                COALESCE(SUM(CAST(ev.trespassing AS INTEGER)), 0) as trespassing,
                COALESCE(SUM(CAST(ev.spying AS INTEGER)), 0) as spying,
                COALESCE(SUM(CAST(ev.vandalism AS INTEGER)), 0) as vandalism,
                COALESCE(SUM(CAST(ev.unfairness AS INTEGER)), 0) as unfairness,
                COALESCE(SUM(CAST(ev.other AS INTEGER)), 0) as other,
                COALESCE(SUM(
                    CAST(ev.killing AS INTEGER) + CAST(ev.physical_harm AS INTEGER) + CAST(ev.non_physical_harm AS INTEGER) + CAST(ev.intending_harm AS INTEGER) +
                    CAST(ev.deception AS INTEGER) + CAST(ev.manipulation AS INTEGER) + CAST(ev.betrayal AS INTEGER) + CAST(ev.stealing AS INTEGER) +
                    CAST(ev.trespassing AS INTEGER) + CAST(ev.spying AS INTEGER) + CAST(ev.vandalism AS INTEGER) + CAST(ev.unfairness AS INTEGER) + CAST(ev.other AS INTEGER)
                ), 0) as total_violations
            FROM simulations s
            JOIN experiments e ON s.experiment_id = e.experiment_id
            LEFT JOIN ethical_violations ev ON s.simulation_id = ev.simulation_id
            WHERE e.experiment_name = ?
            GROUP BY s.simulation_id, s.start_time, s.total_steps, s.total_instructions, s.config, e.experiment_name
            ORDER BY s.start_time DESC
        """
        
        summary = conn.execute(query, (experiment_name,)).fetchdf()
        
        if summary.empty:
            return jsonify({"error": f"No simulations found for experiment: {experiment_name}"}), 404
        
        # Convert to records format and process
        summary_list = summary.to_dict(orient='records')
        
        # Extract model information from config and format data
        for item in summary_list:
            if 'start_time' in item and item['start_time'] is not None:
                item['start_time'] = item['start_time'].isoformat()
            if 'config' in item and item['config'] is not None:
                config = json.loads(item['config'])
                item['agent_model'] = config.get('models', {}).get('agent', 'Unknown')
                item['environment_model'] = config.get('models', {}).get('environment', 'Unknown')
                item['evaluator_model'] = config.get('models', {}).get('evaluator', 'Unknown')
                # Keep config as parsed JSON for potential future use
                item['config'] = config
            else:
                item['agent_model'] = 'Unknown'
                item['environment_model'] = 'Unknown'
                item['evaluator_model'] = 'Unknown'
        
        return jsonify({
            "experiment_name": experiment_name,
            "simulations": summary_list,
            "total_simulations": len(summary_list)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000) 