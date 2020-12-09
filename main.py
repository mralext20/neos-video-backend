from sanic import Sanic
from sanic.response import text, json

from datetime import datetime
import neosutils
import videoSources
import youtube
from config import baseurl
from models import Video

app = Sanic(name="Neos Video Backend")


@app.route(f"{baseurl}/all.txt")
async def all(request):
    """
    returns all videos from the database as a single string.
    """
    videos = Video.select().order_by(Video.publishDate.desc())
    return processVideos(videos, request)


@app.route(f"{baseurl}/search/<searchTerm:string>")
async def search(request, searchTerm):
    """
    search through the database for any videos that contain the search term, in either their title or description.
    """
    matches = Video.select().where((Video.title.contains(searchTerm)) | (Video.description.contains(searchTerm)))
    return processVideos(matches, request)


def processVideos(data, req):
    """
    simple connector method to take a result from peewee and return the text to send back on the webclient
    :param req: the original request. will be used to style the response appropriately
    :param data: series of videos.
    :return: response for sanic
    """
    style= {'v':1, 'format':'JSON'}
    params =  {k[0]:k[1] for k in req.query_args}
    if 'Neos' in req.headers['user-agent'] or params.get('format') == 'Neos':
        style['format'] = 'neos'
    if params.get('format') == 'JSON':
        style['format'] = 'JSON'
    if params.get('v') == '2':
        style['v'] = 2

    if style['v'] == 1 or style['v'] is None:
        videos = [[v.title, v.vidId, v.channel, v.description, v.thumbnail, v.publishDate.timestamp()] for v in data]
    else:
        # style['v'] == 2:
        videos = [[v.title, v.vidId, v.channel, v.description, v.thumbnail, v.publishDate.timestamp(), v.duration] for v in data]

    if style['format'] == 'neos':
        return text(neosutils.formatForNeos(videos))
    else:
        return json(videos)


@app.route(f"{baseurl}/related/<videoId:string>")
async def related(request, videoId):
    """
    given a videoId, return any video in the database that the video given mentioned in its description,
    and also any video in the database that mentions the given video
    """
    source = Video.get(Video.vidId == videoId)
    videos = youtube.extractVideosFromDesc(source.description)
    matches = Video.select().where((Video.vidId << videos) | (Video.description.contains(videoId)))
    matches = [match for match in matches if match.vidId != videoId]
    return processVideos(matches, request)


@app.route(f"{baseurl}/info/<videoId:string>")
async def info(request, videoId):
    """
    given a video, return its data
    """
    source = Video.get(Video.vidId == videoId)
    return processVideos([source], request)

@app.route(f"{baseurl}/update")
async def update(request):
    """
    request the database be updated with the latest information from the playlists in `videoSources.py`
    """
    then = datetime.now()
    total = 0
    Video.delete().execute()  # delete all existing videos
    for playlistId in videoSources.youtubePlaylists:
        total += youtube.getPlaylist(playlistId)
    return text(f"Success, took {datetime.now() - then} to retrieve {total} items")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
