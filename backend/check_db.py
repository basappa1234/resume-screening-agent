import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('screening_history.db')
cursor = conn.cursor()

# Check sessions table
print("=== Sessions Table ===")
cursor.execute("SELECT * FROM sessions")
sessions = cursor.fetchall()
print(f"Found {len(sessions)} sessions")
for session in sessions:
    print(f"ID: {session[0]}, Title: {session[2]}, Num Resumes: {session[3]}")
    try:
        session_data = json.loads(session[4]) if session[4] else {}
        print(f"  Session Data: {session_data}")
        if 'job_desc' in session_data:
            print(f"  Job Desc: {session_data['job_desc']}")
    except Exception as e:
        print(f"  Error parsing session data: {e}")
    print()

# Check results table
print("=== Results Table ===")
cursor.execute("SELECT * FROM results")
results = cursor.fetchall()
print(f"Found {len(results)} results")
for result in results[:5]:  # Show first 5 results
    print(f"Session ID: {result[1]}, Candidate: {result[3]}, Score: {result[4]}")

conn.close()