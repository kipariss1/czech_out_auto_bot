import logging
import os
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

TEST_DB_CONTAINER = "postgres_test_db"
HEALTH_CHECK_RETRIES = 30
HEALTH_CHECK_INTERVAL_SECONDS = 2


def _container_health_status() -> str:
    res = subprocess.run(
        ["docker", "inspect", "--format={{json .State.Health.Status}}", TEST_DB_CONTAINER],
        capture_output=True, text=True,
    )
    return res.stdout.strip().strip('"')


def start_or_reuse_test_db() -> None:
    if _container_health_status() == "healthy":
        logger.info("%s is already healthy — reusing it.", TEST_DB_CONTAINER)
        return

    logger.info("Starting %s container...", TEST_DB_CONTAINER)
    subprocess.run(["docker", "compose", "--profile", "test", "up", "-d", TEST_DB_CONTAINER], check=True)

    for _ in range(HEALTH_CHECK_RETRIES):
        if _container_health_status() == "healthy":
            logger.info("%s is healthy.", TEST_DB_CONTAINER)
            return
        time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    logger.error("%s did not become healthy in time.", TEST_DB_CONTAINER)
    sys.exit(1)


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
        env = os.environ.copy()
        env["ENV"] = "test"
        subprocess.run(["uv", "run", "python", "-m", "src.database_utils.init_db"], check=True, env=env)
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        sys.exit(1)


def main():
    if not os.path.exists("docker-compose.yml"):
        logger.error("Please run this command from the project root directory (where docker-compose.yml is located).")
        sys.exit(1)

    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ["ENV"] = "test"

    start_or_reuse_test_db()
    run_init_db()


if __name__ == "__main__":
    main()
