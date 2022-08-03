import asyncio
from math import ceil
from typing import Generator, Iterable, List, TypeVar
from urllib.parse import quote

_T = TypeVar("_T")

priCacheData = {}
priCacheDt = None


def grouper(iterable: Iterable[_T], n: int) -> Generator[Iterable[_T], None, None]:
    """
    given a iterable, yield that iterable back in chunks of size n. last item will be any size.
    """
    for i in range(ceil(len(iterable) / n)):
        yield iterable[i * n : i * n + n]


def formatForNeos(list: Iterable[Iterable]) -> str:
    f = ""
    for i in list:
        f += ",".join([quote(str(j)) for j in i])
        f += ",\r\n"
    return f


def periodic(period):
    """from https://stackoverflow.com/a/53293518"""

    def scheduler(fcn):
        async def wrapper(*args, **kwargs):
            while True:
                asyncio.create_task(fcn(*args, **kwargs))
                print(f"scheduled {fcn.__name__} in {period/60} minutes")
                await asyncio.sleep(period)

        return wrapper

    return scheduler
