import atexit
import io
import os
import secrets
import sqlite3 as sql
from configparser import ConfigParser
from flask import Flask, render_template, flash, redirect, request
from google.cloud import vision
from werkzeug.utils import secure_filename

# read config file
config = ConfigParser()
config.read('utils/config.ini')

with open('utils/api_key.bin', encoding = 'utf-8') as binary_file:
    api_key = binary_file.read()
with open('utils/api_key.json', 'w') as json_file:
    json_file.write(api_key)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'utils/api_key.json'


# set image extensions
# set Google AI Vision API address
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
UPLOAD_FOLDER = 'static/images/'

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def exit_handler():
    os.remove('utils/api_key.json')

# connect to database
def get_connection():
    conn = None
    try:
        conn = sql.connect('database/collection.db')
    except:
        print("Failed to connect to image collection")
        exit()
    return conn


# initialize database
# delete exisiting database
# comment out this method if exisiting database is to be used
def initialize_repository():
    conn = get_connection()
    conn.execute("DROP TABLE IF EXISTS images")
    conn.execute("CREATE TABLE images(name TEXT, url TEXT UNIQUE, labels TEXT)")
    conn.commit()


# check image extensions
def check_extension(filename):
    index = len(filename) - filename[::-1].index('.')
    ext = filename[index:].lower()
    return ext in ALLOWED_EXTENSIONS


# check whether image url provided is a web url
def is_web_url(url):
    return "http" in url


# connect to Google Vision API
# return according labels for image
def connect_to_api(image_url):
    client = vision.ImageAnnotatorClient()
    if is_web_url(image_url):
        image = vision.Image()
        image.source.image_uri = image_url
    else:
        with io.open(image_url, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content = content)

    response = client.label_detection(image = image)
    if response.error.message:
        print("Failed to connect to Google AI Vision API: {}".format(response.error.message))
    else:
        labels = response.label_annotations
        return labels


# call method to connect to Google Vision API
# format and return image labels as string
def get_image_labels(image_url):
    labels = connect_to_api(image_url)
    if not labels:
        return None
    else:
        label_descriptions = [label.description for label in labels]
        return ', '.join(label_descriptions)


# get all images (name and photo) from database
# store images in table of size 3xn for easier html format
def get_images(query):
    conn = get_connection()
    rows = conn.execute(query)
    images = []
    for row in rows:
        images.append({'id': row[0], 'name': row[1], 'url': row[2]})

    table = []
    length = len(images)
    for i in range(0, length, 3):
        row = images[i: i + 3]
        table.append(row)
    return table


# get all information of an image from database
def get_image_info(query):
    conn = get_connection()
    rows = conn.execute(query)
    image = []
    for row in rows:
        image.append({'id': row[0], 'name': row[1], 'url': row[2], 'labels': row[3]})
    return image[0]
    

# index page to show the entire image collection
# contain search bar that can filter images according to 
# their characteristics (labels)
# e.g. a photo of fried chicken might have labels such as
# 'chicken', 'food', 'fast food', 'frying', etc.
@app.route('/', methods = ['GET', 'POST'])
def index_page():
    query = "SELECT rowid, name, url FROM images"
    if request.method == 'POST':
        search = request.form['search']
        if search:
            query = "SELECT rowid, name, url FROM images WHERE labels LIKE '%{}%'".format(search)
            flash("Search result(s) for {}".format(search))
    images = get_images(query)
    return render_template('index.html', images = images)


# page to add new web image
# throw errors if 
# 1. no name or web image url is provided
# 2. wrong image extensions (not png, jpg, or jpeg)
# 3. not a web url
# 4. cannot connect properly to Google AI Vision API
@app.route('/upload', methods = ['GET', 'POST'])
def upload_page():
    if request.method == 'GET':
        return render_template('upload.html')

    name = request.form['image_name']
    image_url = request.form['image_url']
    image_upload = request.files['image_upload']
    
    if not name:
        flash("Please provide a name for the image")
        return redirect(request.url)

    if (not image_url and not image_upload) or (image_url and image_upload):
        flash("Please provide either a web image url or upload a local image")
        return redirect(request.url)

    if image_upload:
        if image_upload.filename == '':
            flash("No image selected")
            return redirect(request.url)

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image_upload.filename))
    else:
        image_path = image_url
    
    if check_extension(image_path):
        if image_upload: image_upload.save(image_path)
        
        labels = get_image_labels(image_path)
        if not labels:
            flash("Something went wrong. Please retry with another image URL")
            return redirect(request.url)

        conn = get_connection()
        conn.execute("INSERT OR IGNORE INTO images(name, url, labels) VALUES (?, ?, ?)", (name, image_path, labels))
        conn.commit()

        flash("Image successfully added to collection")
        return render_template('upload.html', image_path = image_path)
    else:
        flash("Unsupported extension. The supported extensions are png, jpg, and jpeg")
        return redirect(request.url)


# page to delete a web image
@app.route('/delete', methods = ['GET', 'POST'])
def delete_page():
    query = "SELECT rowid, name, url FROM images"
    images = get_images(query)

    if request.method == 'GET':
        return render_template('delete.html', images = images)

    for id in request.form:
        image_id = id

    if not image_id:
        return redirect(request.url)

    conn = get_connection()
    conn.execute("DELETE FROM images WHERE rowid = (?)", (image_id))
    conn.commit()

    flash("Image successfully deleted from collection")
    return redirect(request.url)


# page to display all information of an image
# including name, labels, and the image itself
@app.route('/image<id>')
def image_page(id):
    query = "SELECT rowid, name, url, labels FROM images WHERE rowid = '{}'".format(id)
    image = get_image_info(query)
    return render_template('image.html', image = image)


if __name__ == '__main__':
    initialize_repository()
    app.run()
    atexit.register(exit_handler)
