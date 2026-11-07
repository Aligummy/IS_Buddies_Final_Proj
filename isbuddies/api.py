"""
API Blueprint – JSON endpoints for AJAX calls from the frontend.
Handles: Inventory CRUD, Sales transactions, Knowledge Analysis, User management.
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func, desc

from . import db
from .models import Product, Sale, SaleItem, StockLog, Supplier, PredictionLog, User

bp = Blueprint("api", __name__, url_prefix="/api")


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


# ---------------------------------------------------------------------------
# Inventory / Product CRUD
# ---------------------------------------------------------------------------

@bp.route("/products")
@roles_required("admin", "instructor", "inventory_clerk", "sales_personnel")
def list_products():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)

    query = Product.query
    if q:
        query = query.filter(
            Product.name.ilike(f"%{q}%") | Product.sku.ilike(f"%{q}%")
        )
    if cat:
        query = query.filter(Product.category == cat)

    query = query.order_by(Product.name)
    pag = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "products": [
            {
                "id": p.id, "sku": p.sku, "name": p.name,
                "category": p.category, "supplier": p.supplier,
                "stock": p.stock, "reorder_level": p.reorder_level,
                "unit_price": float(p.unit_price),
                "status": p.status_label, "status_class": p.status_class,
            }
            for p in pag.items
        ],
        "page": pag.page,
        "pages": pag.pages,
        "total": pag.total,
    })


@bp.route("/products", methods=["POST"])
@roles_required("admin", "inventory_clerk")
def create_product():
    d = request.get_json(force=True)
    if Product.query.filter_by(sku=d.get("sku", "").strip()).first():
        return jsonify({"error": "SKU already exists"}), 400
    p = Product(
        sku=d["sku"].strip(),
        name=d["name"].strip(),
        category=d.get("category", "").strip() or None,
        supplier=d.get("supplier", "").strip() or None,
        stock=int(d.get("stock", 0)),
        reorder_level=int(d.get("reorder_level", 0)),
        unit_price=Decimal(str(d.get("unit_price", 0))),
    )
    db.session.add(p)
    db.session.flush()
    # Log the initial stock
    if p.stock > 0:
        db.session.add(StockLog(
            product_id=p.id, user_id=current_user.id,
            change=p.stock, reason="Initial stock"
        ))
    db.session.commit()
    return jsonify({"id": p.id, "message": "Product created"}), 201


@bp.route("/products/<int:pid>", methods=["PUT"])
@roles_required("admin", "inventory_clerk")
def update_product(pid):
    p = db.get_or_404(Product, pid)
    d = request.get_json(force=True)
    old_stock = p.stock

    p.name = d.get("name", p.name).strip()
    p.category = d.get("category", p.category)
    p.supplier = d.get("supplier", p.supplier)
    p.reorder_level = int(d.get("reorder_level", p.reorder_level))
    p.unit_price = Decimal(str(d.get("unit_price", p.unit_price)))

    new_stock = int(d.get("stock", p.stock))
    if new_stock != old_stock:
        diff = new_stock - old_stock
        p.stock = new_stock
        db.session.add(StockLog(
            product_id=p.id, user_id=current_user.id,
            change=diff, reason="Manual adjustment"
        ))

    db.session.commit()
    return jsonify({"message": "Product updated"})


@bp.route("/products/<int:pid>", methods=["DELETE"])
@roles_required("admin", "inventory_clerk")
def delete_product(pid):
    p = db.get_or_404(Product, pid)
    # Check if product is referenced in any sale
    if SaleItem.query.filter_by(product_id=pid).first():
        return jsonify({"error": "Cannot delete product with sale history"}), 400
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Product deleted"})


@bp.route("/products/categories")
@login_required
def product_categories():
    cats = db.session.query(Product.category).distinct().filter(
        Product.category.isnot(None)
    ).order_by(Product.category).all()
    return jsonify([c[0] for c in cats])


# ---------------------------------------------------------------------------
# Stock management
# ---------------------------------------------------------------------------

@bp.route("/products/<int:pid>/restock", methods=["POST"])
@roles_required("admin", "inventory_clerk")
def restock_product(pid):
    p = db.get_or_404(Product, pid)
    d = request.get_json(force=True)
    qty = int(d.get("qty", 0))
    if qty <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400
    p.stock += qty
    db.session.add(StockLog(
        product_id=p.id, user_id=current_user.id,
        change=qty, reason=d.get("reason", "Restock")
    ))
    db.session.commit()
    return jsonify({"message": f"Added {qty} to stock", "new_stock": p.stock})


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------

@bp.route("/sales", methods=["POST"])
@roles_required("admin", "sales_personnel")
def create_sale():
    d = request.get_json(force=True)
    items = d.get("items", [])
    if not items:
        return jsonify({"error": "No items in the sale"}), 400

    sale = Sale(
        cashier_id=current_user.id,
        customer=d.get("customer", "").strip() or None,
        payment_method=d.get("payment_method", "Cash"),
        amount_tendered=Decimal(str(d.get("amount_tendered", 0))),
        discount=Decimal(str(d.get("discount", 0))),
    )
    db.session.add(sale)
    db.session.flush()

    subtotal = Decimal("0")
    for item in items:
        product = db.get_or_404(Product, item["product_id"])
        qty = int(item["qty"])
        if qty > product.stock:
            db.session.rollback()
            return jsonify({"error": f"Insufficient stock for {product.name} (available: {product.stock})"}), 400
        price = product.unit_price
        si = SaleItem(sale_id=sale.id, product_id=product.id, qty=qty, unit_price=price)
        db.session.add(si)
        subtotal += price * qty
        # Deduct stock
        product.stock -= qty
        db.session.add(StockLog(
            product_id=product.id, user_id=current_user.id,
            change=-qty, reason=f"Sale #{sale.id}"
        ))

    sale.total = subtotal - sale.discount
    if sale.total < 0:
        sale.total = Decimal("0")

    db.session.commit()

    return jsonify({
        "message": "Sale completed",
        "sale_id": sale.id,
        "receipt_no": sale.receipt_no,
        "total": float(sale.total),
        "change": float(sale.change_amount),
    }), 201


@bp.route("/sales")
@roles_required("admin", "instructor", "sales_personnel")
def list_sales():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    pag = Sale.query.order_by(Sale.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "sales": [
            {
                "id": s.id,
                "receipt_no": s.receipt_no,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
                "cashier": s.cashier.full_name if s.cashier else "N/A",
                "customer": s.customer or "Walk-in",
                "payment_method": s.payment_method,
                "discount": float(s.discount),
                "total": float(s.total),
                "items": [
                    {
                        "product": si.product.name if si.product else "Unknown",
                        "qty": si.qty,
                        "unit_price": float(si.unit_price),
                        "subtotal": si.subtotal,
                    }
                    for si in s.items
                ],
            }
            for s in pag.items
        ],
        "page": pag.page,
        "pages": pag.pages,
        "total": pag.total,
    })


@bp.route("/sales/<int:sid>")
@roles_required("admin", "instructor", "sales_personnel")
def get_sale(sid):
    s = db.get_or_404(Sale, sid)
    return jsonify({
        "id": s.id,
        "receipt_no": s.receipt_no,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
        "cashier": s.cashier.full_name if s.cashier else "N/A",
        "customer": s.customer or "Walk-in",
        "payment_method": s.payment_method,
        "amount_tendered": float(s.amount_tendered),
        "discount": float(s.discount),
        "total": float(s.total),
        "change": float(s.change_amount),
        "items": [
            {
                "product": si.product.name if si.product else "Unknown",
                "qty": si.qty,
                "unit_price": float(si.unit_price),
                "subtotal": si.subtotal,
            }
            for si in s.items
        ],
    })


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

@bp.route("/dashboard/stats")
@roles_required("admin", "instructor")
def dashboard_stats():
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    # Sales today
    sales_today = db.session.query(func.coalesce(func.sum(Sale.total), 0)).filter(
        Sale.created_at >= today_start
    ).scalar()

    # Low stock items
    low_stock = Product.query.filter(Product.stock <= Product.reorder_level).count()

    # Total products
    total_products = Product.query.count()

    # Total sales count
    total_sales = Sale.query.count()

    # Best selling product (by qty sold)
    best_seller = db.session.query(
        Product.name, func.sum(SaleItem.qty).label("total_qty")
    ).join(SaleItem, SaleItem.product_id == Product.id
    ).group_by(Product.name
    ).order_by(desc("total_qty")
    ).first()

    # Recent 5 transactions
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()

    # Monthly sales data for chart (last 12 months)
    monthly_sales = []
    for i in range(11, -1, -1):
        d = today - timedelta(days=i * 30)
        month_start = d.replace(day=1)
        if d.month == 12:
            month_end = d.replace(year=d.year + 1, month=1, day=1)
        else:
            month_end = d.replace(month=d.month + 1, day=1)
        total = db.session.query(func.coalesce(func.sum(Sale.total), 0)).filter(
            Sale.created_at >= month_start, Sale.created_at < month_end
        ).scalar()
        monthly_sales.append({
            "month": month_start.strftime("%b %Y"),
            "total": float(total),
        })

    # Top 5 products by quantity sold
    top_products = db.session.query(
        Product.name, func.sum(SaleItem.qty).label("total_qty")
    ).join(SaleItem, SaleItem.product_id == Product.id
    ).group_by(Product.name
    ).order_by(desc("total_qty")
    ).limit(5).all()

    # Slow moving products (no sale in 30+ days)
    thirty_days_ago = today_start - timedelta(days=30)
    subq = db.session.query(SaleItem.product_id).join(Sale).filter(
        Sale.created_at >= thirty_days_ago
    ).distinct().subquery()
    slow_products = Product.query.filter(
        Product.stock > 0,
        ~Product.id.in_(db.session.query(subq))
    ).order_by(Product.stock.desc()).limit(5).all()

    return jsonify({
        "sales_today": float(sales_today),
        "low_stock": low_stock,
        "total_products": total_products,
        "total_sales": total_sales,
        "best_seller": best_seller[0] if best_seller else "N/A",
        "best_seller_qty": best_seller[1] if best_seller else 0,
        "monthly_sales": monthly_sales,
        "top_products": [
            {"name": p[0], "qty": int(p[1])} for p in top_products
        ],
        "slow_products": [
            {"name": p.name, "stock": p.stock, "category": p.category}
            for p in slow_products
        ],
        "recent_sales": [
            {
                "receipt_no": s.receipt_no,
                "cashier": s.cashier.full_name if s.cashier else "N/A",
                "total": float(s.total),
                "date": s.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for s in recent_sales
        ],
    })


# ---------------------------------------------------------------------------
# Knowledge Analysis & Prediction
# ---------------------------------------------------------------------------

@bp.route("/knowledge/train", methods=["POST"])
@roles_required("admin", "instructor")
def knowledge_train():
    from . import knowledge as ka
    d = request.get_json(force=True)
    pred_type = d.get("prediction_type")
    model_name = d.get("model", "slr")  # slr or random_forest

    trainers = {
        "demand": ka.train_demand,
        "sales": ka.train_sales,
        "slow_moving": ka.train_slow_moving,
        "best_selling": ka.train_best_selling,
    }

    trainer = trainers.get(pred_type)
    if not trainer:
        return jsonify({"error": f"Unknown prediction type: {pred_type}"}), 400

    try:
        metrics = trainer(model_name)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Add descriptions
    described_metrics = {}
    for key, value in metrics.items():
        described_metrics[key] = {
            "value": value,
            "description": ka.METRIC_DESCRIPTIONS.get(key, ""),
        }

    # Save to prediction log
    log = PredictionLog(
        user_id=current_user.id,
        prediction_type=pred_type,
        model_used=model_name,
        input_params=json.dumps({"action": "train"}),
        result=json.dumps({"status": "trained"}),
        metrics=json.dumps(metrics),
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "message": f"Model trained and saved successfully",
        "model": model_name,
        "prediction_type": pred_type,
        "metrics": described_metrics,
    })


@bp.route("/knowledge/predict", methods=["POST"])
@roles_required("admin", "instructor")
def knowledge_predict():
    from . import knowledge as ka
    d = request.get_json(force=True)
    pred_type = d.get("prediction_type")
    model_name = d.get("model", "slr")
    params = d.get("params", {})

    try:
        if pred_type == "demand":
            result = ka.predict_demand(
                model_name,
                month=int(params.get("month", 1)),
                day_of_week=int(params.get("day_of_week", 0)),
                is_school_season=int(params.get("is_school_season", 0)),
                unit_price=float(params.get("unit_price", 0)),
                stock_level=int(params.get("stock_level", 0)),
            )
            result_data = {"predicted_qty": result}
        elif pred_type == "sales":
            result = ka.predict_sales(
                model_name,
                month=int(params.get("month", 1)),
                year=int(params.get("year", 2026)),
                qty_sold=int(params.get("qty_sold", 0)),
                unit_price=float(params.get("unit_price", 0)),
                discount_pct=float(params.get("discount_pct", 0)),
            )
            result_data = {"predicted_amount": result}
        elif pred_type == "slow_moving":
            result = ka.predict_slow_moving(
                model_name,
                unit_price=float(params.get("unit_price", 0)),
                avg_monthly_sales=float(params.get("avg_monthly_sales", 0)),
                stock_level=int(params.get("stock_level", 0)),
                days_since_last_sale=int(params.get("days_since_last_sale", 0)),
                reorder_level=int(params.get("reorder_level", 0)),
                turnover_rate=float(params.get("turnover_rate", 0)),
            )
            result_data = {
                "classification": "Slow-Moving" if result == 1 else "Fast-Moving",
                "is_slow_moving": result,
            }
        elif pred_type == "best_selling":
            result = ka.predict_best_selling(
                model_name,
                unit_price=float(params.get("unit_price", 0)),
                total_qty_sold=int(params.get("total_qty_sold", 0)),
                total_revenue=float(params.get("total_revenue", 0)),
                avg_monthly_sales=float(params.get("avg_monthly_sales", 0)),
                months_available=int(params.get("months_available", 0)),
                popularity_score=float(params.get("popularity_score", 0)),
            )
            result_data = {
                "classification": "Best-Seller" if result == 1 else "Regular Product",
                "is_best_seller": result,
            }
        else:
            return jsonify({"error": f"Unknown prediction type: {pred_type}"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Save to prediction log
    log = PredictionLog(
        user_id=current_user.id,
        prediction_type=pred_type,
        model_used=model_name,
        input_params=json.dumps(params),
        result=json.dumps(result_data),
        metrics=None,
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "prediction_type": pred_type,
        "model": model_name,
        "result": result_data,
    })


@bp.route("/knowledge/datasets")
@roles_required("admin", "instructor")
def list_datasets():
    from . import knowledge as ka
    try:
        info = ka.get_dataset_info()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(info)


@bp.route("/knowledge/datasets/<name>")
@roles_required("admin", "instructor")
def preview_dataset(name):
    from . import knowledge as ka
    rows = request.args.get("rows", 20, type=int)
    try:
        data = ka.get_dataset_preview(name, rows=rows)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(data)


# ---------------------------------------------------------------------------
# User management (admin)
# ---------------------------------------------------------------------------

@bp.route("/users")
@roles_required("admin")
def list_users():
    users = User.query.order_by(User.id).all()
    return jsonify([
        {
            "id": u.id, "full_name": u.full_name, "username": u.username,
            "email": u.email, "role": u.role, "role_label": u.role_label,
            "status": u.status,
            "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else None,
        }
        for u in users
    ])


@bp.route("/users/<int:uid>/role", methods=["PUT"])
@roles_required("admin")
def change_role(uid):
    user = db.get_or_404(User, uid)
    if user.id == current_user.id:
        return jsonify({"error": "Cannot change your own role"}), 400
    d = request.get_json(force=True)
    role = d.get("role")
    valid_roles = {"admin", "instructor", "inventory_clerk", "sales_personnel"}
    if role not in valid_roles:
        return jsonify({"error": f"Invalid role: {role}"}), 400
    user.role = role
    db.session.commit()
    return jsonify({"message": f"Role changed to {role}"})


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

@bp.route("/suppliers")
@roles_required("admin", "inventory_clerk")
def list_suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify([
        {
            "id": s.id, "name": s.name, "contact_person": s.contact_person,
            "phone": s.phone, "email": s.email, "address": s.address,
        }
        for s in suppliers
    ])


@bp.route("/suppliers", methods=["POST"])
@roles_required("admin", "inventory_clerk")
def create_supplier():
    d = request.get_json(force=True)
    s = Supplier(
        name=d["name"].strip(),
        contact_person=d.get("contact_person", "").strip() or None,
        phone=d.get("phone", "").strip() or None,
        email=d.get("email", "").strip() or None,
        address=d.get("address", "").strip() or None,
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"id": s.id, "message": "Supplier created"}), 201
