import asyncio
import click

from queue_svc.parser import bp
from src.settings.logging_config import configure_logging


@click.command()
def cli():
    configure_logging()
    asyncio.run(bp.parse())

if __name__ == '__main__':
    cli()
