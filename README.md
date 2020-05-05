# Stwórz rss z audycji radia Tokfm

Skrypt służy do stworzenia kanałów rss z audycji rss, w celu odsłuchiwania ich w ulubionym odtwarzaczu.
Mimo, że konto nie jest potrzebne do uruchomienia aplikacji, zakładam, że posiadasz dostęp premium.

## docker-compose

```
APP_URL="https://example.com" docker-composer build
docker-compose up -d
```

## virtualenv

wymagane pakiety:
```
ffmpeg g++ gcc libxslt libxslt-dev sqlite --no-cache jpeg zlib jpeg-dev zlib-dev build-base freetype freetype-dev
pip install -r /opt/Tokfmhack/requirements.txt
mkdir -p data
sqlite3 data/podcast.db < schema.sql
cd tokfmhack
python main.py
```




