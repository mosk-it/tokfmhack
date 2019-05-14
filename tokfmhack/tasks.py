from os import path, environ
import requests
import json
import sys
import config
import threading

from dateutil.parser import parse
from email import utils

from requests_html import HTMLSession


def format_filename(url: str, no_extension=False) -> str:
    filename = url.split('/')[-1].strip('-').lower()
    if no_extension:
        return filename
    return filename + '.mp3'


def background_download_podcast(podcast_id):
    podcast_url = "https://audycje.tokfm.pl/audycja/{}".format(podcast_id)
    t = threading.Thread(target=download_podcast, args=(podcast_url,))
    t.start()



def download_podcast(podcast_id):
    podcast_url = "https://audycje.tokfm.pl/audycja/{}".format(podcast_id)
    url = podcast_url
    file_path = '{}/data/{}'.format(environ['APP_DIR'], format_filename(podcast_url))

    if not path.exists(file_path):

        data = url[url.rfind('/')+1:]
        pid, title = data.split(',')
        body = json.dumps({"pid": pid, "st": "tokfm"})

        r = requests.post("https://audycje.tokfm.pl/gets", data=body)
        data = json.loads(r.text)

        r = requests.get(data["url"], allow_redirects=True)
        filename = format_filename(title)
        open(file_path, 'wb').write(r.content)

    return file_path

# def get_program(url):

#     session = HTMLSession()
#     r = session.get(url)

#     podcasts = r.html.find('.tok-podcasts__row--name a')
#     for podcast in podcasts:
#         download_thread = threading.Thread(target=download_podcast, args=(podcast.attrs['href']))


def get_podcasts():
    con = config.get_db()
    cur = con.cursor()
    cur.execute("select id, title, url from podcasts")
    return cur.fetchall()


def get_podcast_info(url):

    con = config.get_db()
    cur = con.cursor()
    rowcount = cur.execute("""select title, author from podcasts where url=?""",
            (url,)).rowcount

    if rowcount > 0:
        return cur.fetchone()

    session = HTMLSession()
    r = session.get(url)
    title = r.html.find('h1.tok-topwrap__h1', first=True).full_text
    image = r.html.find('.tok-topwrap__topwrap .tok-topwrap__img img', first=True)

    if 'src' in image.attrs:
        image_src = image.attrs['src']




    info_fields = r.html.find('.tok-topwrap__topwrap .tok-divTableRow')
    author = ''

    for i, field in enumerate(info_fields):
        label = field.find('.tok-topwrap__label', first=True).full_text
        if label.find('Prowadzący') > -1:
            author = field.find('a', first=True).full_text

    return { 'title': title, 'author': author, 'image': image_src }



def add_to_db(url):

    program_id = url.split('/')[-1]

    info = get_podcast_info(url)

    con = config.get_db()
    cur = con.cursor()
    cur.execute("select count(*) as count from podcasts where id=?", (program_id,))
    if cur.fetchone()['count'] == 0:
        cur.execute("""insert into podcasts(id, title, url, author, image_url)
                values (?, ?, ?, ?, ?)""",
                (program_id, info['title'], url, info['author'], info['author'],))
        con.commit()

    cur.close()
    con.close()


def queue_downloading(url):
    
    episodes = get_podcast_episodes(url, fast=True)
    
    items = []
    for item in episodes:

        ep_id = item['link'].split('/')[-1]
        t = threading.Thread(target=download_podcast, args=(ep_id,))
        t.start()




def get_podcast_episodes(url, fast=False):
    session = HTMLSession()
    r = session.get(url)

    #'tok-podcasts__row--time'

    blocks = r.html.find('.tok-podcasts', first=True).find('.tok-podcasts__podcast')
    episodes = []

    for block in blocks:
        ep = {}

        info = block.find('.tok-podcasts__item--name', first=True)

        ep['link'] = info.find('.tok-podcasts__row--name a', first=True).attrs['href']

        if fast:
            episodes.append(ep)
            continue


        download_url = '{}/download/{}'.format(config.get_app_url(),
                format_filename(ep['link'], no_extension=True))

        ep['audio_url'] = download_url
        ep['title'] = info.find('.tok-podcasts__row--name a',
                first=True).full_text.strip()

        span = info.find('.tok-podcasts__row--time span a')

        ep['author'] = ''

        if len(span) > 0:
            ep['author'] = span[-1].full_text.strip()

        span = info.find('.tok-podcasts__row--audition-time span')

        d = parse(span[0].full_text.strip())
        
        ep['published'] = utils.formatdate(d.timestamp())

        episodes.append(ep)

    return episodes
