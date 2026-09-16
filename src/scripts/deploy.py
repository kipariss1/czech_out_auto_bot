import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def docker_system_df():
    logger.info("Checking docker disk usage...")
    subprocess.run(["docker", "system", "df"], check=True)


def docker_cleanup():
    logger.info("Cleaning up unused docker images and build cache...")
    subprocess.run(["docker", "image", "prune", "-af"], check=True)
    subprocess.run(["docker", "builder", "prune", "-af"], check=True)


def git_pull():
    logger.info("Pulling latest changes from git...")
    subprocess.run(["git", "pull"], check=True)


def docker_compose_build():
    logger.info("Building docker images from scratch (no cache)...")
    subprocess.run(["docker", "compose", "build", "--no-cache"], check=True)


def docker_compose_up():
    logger.info("Recreating containers with new images...")
    subprocess.run(["docker", "compose", "up", "-d"], check=True)


def main():
    if not os.path.exists("docker-compose.yml"):
        logger.error("Please run this command from the project root directory (where docker-compose.yml is located).")
        sys.exit(1)

    try:
        docker_system_df()
        docker_cleanup()
        git_pull()
        docker_compose_build()
        docker_compose_up()
    except subprocess.CalledProcessError as e:
        logger.error(f"Deployment step failed: {e}")
        sys.exit(1)

    logger.info("Deployment complete.")


if __name__ == "__main__":
    main()
