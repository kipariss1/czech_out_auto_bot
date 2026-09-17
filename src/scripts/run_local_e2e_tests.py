import argparse
import logging
import os
import subprocess
import sys
import time
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

TEST_DB_CONTAINER = "postgres_test_db"
HEALTH_CHECK_RETRIES = 30
HEALTH_CHECK_INTERVAL_SECONDS = 2
WEB_APP_URL = "http://127.0.0.1:8000/"
WEB_APP_READY_RETRIES = 30
WEB_APP_READY_INTERVAL_SECONDS = 1
E2E_TESTS_DIR = os.path.join("tests", "e2e_smoke_tests")

_web_app_process: subprocess.Popen | None = None


def _test_env() -> dict:
    env = os.environ.copy()
    env["ENV"] = "test"
    env.setdefault("BOT_TOKEN", "test-token")
    env["PYTHONPATH"] = os.getcwd()
    return env


def _npm_env() -> dict:
    from src.database_utils.postgres_database import LOCAL_TEST_POSTGRES_HOST, LOCAL_TEST_POSTGRES_PORT
    from src.settings.settings import settings

    env = os.environ.copy()
    postgres_data = settings.postgres_data
    env["POSTGRES_USER"] = postgres_data["user"]
    env["POSTGRES_PASSWORD"] = postgres_data["password"]
    env["POSTGRES_DB"] = postgres_data["db"]
    env["TEST_POSTGRES_HOST"] = LOCAL_TEST_POSTGRES_HOST
    env["TEST_POSTGRES_PORT"] = str(LOCAL_TEST_POSTGRES_PORT)
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


def start_web_app() -> bool:
    global _web_app_process
    logger.info("Starting web app against the test database...")
    _web_app_process = subprocess.Popen(
        ["uv", "run", "uvicorn", "web_app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=_test_env(),
    )

    for _ in range(WEB_APP_READY_RETRIES):
        try:
            with urllib.request.urlopen(WEB_APP_URL, timeout=1):
                logger.info("Web app is ready.")
                return True
        except Exception:
            time.sleep(WEB_APP_READY_INTERVAL_SECONDS)

    logger.error("Web app did not become ready in time.")
    return False


def run_smoke_e2e_tests(web_app_ready: bool, headed: bool) -> bool:
    if not web_app_ready:
        logger.error("Skipping smoke e2e tests — web app never became ready.")
        return False

    logger.info("Running Playwright smoke e2e tests...")
    npm_env = _npm_env()
    if not os.path.isdir(os.path.join(E2E_TESTS_DIR, "node_modules")):
        subprocess.run(["npm", "ci"], cwd=E2E_TESTS_DIR, env=npm_env, check=True)
    subprocess.run(["npx", "playwright", "install", "--with-deps"], cwd=E2E_TESTS_DIR, env=npm_env, check=True)
    subprocess.run(["npm", "run", "build"], cwd=E2E_TESTS_DIR, env=npm_env, check=True)
    test_command = ["npm", "run", "test:playwright"]
    if headed:
        test_command += ["--", "--headed"]
    result = subprocess.run(test_command, cwd=E2E_TESTS_DIR, env=npm_env)
    return result.returncode == 0


def teardown() -> None:
    global _web_app_process
    if _web_app_process is not None:
        logger.info("Stopping web app process...")
        _web_app_process.terminate()
        try:
            _web_app_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _web_app_process.kill()
        _web_app_process = None

    logger.info("Tearing down %s...", TEST_DB_CONTAINER)
    subprocess.run(["docker", "rm", "-f", TEST_DB_CONTAINER], capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headed", action="store_true", help="Run Playwright tests with a visible browser.")
    args = parser.parse_args()

    if not os.path.exists("docker-compose.yml"):
        logger.error("Please run this command from the project root directory (where docker-compose.yml is located).")
        sys.exit(1)

    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ["ENV"] = "test"

    web_app_ready = False
    smoke_passed = False
    try:
        ensure_empty_test_db()
        init_schema()
        web_app_ready = start_web_app()
        smoke_passed = run_smoke_e2e_tests(web_app_ready, headed=args.headed)
    finally:
        teardown()

    logger.info("----- E2E test summary -----")
    logger.info("web_app_ready: %s", web_app_ready)
    logger.info("smoke_e2e_tests: %s", "PASSED" if smoke_passed else "FAILED")

    if not smoke_passed:
        sys.exit(1)

    logger.info("Smoke e2e suite passed.")


if __name__ == "__main__":
    main()
