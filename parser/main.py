from . import bazos_parser
import asyncio


if __name__ == '__main__':
    asyncio.run(bazos_parser.parse())