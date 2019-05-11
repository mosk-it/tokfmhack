from flask import request, render_template, Flask, redirect, url_for, send_file
from re import match
import sys
import threading

import tasks


app = Flask(__name__)

@app.route('/')
def index():

    podcasts = tasks.get_podcasts()

    return render_template('index.html', podcasts=podcasts)


@app.route('/podcast', methods=['POST'])
def podcast():
    url = request.form['url']
    
    if url:
        tasks.add_to_db(url)
        tasks.queue_downloading(url)

    return redirect(url_for('index'))


@app.route('/feed/<podcast_id>', methods=['GET'])
def feed(podcast_id):
    url = 'https://audycje.tokfm.pl/audycja/{}'.format(podcast_id)
    info = tasks.get_podcast_info(url)


    channel = {
            'title': info['title'],
            'link': url,
            'author': info['author'],
            }
    
    episodes = tasks.get_podcast_episodes(url)
    
    items = []
    for item in episodes:

        ep_id = item['link'].split('/')[-1]
        t = threading.Thread(target=tasks.download_podcast, args=(ep_id,))
        t.start()
        # tasks.download_podcast(ep_id)

        items.append({
            'title': item['title'],
            'audio_url': item['audio_url'],
            'author': item['author'],
            'link': item['link'],
            'pub_date': item['published']
            })

    channel['items'] = items
    return render_template('rss.xml', channel=channel)


@app.route('/download/<podcast>', methods=['GET'])
def download(podcast):


    file_path = tasks.download_podcast(podcast)

    return send_file(open(file_path, 'rb'), mimetype='application/octet-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
