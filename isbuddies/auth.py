import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from . import db
from .models import User

bp = Blueprint("auth", __name__)

SIGNUP_ROLES = {"inventory_clerk", "sales_personnel"}  # admin/instructor are created by an admin
HOME = {
    "admin": "main.dashboard",
    "instructor": "main.dashboard",
    "inventory_clerk": "main.inventory",
    "sales_personnel": "main.sales",
}


def home_for(user):
    return url_for(HOME[user.role])


@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(home_for(current_user))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"].strip()).first()
        if not user or not user.check_password(request.form.get("password", "")):
            flash("Invalid username or password.")
        elif user.status == "pending":
            flash("Your account is pending admin approval.")
        elif user.status == "locked":
            flash("Your account is locked. Contact an admin.")
        else:
            login_user(user)
            return redirect(request.args.get("next") or home_for(user))
    return render_template("login.html")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        f = request.form
        username, pw = f["username"].strip(), f.get("password", "")
        error = None
        if pw != f.get("confirm_password", ""):
            error = "Passwords do not match."
        elif len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
            error = "Password needs 8+ characters with a letter and a number."
        elif f["role"] not in SIGNUP_ROLES:
            error = "Please select a valid role."
        elif User.query.filter_by(username=username).first():
            error = "Username is already taken."
        if error:
            flash(error)
        else:
            u = User(full_name=f["full_name"].strip(), email=f["email"].strip(),
                     username=username, role=f["role"], status="pending")
            u.set_password(pw)
            db.session.add(u)
            db.session.commit()
            flash("Account created. Wait for admin approval, then log in.")
            return redirect(url_for("auth.login"))
    return render_template("signup.html")


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
