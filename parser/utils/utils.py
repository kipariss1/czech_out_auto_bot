import re
from typing import Iterable, List

INZERAT_ID_RE = re.compile(r"/inzerat/(\d+)/")


def extract_bazos_id(link: str) -> int:
    match = INZERAT_ID_RE.search(link)
    if not match:
        raise ValueError(f"Wrong format of the link: {link}")
    return int(match.group(1))


def extract_bazos_ids(links: Iterable[str]) -> List[int]:
    ids: List[int] = []

    for link in links:
        ids.append(extract_bazos_id(link))

    return ids