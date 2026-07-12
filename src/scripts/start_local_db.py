import subprocess
import time
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def start_postgres():
    logger.info("Starting postgres_db container with exposed port 5432...")
    
    # Create temporary override to expose port 5432
    override_file = "docker-compose.override.yml"
    override_content = """
services:
  postgres_db:
    ports:
      - "5432:5432"
"""
    with open(override_file, "w") as f:
        f.write(override_content)

    try:
        subprocess.run(["docker", "compose", "up", "-d", "postgres_db"], check=True)
    finally:
        if os.path.exists(override_file):
            os.remove(override_file)

def wait_for_healthy():
    logger.info("Waiting for postgres_db to become healthy...")
    for _ in range(30):
        res = subprocess.run(
            ["docker", "inspect", "--format={{json .State.Health.Status}}", "postgres_db"],
            capture_output=True, text=True
        )
        status = res.stdout.strip().strip('"')
        if status == "healthy":
            logger.info("Database is healthy!")
            return
        time.sleep(2)
    logger.error("Database did not become healthy in time.")
    sys.exit(1)

def run_init_db():
    logger.info("Running src.database_utils.init_db...")
    try:
        from src.database_utils.init_db import init_db
        init_db()
        logger.info("Database initialization complete.")
    except ImportError as e:
        logger.warning(f"Failed to import init_db natively: {e}")
        logger.info("Attempting via subprocess...")
        subprocess.run(["uv", "run", "python", "-m", "src.database_utils.init_db"], check=True)
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        sys.exit(1)

def main():
    # If run via console script, we assume the user is in the project root.
    # We can ensure this by checking for docker-compose.yml
    if not os.path.exists("docker-compose.yml"):
        logger.error("Please run this command from the project root directory (where docker-compose.yml is located).")
        sys.exit(1)

    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    start_postgres()
    wait_for_healthy()
    run_init_db()

if __name__ == "__main__":
    main()
