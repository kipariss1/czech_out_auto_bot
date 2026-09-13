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


def _test_env() -> dict:
    env = os.environ.copy()
    env["ENV"] = "test"
    env.setdefault("BOT_TOKEN", "test-token")
    env["PYTHONPATH"] = os.getcwd()
    return env


def ensure_empty_test_db() -> None:
    logger.info("Recreating an empty %s container...", TEST_DB_CONTAINER)
    subprocess.run(["docker", "rm", "-f", TEST_DB_CONTAINER], capture_output=True, text=True)
    subprocess.run(["docker", "compose", "--profile", "test", "up", "-d", TEST_DB_CONTAINER], check=True)

    for _ in range(HEALTH_CHECK_RETRIES):
        res = subprocess.run(
            ["docker", "inspect", "--format={{json .State.Health.Status}}", TEST_DB_CONTAINER],
            capture_output=True, text=True,
        )
        status = res.stdout.strip().strip('"')
        if status == "healthy":
            logger.info("%s is healthy.", TEST_DB_CONTAINER)
            return
        time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    logger.error("%s did not become healthy in time.", TEST_DB_CONTAINER)
    sys.exit(1)


def init_schema() -> None:
    logger.info("Initializing test database schema...")
    from src.database_utils.init_db import init_db
    init_db()
    # Alembic's fileConfig() (invoked by init_db() above) disables every logger not
    # explicitly listed in alembic.ini and resets the root logger's level to WARNING —
    # undo both so this script's own INFO logs keep showing afterward.
    logger.disabled = False
    logger.setLevel(logging.INFO)


def run_unit_tests() -> bool:
    logger.info("Running unit tests...")
    result = subprocess.run(["uv", "run", "pytest", "tests/unit_tests", "-v"], env=_test_env())
    return result.returncode == 0


def run_integration_tests() -> bool:
    logger.info("Running integration tests...")
    result = subprocess.run(["uv", "run", "pytest", "tests/integration_tests", "-v"], env=_test_env())
    return result.returncode == 0


def teardown() -> None:
    logger.info("Tearing down %s...", TEST_DB_CONTAINER)
    subprocess.run(["docker", "rm", "-f", TEST_DB_CONTAINER], capture_output=True, text=True)


def main():
    if not os.path.exists("docker-compose.yml"):
        logger.error("Please run this command from the project root directory (where docker-compose.yml is located).")
        sys.exit(1)

    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ["ENV"] = "test"

    results = {}
    try:
        ensure_empty_test_db()
        init_schema()
        results["unit_tests"] = run_unit_tests()
        results["integration_tests"] = run_integration_tests()
    finally:
        teardown()

    failed = [name for name, passed in results.items() if not passed]

    logger.info("----- Component test summary -----")
    for name, passed in results.items():
        logger.info("%s: %s", name, "PASSED" if passed else "FAILED")

    if failed:
        logger.error("Failed suites: %s", ", ".join(failed))
        sys.exit(1)

    logger.info("All component test suites passed.")


if __name__ == "__main__":
    main()
