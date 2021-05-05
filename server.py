import flask
import os
import secrets
import sqlite3 as sql
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = flask.Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_connection():
    conn = None
    try:
        conn = sql.connect('repository.db')
        print("Connected to repository")
    except:
        print("Failed to connect to repository")
    return conn


def initialize_repository():
    conn = get_connection()
    conn.execute("DROP TABLE IF EXISTS images")
    conn.execute("CREATE TABLE images(id INT PRIMARY KEY NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL, labels TEXT NOT NULL)")
    conn.commit()
    print("Initialized repository")

def check_extension(filename):
    print(filename)
    index = len(filename) - filename[::-1].index('.')
    ext = filename[index:].lower()
    print(ext)
    return ext in ALLOWED_EXTENSIONS
    

@app.route("/")
def index_page():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM images")

    images = []
    for row in rows:
        images.append({
            'id': row[0],
            'name': row[1],
            'url': "static/" + row[2],
            'labels': row[3]
        })
    return flask.render_template('index.html', images = images)


@app.route('/upload')
def upload_page():
    return flask.render_template('upload.html')

@app.route('/upload', methods = ['POST'])
def upload_image():
    if 'image' not in flask.request.files:
        flask.flash("Form missing image type")
        return flask.redirect(flask.request.url)
    
    image = flask.request.files['image']
    if image.filename == '':
        flask.flash("No image selected")
        return flask.redirect(flask.request.url)
    
    if check_extension(image.filename):
        filename = secure_filename(image.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(path)
        flask.flash("Image successfully uploaded")
        return flask.render_template('upload.html', image = image)
    else:
        flask.flash("Unsupported extension. The supported extensions are png, jpg, and jpeg")
        return flask.redirect(flask.request.url)

if __name__ == '__main__':
    initialize_repository()
    app.run()
        





    







