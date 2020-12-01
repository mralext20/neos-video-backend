from sanic import Sanic
from sanic.response import text

from datetime import datetime
import neosutils
import videoSources
import youtube
from config import baseurl
from models import Video

app = Sanic("hello_example")


@app.route(f"{baseurl}/all.txt")
async def all(request):
    videos = Video.select().order_by(Video.publishDate.desc())
    return processVideos(videos)


@app.route(f"{baseurl}/search/<searchTerm:string>")
async def search(request, searchTerm):
    matches = Video.select().where((Video.title.contains(searchTerm)) | (Video.description.contains(searchTerm)))
    return processVideos(matches)


def processVideos(matches):
    videos = [[v.title, v.vidId, v.channel, v.description, v.thumbnail, v.publishDate.timestamp()] for v in matches]
    ret = neosutils.formatForNeos(videos)
    return text(ret)


@app.route(f"{baseurl}/related/<videoId:string>")
async def related(request, videoId):
    source = Video.get(Video.vidId == videoId)
    videos = youtube.extractVideosFromDesc(source.description)
    matches = Video.select().where((Video.vidId << videos) | (Video.description.contains(videoId)))
    matches = [match for match in matches if match.vidId != videoId]
    return processVideos(matches)


@app.route(f"{baseurl}/info/<videoId:string>")
async def info(request, videoId):
    source = Video.get(Video.vidId == videoId)
    return processVideos([source])

@app.route(f"{baseurl}/update")
async def update(request):
    then = datetime.now()
    total = 0
    for playlistId in videoSources.youtubePlaylists:
        total += youtube.getPlaylist(playlistId)
    return text(f"Success, took {datetime.now() - then} to retrieve {total} items")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
