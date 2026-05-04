import asyncio
import click

from queue_svc.worker import bw
from src.settings.logging_config import configure_logging


@click.command()
def cli():
    configure_logging()
    asyncio.run(bw.process_queue())

if __name__ == "__main__":
    cli()
