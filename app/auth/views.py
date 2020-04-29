from flask import request, session, redirect, render_template

from app import db
from . import auth
from .utils import hash_password, verify_password


@auth.route('/registration', methods=["GET", "POST"])
def registration():
    session.clear()

    if request.method == "POST":
        first_name = request.form.get("firstname")
        last_name = request.form.get("lastname")
        username = request.form.get("username")
        password = hash_password(request.form.get("password"))
        password_confirm = request.form.get("password_confirm")

        # TODO: error page.
        if not verify_password(password, password_confirm):
            return "passwords are different"

        # Сканирование таблицы пользователей при регистрации нового пользователя.
        user = db.execute(
            "SELECT * "
            "FROM users "
            "WHERE username = :username",
            {
                "username": username
            }
        ).fetchone()

        # TODO: error page.
        if user:
            return "username is taken"

        db.execute(
            "INSERT INTO users (first_name, last_name, username, password) "
            "VALUES (:f, :l, :u, :p)",
            {"f": first_name,
             "l": last_name,
             "u": username,
             "p": password
             }
        )
        db.commit()

        return redirect("/login")
    else:
        return render_template("auth/registration.html")


@auth.route('/login', methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.execute(
            "SELECT * "
            "FROM users "
            "WHERE username = :username",
            {
                "username": username
            }
        ).fetchone()

        if user and verify_password(user.password, password):
            session["user_id"] = user.user_id
            session["username"] = user.username
        else:
            return "wrong username or password"

        return redirect("/")
    else:
        return render_template("auth/login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
