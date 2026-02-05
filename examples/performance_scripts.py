import os
import time

def custom_validation(context):
    """
    Custom validation logic intended to run on a remote agent.
    Demonstrates 'Smart Resolution' via method matching.
    """
    print("Running smart-resolved custom validation...")
    
    # Access context variables
    env = context.get('env', 'dev')
    
    # Perform some 'work'
    start_time = time.time()
    time.sleep(1) 
    
    return {
        "status": "success",
        "env_checked": env,
        "duration": time.time() - start_time,
        "message": "Smart resolution successful!"
    }
