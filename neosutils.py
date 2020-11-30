from typing import List
from urllib.parse import quote


def formatForNeos(list: List[List]):
    f = ""
    for i in list:
        f += ",".join([quote(str(j)) for j in i])
        f += ',\r\n'
    return f
