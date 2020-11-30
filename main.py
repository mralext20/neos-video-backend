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
    videos = [[v.title, v.vidId, v.channel, v.description, v.thumbnail, v.publishDate.timestamp()] for v in videos]
    # videos.sort(key=lambda a: a[5], reverse=True)
    ret = neosutils.formatForNeos(videos)
    return text(ret)


@app.route(f"{baseurl}/search/<searchTerm:string>")
async def search(request, searchTerm):
    matches = Video.select().where((Video.title.contains(searchTerm)) | (Video.description.contains(searchTerm)))
    videos = [[v.title, v.vidId, v.channel, v.description, v.thumbnail, v.publishDate.timestamp()] for v in matches]
    # videos.sort(key=lambda a: a[5], reverse=True)
    ret = neosutils.formatForNeos(videos)
    return text(ret)


@app.route(f"{baseurl}/update")
async def update(request):
    then = datetime.now()
    for playlistId in videoSources.youtubePlaylists:
        youtube.getPlaylist(playlistId)
    return text(f"Success, took {datetime.now() - then}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
