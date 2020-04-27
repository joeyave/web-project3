import datetime
import decimal
import os

# https://coderbook.com/@marcus/how-to-render-markdown-syntax-as-html-using-python/

from bs4 import BeautifulSoup
from flask import *
from flask import Markup
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_socketio import SocketIO, emit
from lxml.html.clean import clean_html
from markdown import markdown
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.utils import secure_filename

from soup_functions import *

app = Flask(__name__)
app.secret_key = "secret key"

UPLOAD_FOLDER = os.getcwd() + '/static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

bcrypt = Bcrypt(app)
socketio = SocketIO(app, ping_interval=20)
Session(app)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.strftime('%I:%M%p %d-%m-%Y')
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/blog')
def blog():
    # Блог посты всех пользователей с сортировкой по id блога.
    blog_posts = db.execute("SELECT * FROM blog_posts ORDER by blog_id DESC").fetchall()
    return render_template('blog.html', blog_posts=blog_posts)


@app.route("/blog/<int:blog_id>", methods=["GET", "POST"])
def get_blog(blog_id):
    # Блог-пост и его автор.
    blog_post = db.execute(
        "select * "
        "from blog_posts "
        "inner join users "
        "on users.user_id = blog_user_id "
        "where blog_id = :blog_id",
        {"blog_id": blog_id}).fetchone()

    blog_text_html = markdown(blog_post['blog_text'])
    # Clean from all js injections.
    blog_text_html = clean_html(blog_text_html)
    soup = BeautifulSoup(blog_text_html, features="lxml")
    h1_left_align(soup)
    responsive_images(soup)
    # https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2
    soup = Markup(soup)

    return render_template("blog_post.html", blog_post=blog_post, soup=soup)


@app.route("/blog/<int:blog_id>/load_comments", methods=["POST"])
def load_comments(blog_id):
    req = request.get_json()
    print(req)

    # Комментарии и их авторы текущего блог-поста с сортировкой по убыванию даты создания
    # главных комментариев и сортировкой по возрастанию его наследников.
    comments = db.execute(
        "select * from comments join users on users.user_id = comment_user_id "
        "where comment_blog_post_id = :blog_id order by thread_timestamp, comment_path",
        {
            "blog_id": blog_id
        }
    )
    db.remove()

    comments = json.loads(json.dumps([dict(row) for row in comments], default=alchemyencoder))
    for comment in comments:
        comment['parent_path'] = "_".join(comment['comment_path'].split('_')[:-1])
    comments = json.dumps(comments)

    return make_response(comments, 200)


@app.route("/load_sidebar_comments", methods=["POST"])
def load_sidebar_comments():
    sidebar_comments = db.execute(
        "select * "
        "from comments "
        "join users "
        "on comment_user_id = users.user_id "
        "where comment_level = 0 "
        "order by comment_date "
        "limit 10 "
    )
    db.remove()

    sidebar_comments = json.dumps([dict(row) for row in sidebar_comments], default=alchemyencoder)
    return make_response(sidebar_comments, 200)


@socketio.on("submit comment")
def comment(data):
    _N = 6

    if session.get("user_id"):
        try:
            parent_id = int(data['parent_path'].split('_')[-1])
        except ValueError:
            parent_id = ""

        #
        inserted_comment = db.execute(
            # Формирование нового комментария:
            # 1. Добавляю новый комментарий с полями, известными на текущий момент.
            "insert into comments "
            "(comment_text, comment_date, comment_user_id, comment_parent_id, comment_blog_post_id) "
            "values (:ct, current_timestamp, :cui, :cpi, :cbpi) returning *",
            {
                "ct": data['comment_text'],
                "cui": session.get("user_id"),
                "cpi": parent_id,
                "cbpi": data['blog_id']
            }
        ).fetchone()

        prefix = data['parent_path'] + '_' if parent_id else ''
        comment_path = prefix + '{:0{}d}'.format(inserted_comment['comment_id'], _N)
        comment_level = len(comment_path) // _N - 1

        if comment_level > 0:
            parent_comment = db.execute(
                "select * from comments where comment_id = :parent_id",
                {
                    "parent_id": parent_id
                }
            ).fetchone()
            thread_timestamp = parent_comment['comment_date']
        else:
            thread_timestamp = inserted_comment['comment_date']
            parent_comment = inserted_comment

        # Формирование нового комментария:
        # 2. Модификация путем добавления недостающих данных.
        inserted_comment = db.execute(
            "update comments "
            "set comment_path = :cp, comment_level = :cl, thread_timestamp = :tt "
            "where comment_id = :ci returning *",
            {
                "ci": inserted_comment['comment_id'],

                "cp": comment_path,
                "cl": comment_level,
                "tt": thread_timestamp
            }
        ).fetchone()
        db.commit()

        # Извлечение данных добавленного комментария для отображения на странице сайта в реальном времеми.
        inserted_comment = db.execute("select * "
                                      "from comments "
                                      "join users on comment_user_id = users.user_id "
                                      "where comment_id = :ci",
                                      {
                                          "ci": inserted_comment['comment_id']
                                      })
        db.remove()

        # use special handler for dates and decimals
        inserted_comment = json.loads(json.dumps([dict(row) for row in inserted_comment], default=alchemyencoder))
        inserted_comment = inserted_comment[0]
        inserted_comment["comment_level"] = comment_level
        inserted_comment["parent_path"] = parent_comment["comment_path"]

        emit("announce comment", inserted_comment, broadcast=True)


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

        # Сканирование таблицы пользователей при регистрации нового пользователя.
        user = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        if user is None:
            db.execute("INSERT INTO users (first_name, last_name, username, password) VALUES (:f, :l, :u, :p)",
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
                "INSERT INTO blog_posts (blog_title, blog_text, blog_user_id, blog_date) "
                "VALUES (:bt, :btext, :bui, current_date)",
                {"bt": request.form.get("blog_title"),
                 # Markdown to HTML.
                 "btext": request.form.get("blog_post"),
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
    socketio.run(app)
