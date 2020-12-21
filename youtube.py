import re
from datetime import datetime

import aiohttp
from isodate import parse_duration

import config
import videoSources
from models import Video, database

BASEPARAMS = {'key': config.googleApiKey}
PLAYLISTPARAMS = {**BASEPARAMS, 'part': ['snippet', 'contentDetails'], 'maxResults': 50}
VIDEOSPARAMS = {**BASEPARAMS, 'part': ['contentDetails']}


async def getPlaylist(playlistID, nextPageToken="", session=aiohttp.ClientSession()):
    actions = 0

    async with session.get("https://www.googleapis.com/youtube/v3/playlistItems",
                           params={
                               **PLAYLISTPARAMS,
                               'playlistId': playlistID,
                               'pageToken': nextPageToken
                           }
                           ) as response:
        data = await response.json()

    await processItems(data['items'], session)
    actions += len(data['items'])
    if 'nextPageToken' in data:
        actions += await getPlaylist(playlistID, data['nextPageToken'], session)
    return actions


async def prettyData(items, session):


    async with session.get("https://www.googleapis.com/youtube/v3/videos",
                            params={**VIDEOSPARAMS, 'id': ','.join([i['contentDetails']['videoId'] for i in items])}
                          ) as response:
        data = await response.json()

    durations = {i['id']: i['contentDetails']['duration'] for i in data['items']}
    ret = []
    for i in items:
        snip = i['snippet']
        ret.append({
            'title': snip['title'],
            'vidId': i['contentDetails']['videoId'],
            'thumbnail': snip['thumbnails']['medium']['url'],
            'channel': snip['channelTitle'],
            'description': snip['description'],
            'publishDate': datetime.strptime(snip['publishedAt'], "%Y-%m-%dT%H:%M:%SZ"),
            'duration': parse_duration(durations[i['contentDetails']['videoId']]).seconds
        })
    return ret


async def processItems(items, session):
    items = await prettyData(items, session)
    with database.atomic():
        for i in items:
            v = Video.get_or_none(Video.vidId == i['vidId'])
            if v is None:
                action = "saving"
                v = Video(
                    vidId=i['vidId'],
                    title=i['title'],
                    description=i['description'],
                    channel=i['channel'],
                    thumbnail=i['thumbnail'],
                    publishDate=i['publishDate'],
                    duration=i['duration']
                )
            else:
                action = "updated"
                v.title = i['title']
                v.description = i['description']
                v.channel = i['channel']
                v.thumbnail = i['thumbnail']
                v.duration = i['duration']
            v.save()
            # print(f"{action} video id {i['vidId']}, {i['title']}")


ytLinkRegex = re.compile(r'((http(s)?://)?)(www.)?((youtube.com/)|(youtu.be/))([\S]+)')


def extractVideosFromDesc(description) -> list:
    matches = ytLinkRegex.findall(description)
    ids = [i[7] for i in matches]
    return ids


async def update() -> int:
    """updates database with newest videos from all playlists. also clears videos no longer part of the playlists"""
    total = 0
    with database.atomic():
        Video.delete().execute()  # delete all existing videos
        async with aiohttp.ClientSession() as session:
            for playlistId in videoSources.youtubePlaylists:
                total += await getPlaylist(playlistId, session=session)
    return total
