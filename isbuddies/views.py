from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import User, Product, Sale, SaleItem

bp = Blueprint("main", __name__)

# (endpoint, icon, label) per role -> drives the sidebar in base_app.html
NAV = {
    "admin": [("main.dashboard", "📊", "Dashboard"),
              ("main.inventory", "📦", "Inventory"),
              ("main.sales", "🛒", "Sales"),
              ("main.users", "👥", "Users"),
              ("main.suppliers_page", "🏭", "Suppliers"),
              ("main.knowledge", "🧠", "Knowledge Analysis")],
    "instructor": [("main.dashboard", "📊", "Dashboard"),
                   ("main.inventory", "📦", "Inventory (view)"),
                   ("main.sales", "🛒", "Sales (view)"),
                   ("main.knowledge", "🧠", "Knowledge Analysis")],
    "inventory_clerk": [("main.inventory", "📦", "Inventory"),
                        ("main.suppliers_page", "🏭", "Suppliers")],
    "sales_personnel": [("main.sales", "🛒", "Sales"),
                        ("main.sales_history", "📋", "Sales History")],
}


def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        @login_required
        def wrapper(*a, **kw):
            if current_user.role not in roles:
                abort(403)
            return fn(*a, **kw)
        return wrapper
    return deco


@bp.app_context_processor
def inject_nav():
    if current_user.is_authenticated:
        return {"nav_items": NAV.get(current_user.role, [])}
    return {}


@bp.route("/dashboard")
@roles_required("admin", "instructor")
def dashboard():
    return render_template("dashboard.html")


@bp.route("/inventory")
@roles_required("admin", "instructor", "inventory_clerk")
def inventory():
    categories = db.session.query(Product.category).distinct().filter(
        Product.category.isnot(None)
    ).order_by(Product.category).all()
    cats = [c[0] for c in categories]
    return render_template("inventory.html", categories=cats)


@bp.route("/sales")
@roles_required("admin", "instructor", "sales_personnel")
def sales():
    return render_template("sales.html")


@bp.route("/sales/history")
@roles_required("admin", "instructor", "sales_personnel")
def sales_history():
    return render_template("sales_history.html")


@bp.route("/knowledge")
@roles_required("admin", "instructor")
def knowledge():
    return render_template("knowledge.html")


@bp.route("/suppliers")
@roles_required("admin", "inventory_clerk")
def suppliers_page():
    return render_template("suppliers.html")


@bp.route("/users")
@roles_required("admin")
def users():
    return render_template("users.html", users=User.query.order_by(User.id).all())


@bp.route("/users/<int:user_id>/status", methods=["POST"])
@roles_required("admin")
def set_status(user_id):
    user = db.get_or_404(User, user_id)
    status = request.form["status"]
    if status in ("active", "locked") and user.id != current_user.id:
        user.status = status
        db.session.commit()
        flash(f"{user.username} is now {status}.")
    return redirect(url_for("main.users"))
