"""
Database Seeder for IS Buddies (School & Office Supplies)
Seeds realistic initial products, suppliers, and instructor account.

Use ``python seed_db.py --demo`` to add fictional customers and sales for testing.
"""
import argparse
from datetime import datetime, timedelta
from decimal import Decimal

from isbuddies import create_app, db
from isbuddies.models import Customer, Product, Sale, SaleItem, Supplier, User

app = create_app()

INITIAL_SUPPLIERS = [
    {
        "name": "Advance Paper Corporation",
        "contact_person": "Renato Santos",
        "phone": "0917-555-1234",
        "email": "orders@advancepaper.ph",
        "address": "Caloocan City, Metro Manila"
    },
    {
        "name": "Pilot Pen Philippines / Cosmos",
        "contact_person": "Grace Lim",
        "phone": "0920-888-9900",
        "email": "sales@pilotpen.ph",
        "address": "Quezon City, Metro Manila"
    },
    {
        "name": "Sterling Paper Products",
        "contact_person": "Eduardo Cruz",
        "phone": "0918-222-3344",
        "email": "corporate@sterling.ph",
        "address": "Meycauayan, Bulacan"
    },
    {
        "name": "Faber-Castell PH Supply",
        "contact_person": "Carmela Reyes",
        "phone": "0919-444-5566",
        "email": "inquiry@fabercastell.ph",
        "address": "Pasig City, Metro Manila"
    }
]

INITIAL_PRODUCTS = [
    # Paper & Notebooks
    {"sku": "NB-SP-001", "name": "Spiral Notebook 80 leaves (Assorted)", "category": "Paper", "supplier": "Advance Paper Corporation", "stock": 180, "reorder_level": 30, "unit_price": 28.50},
    {"sku": "NB-CM-002", "name": "Composition Notebook 80 leaves", "category": "Paper", "supplier": "Advance Paper Corporation", "stock": 150, "reorder_level": 30, "unit_price": 27.00},
    {"sku": "BP-A4-001", "name": "Hard Copy A4 Bond Paper (70gsm, 500 sheets)", "category": "Paper", "supplier": "Sterling Paper Products", "stock": 65, "reorder_level": 15, "unit_price": 240.00},
    {"sku": "BP-ST-002", "name": "Hard Copy Short Bond Paper (70gsm, 500 sheets)", "category": "Paper", "supplier": "Sterling Paper Products", "stock": 70, "reorder_level": 15, "unit_price": 220.00},
    {"sku": "BP-LG-003", "name": "Hard Copy Long Bond Paper (70gsm, 500 sheets)", "category": "Paper", "supplier": "Sterling Paper Products", "stock": 55, "reorder_level": 15, "unit_price": 260.00},
    {"sku": "YP-PAD-01", "name": "Yellow Intermediate Writing Pad (80 leaves)", "category": "Paper", "supplier": "Advance Paper Corporation", "stock": 140, "reorder_level": 25, "unit_price": 38.00},
    {"sku": "IP-PAD-02", "name": "1/4 Quiz Pad Paper (80 leaves)", "category": "Paper", "supplier": "Advance Paper Corporation", "stock": 200, "reorder_level": 40, "unit_price": 18.00},
    
    # Writing Instruments
    {"sku": "PEN-BK-01", "name": "Pilot G-Tech-C4 0.3mm (Black)", "category": "Writing", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 90, "reorder_level": 20, "unit_price": 85.00},
    {"sku": "PEN-BL-02", "name": "Pilot G-Tech-C4 0.3mm (Blue)", "category": "Writing", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 85, "reorder_level": 20, "unit_price": 85.00},
    {"sku": "BP-HB-01", "name": "HBW Matrix Ballpen 0.5mm (Black)", "category": "Writing", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 350, "reorder_level": 50, "unit_price": 9.00},
    {"sku": "BP-HB-02", "name": "HBW Matrix Ballpen 0.5mm (Blue)", "category": "Writing", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 300, "reorder_level": 50, "unit_price": 9.00},
    {"sku": "BP-HB-03", "name": "HBW Matrix Ballpen 0.5mm (Red)", "category": "Writing", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 150, "reorder_level": 30, "unit_price": 9.00},
    {"sku": "PC-FB-01", "name": "Faber-Castell 2B Pencil (Box of 12)", "category": "Writing", "supplier": "Faber-Castell PH Supply", "stock": 60, "reorder_level": 12, "unit_price": 110.00},
    {"sku": "HL-PS-01", "name": "Pastel Highlighter Set (6 colors)", "category": "Writing", "supplier": "Faber-Castell PH Supply", "stock": 45, "reorder_level": 10, "unit_price": 145.00},
    {"sku": "WB-MK-01", "name": "Whiteboard Marker (Black, Bullet Tip)", "category": "Writing", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 75, "reorder_level": 15, "unit_price": 42.00},
    
    # Filing & Organization
    {"sku": "FL-SH-01", "name": "Short Brown Kraft Envelope (Pack of 10)", "category": "Filing", "supplier": "Sterling Paper Products", "stock": 80, "reorder_level": 20, "unit_price": 35.00},
    {"sku": "FL-LG-02", "name": "Long Brown Kraft Envelope (Pack of 10)", "category": "Filing", "supplier": "Sterling Paper Products", "stock": 90, "reorder_level": 20, "unit_price": 42.00},
    {"sku": "FL-CL-03", "name": "Clear Plastic Folder Long with Slider (Pack of 5)", "category": "Filing", "supplier": "Advance Paper Corporation", "stock": 110, "reorder_level": 20, "unit_price": 65.00},
    {"sku": "BD-RN-01", "name": "2-Ring Binder Folder Long (Black)", "category": "Filing", "supplier": "Sterling Paper Products", "stock": 40, "reorder_level": 8, "unit_price": 135.00},
    
    # Art & Craft
    {"sku": "CR-CY-24", "name": "Crayola Crayons (24 colors)", "category": "Art Supplies", "supplier": "Faber-Castell PH Supply", "stock": 50, "reorder_level": 10, "unit_price": 115.00},
    {"sku": "OS-WS-12", "name": "Oil Pastel Set (12 colors)", "category": "Art Supplies", "supplier": "Faber-Castell PH Supply", "stock": 35, "reorder_level": 8, "unit_price": 95.00},
    {"sku": "SC-SS-01", "name": "Stainless School Scissors 5-inch (Blunt tip)", "category": "Art Supplies", "supplier": "Advance Paper Corporation", "stock": 60, "reorder_level": 12, "unit_price": 38.00},
    {"sku": "GL-ST-01", "name": "All-Purpose Glue Stick 21g", "category": "Adhesives", "supplier": "Faber-Castell PH Supply", "stock": 85, "reorder_level": 15, "unit_price": 32.00},
    {"sku": "TP-CL-01", "name": "Transparent Adhesive Tape 3/4 inch", "category": "Adhesives", "supplier": "Sterling Paper Products", "stock": 120, "reorder_level": 25, "unit_price": 22.00},
    
    # Desk & Math Tools
    {"sku": "RL-PL-12", "name": "Transparent Plastic Ruler 12-inch (30cm)", "category": "Measuring", "supplier": "Advance Paper Corporation", "stock": 130, "reorder_level": 25, "unit_price": 15.00},
    {"sku": "MT-ST-01", "name": "Math Protractor & Compass Set", "category": "Measuring", "supplier": "Advance Paper Corporation", "stock": 40, "reorder_level": 10, "unit_price": 85.00},
    {"sku": "CL-SC-01", "name": "Casio Scientific Calculator FX-991ES Plus", "category": "Measuring", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 18, "reorder_level": 5, "unit_price": 950.00},
    {"sku": "ST-HD-01", "name": "Heavy Duty Desktop Stapler with Staples (#35)", "category": "Desk Accessories", "supplier": "Sterling Paper Products", "stock": 25, "reorder_level": 5, "unit_price": 185.00},
    {"sku": "CT-CR-01", "name": "Correction Tape 5mm x 6m", "category": "Desk Accessories", "supplier": "Pilot Pen Philippines / Cosmos", "stock": 115, "reorder_level": 20, "unit_price": 45.00},
    {"sku": "ER-FB-01", "name": "Faber-Castell Dust-Free Eraser (Medium)", "category": "Desk Accessories", "supplier": "Faber-Castell PH Supply", "stock": 160, "reorder_level": 30, "unit_price": 16.00},
]


DEMO_CUSTOMERS = [
    {"name": "Demo Customer 01", "email": "customer01@example.test", "phone": "09170000001"},
    {"name": "Demo Customer 02", "email": "customer02@example.test", "phone": "09170000002"},
    {"name": "Demo Customer 03", "email": "customer03@example.test", "phone": "09170000003"},
    {"name": "Demo Customer 04", "email": "customer04@example.test", "phone": "09170000004"},
    {"name": "Demo Customer 05", "email": "customer05@example.test", "phone": "09170000005"},
]

# days ago, customer index, payment method, and (product SKU, quantity) pairs
DEMO_SALES = [
    (1, 0, "Cash", [("NB-SP-001", 2), ("BP-HB-01", 3)]),
    (3, 1, "GCash", [("BP-A4-001", 1), ("PEN-BK-01", 1)]),
    (5, 2, "Cash", [("FL-CL-03", 2), ("GL-ST-01", 1)]),
    (8, 3, "Card", [("CR-CY-24", 1), ("OS-WS-12", 1), ("SC-SS-01", 2)]),
    (12, 4, "Cash", [("NB-CM-002", 3), ("BP-HB-02", 2)]),
    (16, 0, "GCash", [("BP-ST-002", 1), ("YP-PAD-01", 2)]),
    (21, 1, "Cash", [("PC-FB-01", 1), ("ER-FB-01", 2)]),
    (27, 2, "Card", [("CT-CR-01", 2), ("WB-MK-01", 1)]),
    (34, 3, "Cash", [("IP-PAD-02", 4), ("RL-PL-12", 2)]),
    (42, 4, "GCash", [("CL-SC-01", 1), ("MT-ST-01", 1)]),
    (50, 0, "Cash", [("NB-SP-001", 2), ("BP-HB-02", 5)]),
    (59, 1, "Card", [("BP-LG-003", 1), ("FL-LG-02", 2)]),
    (68, 2, "Cash", [("HL-PS-01", 1), ("GL-ST-01", 2)]),
    (77, 3, "GCash", [("BP-HB-03", 4), ("FL-SH-01", 2)]),
    (88, 4, "Cash", [("BD-RN-01", 1), ("TP-CL-01", 2)]),
    (99, 0, "Card", [("NB-CM-002", 2), ("PEN-BL-02", 1)]),
    (111, 1, "Cash", [("ST-HD-01", 1), ("CT-CR-01", 1)]),
    (124, 2, "GCash", [("BP-A4-001", 1), ("IP-PAD-02", 2)]),
    (137, 3, "Cash", [("CR-CY-24", 2), ("PC-FB-01", 1)]),
    (150, 4, "Card", [("NB-SP-001", 3), ("BP-HB-01", 4)]),
]


def seed(include_demo=False):
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        # Seed suppliers
        for sup in INITIAL_SUPPLIERS:
            if not Supplier.query.filter_by(name=sup["name"]).first():
                db.session.add(Supplier(**sup))
        db.session.commit()
        print("Suppliers seeded.")

        # Seed products
        added_prods = 0
        for p in INITIAL_PRODUCTS:
            if not Product.query.filter_by(sku=p["sku"]).first():
                db.session.add(Product(**p))
                added_prods += 1
        db.session.commit()
        print(f"Products seeded: {added_prods} new products added.")

        # Ensure Instructor account exists
        instructor = User.query.filter_by(username="instructor").first()
        if not instructor:
            u = User(
                full_name="Professor / Instructor",
                email="instructor@school.edu.ph",
                username="instructor",
                role="instructor",
                status="active"
            )
            u.set_password("Instructor123")
            db.session.add(u)
            db.session.commit()
            print("Instructor account created: username 'instructor', password 'Instructor123'")
        else:
            instructor.status = "active"
            db.session.commit()
            print("Instructor account already exists.")

        if include_demo:
            instructor = User.query.filter_by(username="instructor").one()
            customers = []
            for customer_data in DEMO_CUSTOMERS:
                customer = Customer.query.filter_by(email=customer_data["email"]).first()
                if customer is None:
                    customer = Customer(**customer_data)
                    db.session.add(customer)
                customers.append(customer)
            db.session.flush()

            if Sale.query.filter(Sale.customer.like("DEMO - %")).first():
                print("Demo sales already exist; leaving them unchanged.")
            else:
                products = {product.sku: product for product in Product.query.all()}
                now = datetime.utcnow()
                for index, (days_ago, customer_index, payment_method, item_data) in enumerate(DEMO_SALES):
                    sale_time = now - timedelta(days=days_ago, hours=index % 9)
                    sale = Sale(
                        created_at=sale_time,
                        cashier_id=instructor.id,
                        customer_id=customers[customer_index].id,
                        customer=f"DEMO - {customers[customer_index].name}",
                        payment_method=payment_method,
                        discount=Decimal("0.00"),
                        amount_tendered=Decimal("0.00"),
                        total=Decimal("0.00"),
                    )
                    total = Decimal("0.00")
                    for sku, quantity in item_data:
                        product = products.get(sku)
                        if product is None:
                            raise RuntimeError(f"Cannot create demo sale: product {sku} is missing.")
                        unit_price = Decimal(product.unit_price)
                        total += unit_price * quantity
                        sale.items.append(SaleItem(
                            product_id=product.id,
                            qty=quantity,
                            returned_qty=0,
                            unit_price=unit_price,
                        ))
                    sale.total = total
                    sale.amount_tendered = total
                    db.session.add(sale)
                db.session.commit()
                print(f"Demo data seeded: {len(customers)} customers and {len(DEMO_SALES)} sales.")
            db.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed IS Buddies products, suppliers, and optional demo activity.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="also add clearly labeled fictional customers and historical sales",
    )
    seed(include_demo=parser.parse_args().demo)
