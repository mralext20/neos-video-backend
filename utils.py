import asyncio
from typing import List
from urllib.parse import quote


def formatForNeos(list: List[List]):
    f = ""
    for i in list:
        f += ",".join([quote(str(j)) for j in i])
        f += ',\r\n'
    return f


def periodic(period):
    """from https://stackoverflow.com/a/53293518 """
    def scheduler(fcn):

        async def wrapper(*args, **kwargs):

            while True:
                asyncio.create_task(fcn(*args, **kwargs))
                print(f"scheduled {fcn} in {period/60} minutes")
                await asyncio.sleep(period)

        return wrapper

    return scheduler
