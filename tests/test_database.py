import datetime
import os
import unittest
from typing import List

import database as db


class TestDatabase(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def get_videos() -> List[db.Video]:
        return [
            db.Video(
                'jUUe6TuRlgU',
                "2kliksphilip's Games of 2020",
                "see also , https://www.youtube.com/watch?v=dQw4w9WgXcQ .",
                "2kliksphilip",
                datetime.datetime(2020, 12, 31, 5, 2),
                "https://i.ytimg.com/vi/jUUe6TuRlgU/hqdefault.jpg",
                datetime.timedelta(minutes=24, seconds=33),
            ),
            db.Video(
                'dQw4w9WgXcQ',
                "Rick Astley - Never Gonna Give You Up (Video)",
                """Lyrics:
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you""",
                "Official Rick Astley ",
                datetime.datetime(2009, 10, 24, 5, 2),
                "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                datetime.timedelta(minutes=3, seconds=32),
            ),
            db.Video(
                'videooo',
                "another test video",
                "hello world!",
                "alex from alaska",
                datetime.datetime(2021, 1, 1, 5, 2),
                "https://i.ytimg.com/vi/videooo/hqdefault.jpg",
                datetime.timedelta(minutes=1, seconds=20),
            ),
        ]

    async def asyncSetUp(self):
        self.vids = self.get_videos()
        await db.start()
        await db.saveManyVideo(self.vids)

    async def test_getSingle(self):
        for vid in self.vids:
            self.assertSequenceEqual(vid.as_tuple, (await db.getVideoById(vid.vidId)).as_tuple)

    async def test_getAll(self):
        source = {vid.vidId: vid for vid in self.vids}
        ret = {vid.vidId: vid for vid in await db.getAllVideos()}
        self.assertDictEqual(source, ret)

    async def test_raisesMissing(self):
        with self.assertRaises(db.VideoNotFound):
            await db.getVideoById("NOTFOUND")

    def setUp(self):
        db.PATH = 'testdb.db'

    def tearDown(self):
        os.remove('testdb.db')
