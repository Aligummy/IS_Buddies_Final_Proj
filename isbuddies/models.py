from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager

ROLE_LABELS = {
    "admin": "Admin",
    "instructor": "Instructor",
    "inventory_clerk": "Inventory Clerk",
    "sales_personnel": "Sales Personnel",
}


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="pending")  # pending | active | locked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(64))
    supplier = db.Column(db.String(120))
    stock = db.Column(db.Integer, default=0, nullable=False)
    reorder_level = db.Column(db.Integer, default=0, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def status_label(self):
        if self.stock <= 0:
            return "Out of stock"
        if self.stock <= self.reorder_level:
            return "Low stock"
        return "In stock"

    @property
    def status_class(self):
        if self.stock <= 0:
            return "r"
        if self.stock <= self.reorder_level:
            return "r"
        return "g"


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    cashier_id = db.Column(db.ForeignKey("users.id"))
    cashier = db.relationship("User", backref="sales")
    customer = db.Column(db.String(120))
    payment_method = db.Column(db.String(32), default="Cash")
    amount_tendered = db.Column(db.Numeric(10, 2), default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)
    items = db.relationship("SaleItem", backref="sale", cascade="all, delete-orphan")

    @property
    def change_amount(self):
        return max(0, float(self.amount_tendered or 0) - float(self.total or 0))

    @property
    def receipt_no(self):
        return f"RCT-{self.id:06d}"


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.ForeignKey("sale.id"), nullable=False)
    product_id = db.Column(db.ForeignKey("product.id"), nullable=False)
    product = db.relationship("Product")
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    @property
    def subtotal(self):
        return float(self.qty) * float(self.unit_price)


class StockLog(db.Model):
    """Tracks stock adjustments (additions, deductions from sales, manual adjustments)."""
    __tablename__ = "stock_log"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.ForeignKey("product.id"), nullable=False)
    product = db.relationship("Product")
    user_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User")
    change = db.Column(db.Integer, nullable=False)  # positive=add, negative=deduct
    reason = db.Column(db.String(120))  # e.g. "Sale #123", "Manual restock", "Stock adjustment"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Supplier(db.Model):
    """Supplier directory for the store."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    contact_person = db.Column(db.String(120))
    phone = db.Column(db.String(32))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PredictionLog(db.Model):
    """Stores prediction results for audit and review."""
    __tablename__ = "prediction_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User")
    prediction_type = db.Column(db.String(64), nullable=False)  # demand, sales, slow_moving, best_selling
    model_used = db.Column(db.String(64), nullable=False)  # slr, random_forest
    input_params = db.Column(db.Text)  # JSON string of inputs
    result = db.Column(db.Text)  # JSON string of prediction results
    metrics = db.Column(db.Text)  # JSON string of evaluation metrics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
