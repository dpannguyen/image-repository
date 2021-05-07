import requests
import secrets
import sqlite3 as sql
from flask import Flask, render_template, flash, redirect, request


# set image extensions
# set Google AI Vision API address
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
API_URL = "https://google-ai-vision.p.rapidapi.com/cloudVision/imageLabelsDetection"

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)


# connect to database
def get_connection():
    conn = None
    try:
        conn = sql.connect('collection.db')
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
    print(filename)
    index = len(filename) - filename[::-1].index('.')
    ext = filename[index:].lower()
    return ext in ALLOWED_EXTENSIONS


# check image url provided is not from local path
def check_web_url(url):
    return "http" in url


# connect to Google AI Vision API
# return according labels for image
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

    response_json = None
    try:
        response_json = response.json()
    except:
        print("Failed to connect to Google AI Vision API")
    return response_json


# call method to connect to Google API
# format and return image labels as string
def get_image_labels(image_url):
    response = connect_to_api(image_url)
    if not response:
        return None

    labels = None
    try:
        labels = response["labels"]
    except:
        print("Bad request to Google AI Vision API")
        return None
    else: 
        print(labels)
        return ', '.join(labels)


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
    

# index page which shows the entire image collection
# page contains search bar that can filter images according to 
# their characteristics (labels)
# e.g. a photo of fried chicken might have labels such as
# 'chicken', 'food', 'fast food', 'frying', etc.
@app.route('/', methods = ['GET', 'POST'])
def index_page():
    query = "SELECT rowid, name, url FROM images"
    if request.method == 'POST':
        search = request.form['search']
        if search:
            query = "SELECT rowid, name, url FROM images WHERE labels LIKE '%" + search + "%'"
            flash("Search result(s) for " + search)
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

    name = request.form['name']
    image_url = request.form['image_url']
    
    if not name or not image_url:
        flash("Please provide a name and a web URL for the image")
        return redirect(request.url)

    if not check_web_url(image_url):
        flash("Cannot accept local images. Please retry with web image URL")
        return redirect(request.url)

    if check_extension(image_url):
        labels = get_image_labels(image_url)
        if not labels:
            flash("Something went wrong. Please retry with another web image URL")
            return redirect(request.url)

        conn = get_connection()
        conn.execute("INSERT OR IGNORE INTO images(name, url, labels) VALUES (?, ?, ?)", (name, image_url, labels))
        conn.commit()

        flash("Image successfully added to collection")
        return render_template('upload.html', image_url = image_url)
    else:
        flash("Unsupported extension. The supported extensions are png, jpg, and jpeg")
        return redirect(request.url)


# page to display all information of an image
# including name, labels, and the image itself
@app.route('/image<id>')
def image_page(id):
    query = "SELECT rowid, name, url, labels FROM images WHERE rowid = '" + id + "'"
    image = get_image_info(query)
    return render_template('image.html', image = image)


if __name__ == '__main__':
    # initialize_repository()
    app.run()
