from parser import bp
import asyncio
import click


@click.command()
def cli():
    asyncio.run(bp.parse())

if __name__ == '__main__':
    cli()