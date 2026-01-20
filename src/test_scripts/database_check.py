"""
Database connectivity check
Language: Python
"""
import psycopg2
import time

def check_database():
    """Check PostgreSQL database connectivity"""
    start = time.time()
    
    try:
        conn = psycopg2.connect(
            dbname="production",
            user="readonly",
            host="localhost",
            password="password"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        duration = time.time() - start
        
        return {
            "duration": duration,
            "connected": True,
            "response_time_ms": duration * 1000,
            "check_type": "database",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "duration": time.time() - start,
            "connected": False,
            "error": str(e),
            "check_type": "database",
            "timestamp": time.time()
        }

result = check_database()
