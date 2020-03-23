import os
import requests
from soup_functions import *

from flask import *
from flask_bcrypt import Bcrypt
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from markdown import markdown

from flask import Markup
from werkzeug.utils import secure_filename

# https://coderbook.com/@marcus/how-to-render-markdown-syntax-as-html-using-python/
from bs4 import BeautifulSoup

UPLOAD_FOLDER = os.getcwd() + '/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
bcrypt = Bcrypt(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
# engine = create_engine(
#     "postgres://boqyxxkgziqwvp:1da49940138d6b0b7d730d9c31863551afdad524198814e997dc4438fae6ab82@ec2-34-200-116-132.compute-1.amazonaws.com:5432/dcd1iguaiog2m3")
db = scoped_session(sessionmaker(bind=engine))


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/blog')
def blog():
    blog_posts = db.execute("SELECT * FROM blogs ORDER by blog_id DESC ").fetchall()
    return render_template('blog.html', blog_posts=blog_posts)


@app.route("/blogs/<int:blog_id>")
def get_blog(blog_id):
    blog = db.execute("select * from blogs join users on users.user_id = blog_user_id where blog_id = :blog_id",
                      {"blog_id": blog_id}).fetchone()

    soup = BeautifulSoup(markdown(blog['blog_description']))
    h1_left_align(soup)
    responsive_images(soup)

    # https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2
    soup = Markup(soup)
    return render_template("blog.html", blog=blog, soup=soup)


@app.route('/registration', methods=["GET", "POST"])
def registration():
    session.clear()

    if request.method == "POST":
        if not request.form.get("firstname"):
            return "error"
        if not request.form.get("lastname"):
            return "error"
        if not request.form.get("username"):
            return "input username"
        if not request.form.get("password"):
            return "input password"
        if not request.form.get("password_confirm"):
            return "confirm password"
        if request.form.get("password") != request.form.get("password_confirm"):
            return "passwords are different"

        user = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        if user is None:
            db.execute("INSERT INTO users (firstname, lastname, username, password) VALUES (:f, :l, :u, :p)",
                       {"f": request.form.get("firstname"),
                        "l": request.form.get("lastname"),
                        "u": request.form.get("username"),
                        "p": bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')})
            db.commit()
        else:
            return "username is taken"

        return redirect("/login")
    else:
        return render_template("registration.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return "input username"
        if not request.form.get("password"):
            return "input password"

        user = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        if user is None:
            return "No such a user"

        if not bcrypt.check_password_hash(user.password, request.form.get("password")):
            return "wrong password"

        session["user_id"] = user.user_id
        session["username"] = user.username

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route('/add_blog_post', methods=["GET", "POST"])
def add_blog_post():
    if request.method == "POST":
        if session.get('user_id'):
            db.execute(
                "INSERT INTO blogs (blog_title, blog_description, blog_user_id, blog_date) "
                "VALUES (:bt, :bd, :bui, current_date)",
                {"bt": request.form.get("blog_title"),
                 # Markdown to HTML.
                 "bd": request.form.get("blog_post"),
                 "bui": session.get("user_id")})
            db.commit()

            return redirect("/")
        else:
            return "login first"
    else:
        return render_template("add_blog_post.html")


@app.route('/upload_file', methods=["POST"])
def upload_file():
    file_urls = []
    files = request.files.getlist('files')

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_urls.append(url_for('uploaded_file', filename=filename))

    return jsonify({'links': file_urls})


if __name__ == '__main__':
    app.run()
