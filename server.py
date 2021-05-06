import requests
import secrets
import sqlite3 as sql
from flask import Flask, render_template, flash, redirect, request


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
API_URL = "https://google-ai-vision.p.rapidapi.com/cloudVision/imageLabelsDetection"

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)


def get_connection():
    conn = None
    try:
        conn = sql.connect('collection.db')
    except:
        print("Failed to connect to image collection")
    return conn


def initialize_repository():
    conn = get_connection()
    conn.execute("DROP TABLE IF EXISTS images")
    conn.execute("CREATE TABLE images(name TEXT, url TEXT UNIQUE, labels TEXT)")
    conn.commit()


def check_extension(filename):
    print(filename)
    index = len(filename) - filename[::-1].index('.')
    ext = filename[index:].lower()
    return ext in ALLOWED_EXTENSIONS


def connect_to_api(image_url):
    url = API_URL

    with open('api_key.bin', encoding = 'utf-8') as binary_file:
        api_key = binary_file.read()
    headers = {
        'content-type': "application/json",
        'x-rapidapi-key': str(api_key),
        'x-rapidapi-host': "google-ai-vision.p.rapidapi.com"
    }

    payload = "{\"source\": \"" + image_url + "\", \"sourceType\": \"url\"}"
    response = requests.request("POST", url, data = payload, headers = headers)
    return response.json()


def get_image_labels(image_url):
    response = connect_to_api(image_url)
    labels = response["labels"]
    print(labels)
    return ', '.join(labels)


def get_images(query):
    conn = get_connection()
    rows = conn.execute(query)
    images = []
    for row in rows:
        images.append({
            'name': row[0],
            'url': row[1]
        })
    return images


@app.route('/', methods = ['GET', 'POST'])
def index_page():
    query = "SELECT name, url FROM images"

    if request.method == 'POST':
        search = request.form['search']
        if search:
            query = "SELECT name, url FROM images WHERE labels LIKE '%" + search + "%'"
            flash("Search result for " + search)
    
    images = get_images(query)
    return render_template('index.html', images = images)


@app.route('/upload', methods = ['GET', 'POST'])
def upload_page():
    if request.method == 'GET':
        return render_template('upload.html')

    name = request.form['name']
    image_url = request.form['image_url']

    if check_extension(image_url):
        labels = get_image_labels(image_url)
        conn = get_connection()
        conn.execute("INSERT OR IGNORE INTO images(name, url, labels) VALUES (?, ?, ?)", (name, image_url, labels))
        conn.commit()

        flash("Image successfully added to collection")
        return render_template('upload.html', image_url = image_url)

    else:
        flash("Unsupported extension. The supported extensions are png, jpg, and jpeg")
        return redirect(request.url)


if __name__ == '__main__':
    initialize_repository()
    app.run()
