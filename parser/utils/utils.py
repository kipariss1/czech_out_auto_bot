import re
from typing import Iterable, List, overload

INZERAT_ID_RE = re.compile(r"/inzerat/(\d+)/")


@overload
def extract_bazos_ids(link: str) -> int: ...
    

@overload
def extract_bazos_ids(links: Iterable[str]) -> List[int]: ...


def extract_bazos_ids(links):
    if isinstance(links, str):
        match = INZERAT_ID_RE.search(links)
        if not match:
            raise ValueError(f"Not correct format of the link: {links}")
        return int(match.group(1))

    ids: List[int] = []
    for link in links:
        match = INZERAT_ID_RE.search(link)
        if match:
            ids.append(int(match.group(1)))

    return ids
