from cesare.utils.database import SimulationDB

db = SimulationDB('logs/simulations.duckdb')
try:
    schema = db._execute_with_retry('DESCRIBE simulations').fetchdf()
    print('Simulations table schema:')
    print(schema)
    print()
    eval_schema = db._execute_with_retry('DESCRIBE evaluations').fetchdf()
    print('Evaluations table schema:')
    print(eval_schema)
finally:
    db.close() 