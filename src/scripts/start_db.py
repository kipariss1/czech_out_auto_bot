import logging
import os
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

PRODUCTION_DB_CONTAINER = "postgres_db"
LOCAL_TEST_DB_CONTAINER = "postgres_test_db"
HEALTH_CHECK_RETRIES = 30
HEALTH_CHECK_INTERVAL_SECONDS = 2


def _container_health_status(container: str) -> str:
    res = subprocess.run(
        ["docker", "inspect", "--format={{json .State.Health.Status}}", container],
        capture_output=True, text=True,
    )
    return res.stdout.strip().strip('"')


def _wait_for_healthy(container: str) -> None:
    logger.info("Waiting for %s to become healthy...", container)
    for _ in range(HEALTH_CHECK_RETRIES):
        if _container_health_status(container) == "healthy":
            logger.info("%s is healthy.", container)
            return
        time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    logger.error("%s did not become healthy in time.", container)
    sys.exit(1)


def start_production_db() -> None:
    logger.info("Starting %s container with exposed port 5432...", PRODUCTION_DB_CONTAINER)

    # postgres_db doesn't publish a port in docker-compose.yml (other services reach it over
    # the Compose network), so expose it temporarily via an override for host-side access.
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
        subprocess.run(["docker", "compose", "up", "-d", PRODUCTION_DB_CONTAINER], check=True)
    finally:
        if os.path.exists(override_file):
            os.remove(override_file)

    _wait_for_healthy(PRODUCTION_DB_CONTAINER)


def start_or_reuse_local_test_db() -> None:
    if _container_health_status(LOCAL_TEST_DB_CONTAINER) == "healthy":
        logger.info("%s is already healthy — reusing it.", LOCAL_TEST_DB_CONTAINER)
        return

    logger.info("Starting %s container...", LOCAL_TEST_DB_CONTAINER)
    subprocess.run(["docker", "compose", "--profile", "test", "up", "-d", LOCAL_TEST_DB_CONTAINER], check=True)
    _wait_for_healthy(LOCAL_TEST_DB_CONTAINER)


def run_init_db() -> None:
    logger.info("Running src.database_utils.init_db...")
    try:
        from src.database_utils.init_db import init_db
        init_db()
        # Alembic's fileConfig() (invoked by init_db() above) disables every logger not
        # explicitly listed in alembic.ini and resets the root logger's level to WARNING —
        # undo both so this script's own INFO logs keep showing afterward.
        logger.disabled = False
        logger.setLevel(logging.INFO)
        logger.info("Database initialization complete.")
    except ImportError as e:
        logger.warning(f"Failed to import init_db natively: {e}")
        logger.info("Attempting via subprocess...")
        subprocess.run(["uv", "run", "python", "-m", "src.database_utils.init_db"], check=True, env=os.environ.copy())
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

    if os.environ.get("ENV", "local") in ("local", "test"):
        start_or_reuse_local_test_db()
    else:
        start_production_db()

    run_init_db()


def main_test_db():
    os.environ["ENV"] = "test"
    main()


if __name__ == "__main__":
    main()
