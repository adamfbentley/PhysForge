"""
Quick diagnostic script to check the PhysForge demo app database
"""
import sqlite3
import json

DB_PATH = "physforge.db"

try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if database exists and has tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print("Tables in database:", tables)
    
    # Check jobs
    c.execute("SELECT COUNT(*) FROM jobs")
    job_count = c.fetchone()[0]
    print(f"\nTotal jobs: {job_count}")
    
    # Get latest completed job
    c.execute("""
        SELECT id, status, dataset_name, result_data 
        FROM jobs 
        WHERE status = 'completed'
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    row = c.fetchone()
    if row:
        print(f"\nLatest completed job:")
        print(f"  ID: {row[0]}")
        print(f"  Status: {row[1]}")
        print(f"  Dataset: {row[2]}")
        print(f"  Has result_data: {row[3] is not None}")
        
        if row[3]:
            result = json.loads(row[3])
            print(f"\n  Result keys: {list(result.keys())}")
            print(f"  Equation: {result.get('equation', 'N/A')}")
            print(f"  Coefficients: {result.get('coefficients', {})}")
            print(f"  R²: {result.get('r_squared', 'N/A')}")
    else:
        print("\nNo completed jobs found")
    
    # Check all jobs status
    c.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    status_counts = c.fetchall()
    print(f"\nJobs by status:")
    for status, count in status_counts:
        print(f"  {status}: {count}")
    
    conn.close()
    
except FileNotFoundError:
    print(f"Database file '{DB_PATH}' not found. Run the app first to create it.")
except Exception as e:
    print(f"Error: {e}")
