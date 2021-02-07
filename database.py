import datetime
import re
from dataclasses import dataclass
from typing import List

import aiosqlite

PATH = "cache.db"

SCHEMA: str = open("schema.sql").read()

YTLINKREGEX = re.compile(r"((http(s)?://)?)(www.)?((youtube.com/)|(youtu.be/))([\S]+)")


class VideoNotFound(Exception):
    pass


@dataclass
class Video:
    vidId: str
    title: str
    description: str
    channel: str
    publishDate: datetime.datetime
    thumbnail: str
    duration: datetime.timedelta

    @classmethod
    def from_row(cls, row: aiosqlite.Row):
        return cls(
            row[0],
            row[1],
            row[2],
            row[3],
            datetime.datetime.fromtimestamp(row[4]),
            row[5],
            datetime.timedelta(seconds=row[6]),
        )

    @classmethod
    def from_yt(cls, data: dict):
        snip = data["snippet"]
        return cls(
            data["contentDetails"]["videoId"],
            snip["title"],
            snip["description"],
            snip["channelTitle"],
            datetime.datetime.strptime(data["contentDetails"]["videoPublishedAt"], "%Y-%m-%dT%H:%M:%SZ"),
            snip["thumbnails"]["medium"]["url"],
            None,  # will be filled in later with another request to yt
        )

    async def get_related_videos(self) -> List["Video"]:
        matches = YTLINKREGEX.findall(self.description)
        res = []
        for i in matches:
            try:
                res.append(await getVideoById(i[7]))
            except VideoNotFound:
                pass
        return res

    @property
    def as_tuple(self):
        return (
            self.vidId,
            self.title,
            self.description,
            self.channel,
            self.publishDate.timestamp(),
            self.thumbnail,
            self.duration.total_seconds(),
        )


async def saveVideo(v: Video):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute(
            """INSERT INTO videos
                           VALUES(?, ?, ?, ?, ?, ?, ?)""",
            v.as_tuple,
        )
        await conn.commit()


async def saveManyVideo(videos: List[Video], conn: aiosqlite.Connection = None):
    if not conn:
        conn = await aiosqlite.connect(PATH)
    videoset = set([v.as_tuple for v in videos])
    await conn.executemany("""INSERT INTO videos VALUES (?,?,?,?,?,?,?)""", videoset)
    await conn.commit()


async def getAllVideos() -> List[Video]:
    async with aiosqlite.connect(PATH) as conn:
        res = await conn.execute("SELECT * FROM videos;")
        return [Video.from_row(row) for row in await res.fetchall()]


async def getVideoById(videoId: str) -> Video:
    async with aiosqlite.connect(PATH) as conn:
        res = await conn.execute("""SELECT * FROM videos WHERE id=?""", (videoId,))
        res = await res.fetchone()
        if not res:
            raise VideoNotFound
        return Video.from_row(res)


async def search(term: str) -> List[Video]:
    async with aiosqlite.connect(PATH) as conn:
        res = await conn.execute(
            """
                with original as (
                    select
                        rowid,
                        *
                    from [videos]
                )
                select
                    [original].*
                from
                    [original]
                    join [videos_fts] on [original].rowid = [videos_fts].rowid
                where
                    [videos_fts] match ?
                order by
                    [videos_fts].rank
            """,
            (term,),
        )
        return [Video.from_row(tuple(list(row)[1:])) for row in await res.fetchall()]


async def start():
    async with aiosqlite.connect(PATH) as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()


async def emptyDatabase():
    async with aiosqlite.connect(PATH) as conn:
        conn.executeScript("""DELETE FROM videos""")
        await conn.commit()


async def update_all_data(videos: List[Video]):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute("DELETE FROM videos")
        await saveManyVideo(videos, conn)
