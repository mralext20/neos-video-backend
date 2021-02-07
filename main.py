from datetime import datetime
from typing import List

from sanic import Sanic
from sanic.request import Request
from sanic.response import json, text

import database as db
import utils
import youtube
from config import baseurl

app = Sanic(name="Neos Video Backend")


@app.route(f"{baseurl}/all.txt")
async def all(request):
    """
    returns all videos from the database as a single string.
    """
    videos = await db.getAllVideos()
    return processVideos(videos, request)


@app.route(f"{baseurl}/search/<searchTerm:string>")
async def search(request, searchTerm: str):
    """
    search through the database for any videos that contain the search term, in either their title or description.
    """
    matches = await db.search(searchTerm)
    return processVideos(matches, request)


def processVideos(videos: List[db.Video], req: Request):
    """
    simple connector method to take a result from peewee and return the text to send back on the webclient
    :param req: the original request. will be used to style the response appropriately
    :param data: series of videos.
    :return: response for sanic
    """
    style = {'format': 'JSON'}
    DEFAULTPARAMS = {'page': '1', 'pageLength': '1000'}
    params = {**DEFAULTPARAMS, **{k[0]: k[1] for k in req.query_args}}
    if 'Neos' in req.headers['user-agent'] or params.get('format') == 'Neos':
        style['format'] = 'neos'
    if params.get('format') == 'JSON':
        style['format'] = 'JSON'

    start = (int(params['page']) - 1) * int(params['pageLength'])
    end = start + int(params['pageLength'])
    videos = [v.as_tuple for v in videos][start:end]

    if style['format'] == 'neos':
        return text(utils.formatForNeos(videos))
    else:
        return json(videos)


@app.route(f"{baseurl}/related/<videoId:string>")
async def related(request: Request, videoId: str):
    """
    given a videoId, return any video in the database that the video given mentioned in its description,
    and also any video in the database that mentions the given video
    """
    return processVideos(await (await db.getVideoById(videoId)).get_related_videos(), request)


@app.route(f"{baseurl}/info/<videoId:string>")
async def info(request, videoId: str):
    """
    given a video, return its data
    """
    source = await db.getVideoById(videoId)
    return processVideos([source], request)


@app.route(f"{baseurl}/update")
async def update(request):
    """
    request the database be updated with the latest information from the playlists in `videoSources.py`
    """
    then = datetime.now()
    total = await youtube.update()
    return text(f"Success, took {datetime.now() - then} to retrieve {total} items")


@app.listener("after_server_start")
async def startup(app, loop):
    await db.start()
    await utils.periodic(24 * 60 * 60)(youtube.update)()  # update data every day


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
