import os
import shutil

def cleanup():
    """
    Simulates a cleanup script on a remote agent.
    Demonstrates 'Smart Resolution' via file matching in agent_scripts/
    """
    print("🧹 Starting remote cleanup session...")
    
    # Simulate finding files
    files_to_clean = ["/tmp/test.jmx", "/tmp/results.jtl", "/tmp/test.js"]
    deleted = []
    
    for f in files_to_clean:
        if os.path.exists(f):
            os.remove(f)
            deleted.append(f)
            
    return {
        "status": "success",
        "deleted_files": deleted,
        "message": f"Cleaned up {len(deleted)} temporary files"
    }

# Execute
result = cleanup()
