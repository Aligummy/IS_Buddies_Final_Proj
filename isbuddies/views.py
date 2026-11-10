from functools import wraps
import json

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import AuditLog, User, Product

bp = Blueprint("main", __name__)

# (endpoint, icon, label) per role -> drives the sidebar in base_app.html
NAV = {
    "admin": [("main.dashboard", "dashboard", "Dashboard"),
              ("main.inventory", "inventory", "Inventory"),
              ("main.sales", "sales", "Transactions"),
              ("main.sales_history", "history", "Sales History"),
              ("main.users", "users", "Users"),
              ("main.suppliers_page", "suppliers", "Suppliers"),
              ("main.customers_page", "customers", "Customers"),
              ("main.reports_page", "reports", "Reports"),
              ("main.knowledge", "knowledge", "Knowledge Analysis")],
    "instructor": [("main.dashboard", "dashboard", "Dashboard"),
                   ("main.inventory", "inventory", "Inventory (view)"),
                   ("main.sales", "sales", "Transactions (view)"),
                   ("main.sales_history", "history", "Sales History"),
                   ("main.customers_page", "customers", "Customers"),
                   ("main.reports_page", "reports", "Reports"),
                   ("main.knowledge", "knowledge", "Knowledge Analysis")],
    "inventory_clerk": [("main.inventory", "inventory", "Inventory"),
                        ("main.suppliers_page", "suppliers", "Suppliers")],
    "sales_personnel": [("main.sales", "sales", "Sales"),
                        ("main.sales_history", "history", "Sales History"),
                        ("main.customers_page", "customers", "Customers")],
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
    return render_template(
        "sales_history.html",
        can_return=current_user.role in ("admin", "sales_personnel"),
        can_report=current_user.role in ("admin", "instructor"),
    )


@bp.route("/knowledge")
@roles_required("admin", "instructor")
def knowledge():
    return render_template("knowledge.html")


@bp.route("/suppliers")
@roles_required("admin", "inventory_clerk")
def suppliers_page():
    return render_template("suppliers.html")


@bp.route("/customers")
@roles_required("admin", "instructor", "sales_personnel")
def customers_page():
    return render_template(
        "customers.html",
        can_manage=current_user.role in ("admin", "sales_personnel"),
    )


@bp.route("/reports")
@roles_required("admin", "instructor")
def reports_page():
    return render_template("reports.html")


@bp.route("/users")
@roles_required("admin")
def users():
    return render_template("users.html", users=User.query.order_by(User.id).all())


@bp.route("/users/<int:user_id>/status", methods=["POST"])
@roles_required("admin")
def set_status(user_id):
    user = db.get_or_404(User, user_id)
    status = request.form.get("status")
    if status not in ("active", "locked"):
        flash("Invalid account status.")
    elif user.id == current_user.id:
        flash("You cannot change your own account status.")
    elif user.role == "admin" and user.status == "active" and status == "locked" and User.query.filter_by(
        role="admin", status="active"
    ).count() <= 1:
        flash("At least one active admin account must remain.")
    else:
        previous_status = user.status
        user.status = status
        db.session.add(AuditLog(
            user_id=current_user.id,
            action="change_status",
            entity_type="user",
            entity_id=user.id,
            details=json.dumps({"from": previous_status, "to": status}),
        ))
        db.session.commit()
        flash(f"{user.username} is now {status}.")
    return redirect(url_for("main.users"))
