from flask import request, session, redirect, render_template

from app import db, bcrypt
from . import auth


@auth.route('/registration', methods=["GET", "POST"])
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
        user = db.execute(
            "SELECT * "
            "FROM users "
            "WHERE username = :username",
            {
                "username": request.form.get("username")
            }
        ).fetchone()

        if user is None:
            db.execute("INSERT INTO users (first_name, last_name, username, password) "
                       "VALUES (:f, :l, :u, :p)",
                       {"f": request.form.get("firstname"),
                        "l": request.form.get("lastname"),
                        "u": request.form.get("username"),
                        "p": bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')})
            db.commit()
        else:
            return "username is taken"

        return redirect("/login")
    else:
        return render_template("auth/registration.html")


@auth.route('/login', methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return "input username"
        if not request.form.get("password"):
            return "input password"

        user = db.execute("SELECT * "
                          "FROM users "
                          "WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        if user is None:
            return "No such a auth"

        if not bcrypt.check_password_hash(user.password, request.form.get("password")):
            return "wrong password"

        session["user_id"] = user.user_id
        session["username"] = user.username

        return redirect("/")
    else:
        return render_template("auth/login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
