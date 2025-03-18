import os
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Path to the file that will store last run timestamps
LAST_RUN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             "storage", "last_run.json")

def _ensure_storage_dir():
    """Ensure the storage directory exists"""
    storage_dir = os.path.dirname(LAST_RUN_FILE)
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

def _load_last_runs():
    """Load the last run times from the JSON file"""
    _ensure_storage_dir()
    if not os.path.exists(LAST_RUN_FILE):
        return {}
    
    try:
        with open(LAST_RUN_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.warning(f"Could not read last run file at {LAST_RUN_FILE}, creating new one")
        return {}

def _save_last_runs(last_runs):
    """Save the last run times to the JSON file"""
    _ensure_storage_dir()
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump(last_runs, f)

def get_last_run(task_name):
    """Get the timestamp of when a task was last run
    
    Args:
        task_name: The name of the task
        
    Returns:
        datetime or None: The timestamp of when the task was last run,
                          or None if it has never been run
    """
    last_runs = _load_last_runs()
    timestamp_str = last_runs.get(task_name)
    
    if timestamp_str:
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            logger.error(f"Invalid timestamp format for task {task_name}: {timestamp_str}")
    
    return None

def update_last_run(task_name):
    """Update the last run time for a task to the current time
    
    Args:
        task_name: The name of the task
    """
    last_runs = _load_last_runs()
    last_runs[task_name] = datetime.utcnow().isoformat()
    _save_last_runs(last_runs)
    logger.info(f"Updated last run time for task {task_name}")

def should_run_task(task_name, interval_hours=24):
    """Check if a task should be run based on its last run time
    
    Args:
        task_name: The name of the task
        interval_hours: The minimum interval in hours between runs
        
    Returns:
        bool: True if the task should be run, False otherwise
    """
    last_run = get_last_run(task_name)
    
    # If the task has never been run, or the last run time is invalid, run it
    if not last_run:
        logger.info(f"Task {task_name} has never been run, should run now")
        return True
    
    # Check if enough time has passed since the last run
    next_run_time = last_run + timedelta(hours=interval_hours)
    should_run = datetime.utcnow() >= next_run_time
    
    if should_run:
        logger.info(f"Task {task_name} last ran at {last_run}, should run now")
    else:
        hours_until_next_run = (next_run_time - datetime.utcnow()).total_seconds() / 3600
        logger.info(f"Task {task_name} last ran at {last_run}, next run in {hours_until_next_run:.2f} hours")
    
    return should_run 