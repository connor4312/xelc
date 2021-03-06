from flask import Flask, request, render_template, redirect, abort, url_for

app = Flask(__name__);
app.config.from_object('config')

import redis, math, random
from urlparse import urlparse
r = redis.StrictRedis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DB'])

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
def index(path):
	count = r.hlen('links')
	if request.method == 'GET':
		return render_template('index.html', count=count, url_base=url_for('index', _external=True))
	else:
		parts = urlparse(request.form['url'])
		if not parts.scheme in ('http', 'https'):
			return 'Invalid URL! Be sure to prepend with http:// or https://', 400

		chars = []

		def shorten(input):
			pointer = math.floor(input / 25)
			if pointer > 25:
				pointer = shorten(pointer)
				chars.append(pointer)
			else:
				remainder = input % 25
				chars.append(pointer)
				chars.append(remainder)

			return pointer

		shorten(count)

		str = ''
		for char in chars:
			str += chr(97 + int(char))

		r.hset('links', str, request.form['url'])
		return str, 200

@app.route('/<link>')
def get_link(link):

	if app.config['ENABLE_EVIL'] and random.randint(0, 100) <= app.config['EVIL_LEVEL']:
		evil_sites = [
			# Put your evil sites here...
		]
		return redirect(random.choice(evil_sites))


	url = r.hget('links', link)

	if url:
		return redirect(url)
	else:
		return abort(404)

from gevent.wsgi import WSGIServer
http_server = WSGIServer(('', app.config['APP_PORT']), app)
http_server.serve_forever()
