import re
from datetime import datetime

import requests
from isodate import parse_duration

import config
from models import Video, database

BASEPARAMS = {'key': config.googleApiKey}
PLAYLISTPARAMS = {**BASEPARAMS, 'part': ['snippet', 'contentDetails'], 'maxResults': 50}
VIDEOSPARAMS = {**BASEPARAMS, 'part': ['contentDetails']}


def getPlaylist(playlistID, nextPageToken=""):
    actions = 0

    res = requests.get(
        "https://www.googleapis.com/youtube/v3/playlistItems",
        params={**PLAYLISTPARAMS, 'playlistId': playlistID, "pageToken": nextPageToken},
    )
    res.raise_for_status()

    data = res.json()
    processItems(data['items'])
    actions += len(data['items'])
    if 'nextPageToken' in data:
        actions += getPlaylist(playlistID, data['nextPageToken'])
    print(res)
    return actions


def prettyData(items):
    res = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={**VIDEOSPARAMS, 'id': ','.join([i['contentDetails']['videoId'] for i in items])}
    )
    res.raise_for_status()
    data = res.json()
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


def processItems(items):
    items = prettyData(items)
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
            print(f"{action} video id {i['vidId']}, {i['title']}")


ytLinkRegex = re.compile(r'((http(s)?://)?)(www.)?((youtube.com/)|(youtu.be/))([\S]+)')


def extractVideosFromDesc(description) -> list:
    matches = ytLinkRegex.findall(description)
    ids = [i[7] for i in matches]
    return ids
