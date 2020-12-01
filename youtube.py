from datetime import datetime

import requests

import config
from models import Video, database

baseParams = {'part': ['snippet'], 'maxResults': 50, 'key': config.googleApiKey}


def getPlaylist(playlistID, nextPageToken=""):
    actions = 0

    res = requests.get(
        "https://www.googleapis.com/youtube/v3/playlistItems",
        params={**baseParams, 'playlistId': playlistID, "pageToken": nextPageToken},
    )
    res.raise_for_status()

    data = res.json()
    processItems(data['items'])
    actions += len(data['items'])
    if 'nextPageToken' in data:
        actions += getPlaylist(playlistID, data['nextPageToken'])
    print(res)
    return actions


def processItems(items):
    with database.atomic():
        for i in items:
            snip = i['snippet']
            vid = snip['resourceId']['videoId']
            v = Video.get_or_none(Video.vidId == vid)
            if v is None:
                action = "saving"
                v = Video(
                    vidId=vid,
                    title=snip['title'],
                    description=snip['description'],
                    channel=snip['channelTitle'],
                    thumbnail=snip['thumbnails']['default']['url'],
                    publishDate=datetime.strptime(snip['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                )
            else:
                action = "updated"
                v.title = snip['title']
                v.description = snip['description']
                v.channel = snip['channelTitle']
                v.thumbnail = snip['thumbnails']['default']['url']
            v.save()
            print(f"{action} video id {vid}")
