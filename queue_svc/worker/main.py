import click
from queue_svc.worker import bw
import asyncio

@click.command
def cli():
    asyncio.run(bw.process_queue())

if __name__ == "__main__":
    cli()