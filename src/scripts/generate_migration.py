import argparse
import logging
import os
import sys

from alembic import command
from src.database_utils.migrations import get_alembic_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    if not os.path.exists("alembic.ini"):
        logger.error("Please run this command from the project root directory (where alembic.ini is located).")
        sys.exit(1)

    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    parser = argparse.ArgumentParser(description="Generate a new Alembic migration.")
    parser.add_argument(
        "-m", "--message",
        required=True,
        help="Migration message describing the changes"
    )
    args = parser.parse_args()

    logger.info(f"Generating new migration with message: '{args.message}'")
    try:
        command.revision(get_alembic_config(), message=args.message, autogenerate=True)
        logger.info("Migration generated successfully.")
    except Exception as e:
        logger.error(f"Failed to generate migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
