import json
import os

from bs4 import BeautifulSoup
from flask import render_template, send_from_directory, request, make_response, session, redirect, url_for, jsonify, \
    current_app
from flask_socketio import emit
from lxml.html.clean import clean_html
from markdown import markdown
from markupsafe import Markup
from werkzeug.utils import secure_filename

from app import db, socketio
from . import main

from app.utils import *


@main.before_request
def enforce_https_in_heroku():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@main.route('/blog')
def blog():
    # Блог посты всех пользователей с сортировкой по id блога.
    blog_posts = db.execute(
        "SELECT * "
        "FROM blog_posts "
        "ORDER by blog_id DESC"
    ).fetchall()
    return render_template('blog.html', blog_posts=blog_posts)


@main.route("/blog/<int:blog_id>", methods=["GET", "POST"])
def get_blog(blog_id):
    # Блог-пост и его автор.
    blog_post = db.execute(
        "select * "
        "from blog_posts "
        "inner join users "
        "on users.user_id = blog_user_id "
        "where blog_id = :blog_id",
        {
            "blog_id": blog_id
        }
    ).fetchone()

    blog_text_html = markdown(blog_post['blog_text'])
    # Clean from all js injections.
    blog_text_html = clean_html(blog_text_html)
    soup = BeautifulSoup(blog_text_html, features="lxml")
    h1_left_align(soup)
    responsive_images(soup)
    # https://stackoverflow.com/questions/3206344/passing-html-to-template-using-flask-jinja2
    soup = Markup(soup)

    return render_template("blog_post.html", blog_post=blog_post, soup=soup)


@main.route("/blog/<int:blog_id>/load_comments", methods=["POST"])
def load_comments(blog_id):
    req = request.get_json()
    print(req)

    # Комментарии и их авторы текущего блог-поста с сортировкой по убыванию даты создания
    # главных комментариев и сортировкой по возрастанию его наследников.
    comments = db.execute(
        "select * "
        "from comments "
        "join users "
        "on users.user_id = comment_user_id "
        "where comment_blog_post_id = :blog_id "
        "order by thread_timestamp, comment_path",
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


@main.route("/load_sidebar_comments", methods=["POST"])
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
            "values (:ct, current_timestamp, :cui, :cpi, :cbpi) "
            "returning *",
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
                "select * "
                "from comments "
                "where comment_id = :parent_id",
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
            "where comment_id = :ci "
            "returning *",
            {
                "ci": inserted_comment['comment_id'],

                "cp": comment_path,
                "cl": comment_level,
                "tt": thread_timestamp
            }
        ).fetchone()
        db.commit()

        # Извлечение данных добавленного комментария для отображения на странице сайта в реальном времеми.
        inserted_comment = db.execute(
            "select * "
            "from comments "
            "join users "
            "on comment_user_id = users.user_id "
            "where comment_id = :ci",
            {
                "ci": inserted_comment['comment_id']
            }
        )
        db.remove()

        # use special handler for dates and decimals
        inserted_comment = json.loads(json.dumps([dict(row) for row in inserted_comment], default=alchemyencoder))
        inserted_comment = inserted_comment[0]
        inserted_comment["comment_level"] = comment_level
        inserted_comment["parent_path"] = parent_comment["comment_path"]

        emit("announce comment", inserted_comment, broadcast=True)


@main.route('/add_blog_post', methods=["GET", "POST"])
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


@main.route('/upload_file', methods=["POST"])
def upload_file():
    file_urls = []
    files = request.files.getlist('files')

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            file_urls.append(url_for('main.uploaded_file', filename=filename))

    return jsonify({'links': file_urls})
