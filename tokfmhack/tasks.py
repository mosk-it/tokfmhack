from os import path, environ
import requests
import json
import sys
import config
import threading
import datetime

from dateutil.parser import parse
from email import utils
import time


from uuid import uuid4
from PIL import Image, ImageFont, ImageDraw


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

        r = requests.post("https://audycje.tokfm.pl/gets?disableRedirect=true", data=body)
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
    row = cur.execute("""select title, author, image_url from
            podcasts where url=?""", (url,)).fetchone()

    if row is not None:
        return row

    session = HTMLSession()
    r = session.get(url)
    title = r.html.find('h1.tok-topwrap__h1', first=True).full_text
    image = r.html.find('.tok-topwrap__topwrap .tok-topwrap__img img', first=True)

    image_src = ''

    if 'src' in image.attrs:
        image_src = image.attrs['data-src']

    image_file = make_podcast_image(image_src, title)


    info_fields = r.html.find('.tok-topwrap__topwrap .tok-divTableRow')
    author = ''

    for i, field in enumerate(info_fields):
        label = field.find('.tok-topwrap__label', first=True).full_text
        if label.find('Prowadzący') > -1:
            author = field.find('a', first=True).full_text

    return { 'title': title, 'author': author, 'image_url': image_file }



def add_to_db(url):

    program_id = url.split('/')[-1]

    info = get_podcast_info(url)

    con = config.get_db()
    cur = con.cursor()
    cur.execute("select count(*) as count from podcasts where id=?", (program_id,))
    if cur.fetchone()['count'] == 0:
        cur.execute("""insert into podcasts(id, title, url, author, image_url)
                values (?, ?, ?, ?, ?)""",
                (program_id, info['title'], url, info['author'], info['image_url'],))
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

        date_span = span[0].full_text.strip()
        try:
            dt = datetime.datetime.strptime(date_span, '%d.%m.%Y %H:%M')
        except ValueError:
            now = datetime.datetime.now()
            hours, minutes = date_span.split(':')
            fmt = '{}.{}.{} {}:{}'.format(now.day, now.month, now.year, hours, minutes)
            dt = datetime.datetime.strptime(fmt, '%d.%m.%Y %H:%M')


        ep['published'] = utils.formatdate(time.mktime(dt.timetuple()))

        episodes.append(ep)

    return episodes


def make_podcast_image(img_url, text):

    r = requests.get(img_url, allow_redirects=True)
    extension = img_url.split('.')[-1]
    filename = "{}.{}".format(str(uuid4()), extension)
    filepath = '{}/data/{}'.format(environ['APP_DIR'], filename)

    open(filepath, 'wb').write(r.content)

    img = Image.open(filepath)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("./LiberationMono-Bold.ttf", 60)

    size = 68

    split_by = 7
    parts = [text[i: i + split_by].strip() for i in range(0, len(text), split_by)]


    shadowcolor=(60,60,60)
    textcolor=(230,230,230)

    thickness = 3

    for i, part in enumerate(parts):
        x = 0
        y = i*size*0.75
        draw.text((x-thickness, y), part, font=font, fill=shadowcolor)
        draw.text((x+thickness, y), part, font=font, fill=shadowcolor)
        draw.text((x, y-thickness), part, font=font, fill=shadowcolor)
        draw.text((x, y+thickness), part, font=font, fill=shadowcolor)
        #
        draw.text((x-thickness, y-thickness), part, font=font, fill=shadowcolor)
        draw.text((x+thickness, y-thickness), part, font=font, fill=shadowcolor)
        draw.text((x-thickness, y+thickness), part, font=font, fill=shadowcolor)
        draw.text((x+thickness, y+thickness), part, font=font, fill=shadowcolor)
        #
        draw.text((x, y), part, font=font, fill=textcolor)


    img.save(filepath)

    return filename

def get_full_image_url(img_id):
    return config.get_app_url() + '/image/' + img_id
