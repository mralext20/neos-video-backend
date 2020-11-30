from datetime import datetime

import requests

import config
from models import Video, database

baseParams = {'part': ['snippet'], 'maxResults': 50, 'key': config.googleApiKey}


def getPlaylist(playlistID, nextPageToken=""):
    items = []

    res = requests.get(
        "https://www.googleapis.com/youtube/v3/playlistItems",
        params={**baseParams, 'playlistId': playlistID, "pageToken": nextPageToken},
    )
    res.raise_for_status()

    data = res.json()
    processItems(data['items'])
    if 'nextPageToken' in data:
        getPlaylist(playlistID, data['nextPageToken'])
    print(res)


def processItems(items):
    with database.atomic():
        for i in items:
            vid = i['snippet']['resourceId']['videoId']
            v = Video().select().where(Video.vidId == vid)
            if v.exists():
                print(f"already saved {vid}")
            else:
                v = Video(
                    vidId=vid,
                    title=i['snippet']['title'],
                    description=i['snippet']['description'],
                    channel=i['snippet']['channelTitle'],
                    thumbnail=i['snippet']['thumbnails']['default']['url'],
                    publishDate=datetime.strptime(i['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                )
                v.save()
                print(f"saving video id {vid}")
