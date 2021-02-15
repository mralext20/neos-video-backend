import re
from datetime import datetime
from typing import List

import aiohttp
import config
from isodate import parse_duration

import database as db
import videoSources
from utils import grouper

BASEPARAMS = {'key': config.googleApiKey}
PLAYLISTPARAMS = {**BASEPARAMS, 'part': ['snippet', 'contentDetails'], 'maxResults': 50}
VIDEOSPARAMS = {**BASEPARAMS, 'part': ['contentDetails']}


async def getPlaylist(playlistID, session: aiohttp.ClientSession, nextPageToken="") -> List[db.Video]:
    """
    given a playlist, returns db.Video objetcs in a list of that playlist's content.
    """
    async with session.get(
        "https://www.googleapis.com/youtube/v3/playlistItems",
        params={**PLAYLISTPARAMS, 'playlistId': playlistID, 'pageToken': nextPageToken},
    ) as response:
        data = await response.json()
    items = [db.Video.from_yt(item) for item in data['items']]
    if 'nextPageToken' in data:
        items += await getPlaylist(playlistID, session, data['nextPageToken'])
    return items


async def getDuration(videos: List[db.Video], session: aiohttp.ClientSession) -> List[db.Video]:
    """
    given a List[db.Video], extends the data on them to include the duration, and returns it.
    """
    durations = {}
    for group in grouper(videos, 50):
        async with session.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={**VIDEOSPARAMS, 'id': ','.join([i.vidId for i in group])},
        ) as response:
            data = await response.json()
            durations = {**{i['id']: i['contentDetails']['duration'] for i in data['items']}, **durations}
    for vid in videos:
        vid.duration = parse_duration(durations[vid.vidId])
    return videos


async def update() -> int:
    """updates database with newest videos from all playlists. also clears videos no longer part of the playlists"""
    collected: List[db.Video] = []
    async with aiohttp.ClientSession() as session:
        for playlistId in videoSources.youtubePlaylists:
            collected += await getPlaylist(playlistId, session)
        collected = await getDuration(collected, session)
        await db.update_all_data(collected)
    return len(collected)
