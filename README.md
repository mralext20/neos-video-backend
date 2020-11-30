# videos API

a simple project ot cache and proxy video results into neos from multiple playlists. 

# setup

populate your google API key in `config.py`, copied from `example_config.py`

setup your list of playlists in `videoSources.py`

once the server is started (using `python main.py`) be sure to preform a get request to /update to refresh 
all the cached videos.
