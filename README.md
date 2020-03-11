# Package creates rss feed from any tokfm audition

## *This package only allows creating rss feeds, I still recommend subscribe tokfm*

## Using docker-compose

```
APP_URL="https://example.com" docker-composer build
docker-compose up -d
```
## virtualenv
Needed packages:
```
ffmpeg g++ gcc libxslt libxslt-dev sqlite --no-cache jpeg zlib jpeg-dev zlib-dev build-base freetype freetype-dev
pip install -r /opt/Tokfmhack/requirements.txt
mkdir -p data
sqlite3 data/podcast.db < schema.sql
cd tokfmhack
python main.py
```




