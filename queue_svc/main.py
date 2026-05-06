import asyncio
import logging
from datetime import datetime, timedelta, timezone

import click

from queue_svc.parser.bazos_parser import BazosParser
from queue_svc.worker.bazos_worker import BazosWorker
from src.database_utils import db_handler
from src.settings.logging_config import configure_logging


logger = logging.getLogger(__name__)
DEFAULT_INTERVAL_SECONDS = 7200


async def _run_parser() -> None:
    parser_started_at = datetime.now(timezone.utc)
    logger.info(
        "Queue parser step started parser_started_at=%s",
        _format_timestamp(parser_started_at),
    )
    try:
        parser = BazosParser()
        await parser.parse()
    finally:
        db_handler.close_db_connection()
        parser_finished_at = datetime.now(timezone.utc)
        logger.info(
            "Queue parser step finished parser_started_at=%s parser_finished_at=%s elapsed_seconds=%.3f",
            _format_timestamp(parser_started_at),
            _format_timestamp(parser_finished_at),
            (parser_finished_at - parser_started_at).total_seconds(),
        )


async def _run_worker() -> None:
    worker_started_at = datetime.now(timezone.utc)
    logger.info(
        "Queue worker step started worker_started_at=%s",
        _format_timestamp(worker_started_at),
    )
    try:
        worker = BazosWorker()
        await worker.process_queue()
    finally:
        db_handler.close_db_connection()
        worker_finished_at = datetime.now(timezone.utc)
        logger.info(
            "Queue worker step finished worker_started_at=%s worker_finished_at=%s elapsed_seconds=%.3f",
            _format_timestamp(worker_started_at),
            _format_timestamp(worker_finished_at),
            (worker_finished_at - worker_started_at).total_seconds(),
        )


async def run_cycle() -> None:
    await _run_parser()
    await _run_worker()


def _format_timestamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


async def run_forever(interval_seconds: int = DEFAULT_INTERVAL_SECONDS) -> None:
    interval = timedelta(seconds=interval_seconds)
    while True:
        cycle_started_at = datetime.now(timezone.utc)
        logger.info(
            "Queue cycle started cycle_started_at=%s",
            _format_timestamp(cycle_started_at),
        )

        try:
            await run_cycle()
        except Exception:
            logger.exception("Queue cycle failed")

        cycle_finished_at = datetime.now(timezone.utc)
        elapsed = cycle_finished_at - cycle_started_at
        sleep_seconds = max(0, (interval - elapsed).total_seconds())

        logger.info(
            "Queue cycle finished cycle_started_at=%s cycle_finished_at=%s elapsed_seconds=%.3f",
            _format_timestamp(cycle_started_at),
            _format_timestamp(cycle_finished_at),
            elapsed.total_seconds(),
        )

        if sleep_seconds == 0:
            logger.info(
                "Queue cycle exceeded interval interval_seconds=%s; starting next cycle immediately",
                interval_seconds,
            )
            continue

        next_cycle_at = cycle_finished_at + timedelta(seconds=sleep_seconds)
        logger.info(
            "Queue cycle finished before interval; sleeping sleep_seconds=%.3f next_cycle_at=%s",
            sleep_seconds,
            _format_timestamp(next_cycle_at),
        )
        await asyncio.sleep(sleep_seconds)


@click.command()
@click.option(
    "--interval-seconds",
    envvar="INTERVAL_SECONDS",
    default=DEFAULT_INTERVAL_SECONDS,
    show_default=True,
    type=click.IntRange(min=1),
)
def cli(interval_seconds: int) -> None:
    configure_logging()
    logger.info("Queue service started interval_seconds=%s", interval_seconds)
    asyncio.run(run_forever(interval_seconds))


if __name__ == "__main__":
    cli()
