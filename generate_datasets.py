"""
Generate CSV datasets for IS Buddies - School/Office Supplies Store
Generates 4 datasets for ML analysis:
1. product_demand.csv (1200 records) - regression
2. sales_history.csv (1500 records) - sales forecasting
3. slow_moving_products.csv (1000 records) - classification
4. best_selling_products.csv (1000 records) - classification
"""

import numpy as np
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

np.random.seed(42)

# Output directory - passed as arg or default
if len(sys.argv) > 1:
    OUTPUT_DIR = sys.argv[1]
else:
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# PRODUCT CATALOG - Realistic Filipino school/office supplies
# ============================================================
PRODUCTS = [
    # (product_id, product_name, category, min_price, max_price, popularity_weight)
    ("P001", "Notebook 80 Leaves", "Paper", 25, 45, 10),
    ("P002", "Notebook 200 Leaves", "Paper", 55, 80, 8),
    ("P003", "Composition Notebook", "Paper", 20, 35, 7),
    ("P004", "Spiral Notebook A4", "Paper", 60, 90, 6),
    ("P005", "Bond Paper A4 (Ream)", "Paper", 200, 350, 9),
    ("P006", "Bond Paper Short (Ream)", "Paper", 180, 300, 8),
    ("P007", "Yellow Pad Paper", "Paper", 30, 50, 7),
    ("P008", "Index Cards (Pack)", "Paper", 25, 45, 5),
    ("P009", "Construction Paper (Pack)", "Paper", 35, 60, 6),
    ("P010", "Pad Paper", "Paper", 15, 30, 6),
    ("P011", "Ballpen Blue (Pcs)", "Writing", 10, 18, 10),
    ("P012", "Ballpen Black (Pcs)", "Writing", 10, 18, 9),
    ("P013", "Ballpen Red (Pcs)", "Writing", 10, 18, 5),
    ("P014", "Pencil No. 2 (Pcs)", "Writing", 8, 15, 9),
    ("P015", "Mechanical Pencil", "Writing", 25, 60, 6),
    ("P016", "Sign Pen Black", "Writing", 20, 45, 7),
    ("P017", "Sign Pen Blue", "Writing", 20, 45, 6),
    ("P018", "Whiteboard Marker", "Writing", 30, 55, 5),
    ("P019", "Permanent Marker", "Writing", 25, 50, 4),
    ("P020", "Highlighter (Pcs)", "Writing", 20, 40, 7),
    ("P021", "Highlighter Set (6 colors)", "Writing", 90, 150, 5),
    ("P022", "Crayons 8 Colors", "Art Supplies", 25, 45, 7),
    ("P023", "Crayons 16 Colors", "Art Supplies", 40, 75, 8),
    ("P024", "Crayons 24 Colors", "Art Supplies", 55, 100, 6),
    ("P025", "Watercolor Set", "Art Supplies", 35, 80, 5),
    ("P026", "Oil Pastel 12 Colors", "Art Supplies", 45, 90, 5),
    ("P027", "Colored Pencils 12s", "Art Supplies", 50, 100, 6),
    ("P028", "Colored Pencils 24s", "Art Supplies", 90, 160, 4),
    ("P029", "Acrylic Paint Set", "Art Supplies", 120, 250, 3),
    ("P030", "Paint Brush Set", "Art Supplies", 40, 85, 3),
    ("P031", "Plastic Folder A4", "Filing", 12, 25, 8),
    ("P032", "Plastic Folder Long", "Filing", 12, 25, 8),
    ("P033", "Clear Book 20 Pockets", "Filing", 35, 65, 6),
    ("P034", "Clear Book 40 Pockets", "Filing", 55, 95, 5),
    ("P035", "Expanding Envelope", "Filing", 25, 50, 6),
    ("P036", "Brown Envelope Long", "Filing", 3, 8, 7),
    ("P037", "Brown Envelope Short", "Filing", 3, 7, 6),
    ("P038", "Ring Binder 1 inch", "Filing", 65, 120, 4),
    ("P039", "Ring Binder 2 inch", "Filing", 85, 150, 3),
    ("P040", "File Organizer", "Filing", 80, 180, 3),
    ("P041", "Ruler 12 inches (Plastic)", "Measuring", 10, 20, 7),
    ("P042", "Ruler 18 inches (Plastic)", "Measuring", 15, 30, 4),
    ("P043", "Protractor", "Measuring", 10, 25, 4),
    ("P044", "Triangle Set", "Measuring", 20, 45, 4),
    ("P045", "Compass (Drawing)", "Measuring", 25, 60, 3),
    ("P046", "Eraser (Pcs)", "Desk Accessories", 5, 12, 9),
    ("P047", "Sharpener (Pcs)", "Desk Accessories", 5, 15, 8),
    ("P048", "Scissors (Student)", "Desk Accessories", 25, 55, 6),
    ("P049", "Calculator (Basic)", "Desk Accessories", 120, 250, 5),
    ("P050", "Calculator (Scientific)", "Desk Accessories", 350, 750, 4),
    ("P051", "Stapler No. 35", "Desk Accessories", 55, 120, 4),
    ("P052", "Staple Wire No. 35", "Desk Accessories", 20, 40, 5),
    ("P053", "Paper Clips (Box)", "Desk Accessories", 15, 30, 5),
    ("P054", "Push Pins (Box)", "Desk Accessories", 15, 30, 3),
    ("P055", "Desk Organizer", "Desk Accessories", 80, 200, 2),
    ("P056", "Glue Stick", "Adhesives", 15, 35, 7),
    ("P057", "White Glue 120ml", "Adhesives", 20, 40, 6),
    ("P058", "Packaging Tape", "Adhesives", 30, 60, 4),
    ("P059", "Masking Tape", "Adhesives", 25, 50, 4),
    ("P060", "Double-Sided Tape", "Adhesives", 25, 55, 3),
    ("P061", "Correction Tape", "Writing", 18, 40, 8),
    ("P062", "Correction Fluid", "Writing", 25, 50, 5),
    ("P063", "Pencil Case (Basic)", "Organization", 35, 80, 6),
    ("P064", "Pencil Case (Premium)", "Organization", 80, 180, 4),
    ("P065", "Bag Tag / ID Lace", "Organization", 10, 30, 5),
    ("P066", "Book Cover (Roll)", "Organization", 15, 35, 6),
    ("P067", "Sticker Labels (Pack)", "Organization", 20, 45, 4),
    ("P068", "Sticky Notes (Pad)", "Organization", 20, 50, 6),
    ("P069", "Sticky Notes (Set)", "Organization", 45, 100, 4),
    ("P070", "Clipboard", "Organization", 40, 85, 3),
]

# Pre-generate fixed prices for each product
PRODUCT_PRICES = {}
for p in PRODUCTS:
    PRODUCT_PRICES[p[0]] = round(np.random.uniform(p[3], p[4]), 2)


def is_school_season(month):
    """Philippine school calendar: June-October and January-March."""
    return 1 if month in [1, 2, 3, 6, 7, 8, 9, 10] else 0


def get_seasonal_multiplier(month, category):
    """Higher demand during school season, varies by category."""
    base = 1.0
    if is_school_season(month):
        if month in [6, 7]:  # School opening peak
            base = 2.5
        elif month in [8, 9, 10]:
            base = 1.8
        elif month in [1, 2]:  # Second semester
            base = 1.6
        elif month == 3:
            base = 1.3
    else:
        base = 0.6  # April, May, November, December off-season

    # December gets a small bump for holiday gift supplies
    if month == 12:
        base = 0.9

    # Category-specific adjustments
    if category == "Art Supplies" and month in [6, 7, 8]:
        base *= 1.2
    elif category == "Filing" and month in [1, 2, 3]:
        base *= 1.1

    return base


# ============================================================
# Dataset 1: product_demand.csv (1200 records)
# ============================================================
def generate_product_demand(n=1200):
    print(f"Generating product_demand.csv ({n} records)...")
    records = []

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 10, 31)
    total_days = (end_date - start_date).days
    pop_weights = np.array([p[5] for p in PRODUCTS], dtype=float)
    pop_weights /= pop_weights.sum()

    for _ in range(n):
        random_day = np.random.randint(0, total_days)
        date = start_date + timedelta(days=int(random_day))
        day_of_week = date.strftime("%A")
        month = date.month

        prod_idx = np.random.choice(len(PRODUCTS), p=pop_weights)
        prod = PRODUCTS[prod_idx]
        product_id = prod[0]
        product_name = prod[1]
        category = prod[2]
        unit_price = PRODUCT_PRICES[product_id]
        popularity = prod[5]

        school_season = is_school_season(month)
        seasonal_mult = get_seasonal_multiplier(month, category)

        base_qty = popularity * 2
        qty_sold = max(1, int(np.random.poisson(base_qty * seasonal_mult)))

        if date.weekday() >= 5:
            qty_sold = max(1, int(qty_sold * 0.7))

        if school_season:
            stock_level = max(5, int(np.random.normal(80, 30)))
        else:
            stock_level = max(10, int(np.random.normal(150, 40)))

        revenue = round(qty_sold * unit_price, 2)

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "day_of_week": day_of_week,
            "month": month,
            "is_school_season": school_season,
            "unit_price": unit_price,
            "stock_level": stock_level,
            "qty_sold": qty_sold,
            "revenue": revenue,
        })

    df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
    path = os.path.join(OUTPUT_DIR, "product_demand.csv")
    df.to_csv(path, index=False)
    print(f"  -> Saved {len(df)} records to {path}")
    return df


# ============================================================
# Dataset 2: sales_history.csv (1500 records)
# ============================================================
def generate_sales_history(n=1500):
    print(f"Generating sales_history.csv ({n} records)...")
    records = []

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 10, 31)
    total_days = (end_date - start_date).days

    payment_methods = ["Cash", "GCash", "Maya"]
    payment_weights = [0.50, 0.35, 0.15]
    discount_options = [0, 0, 0, 0, 5, 5, 10, 10, 15, 20]

    pop_weights = np.array([p[5] for p in PRODUCTS], dtype=float)
    pop_weights /= pop_weights.sum()

    for _ in range(n):
        random_day = np.random.randint(0, total_days)
        date = start_date + timedelta(days=int(random_day))
        month = date.month
        year = date.year

        prod_idx = np.random.choice(len(PRODUCTS), p=pop_weights)
        prod = PRODUCTS[prod_idx]
        product_id = prod[0]
        product_name = prod[1]
        category = prod[2]
        unit_price = PRODUCT_PRICES[product_id]
        popularity = prod[5]

        seasonal_mult = get_seasonal_multiplier(month, category)

        base_qty = popularity * 1.5
        qty_sold = max(1, int(np.random.poisson(base_qty * seasonal_mult)))

        if date.weekday() >= 5:
            qty_sold = max(1, int(qty_sold * 0.75))

        total_amount = round(qty_sold * unit_price, 2)

        discount_pct = int(np.random.choice(discount_options))
        if not is_school_season(month) and np.random.random() < 0.3:
            discount_pct = int(np.random.choice([10, 15, 20]))

        net_amount = round(total_amount * (1 - discount_pct / 100), 2)

        payment_method = np.random.choice(payment_methods, p=payment_weights)

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "month": month,
            "year": year,
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "qty_sold": qty_sold,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "discount_pct": discount_pct,
            "net_amount": net_amount,
            "payment_method": payment_method,
        })

    df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
    path = os.path.join(OUTPUT_DIR, "sales_history.csv")
    df.to_csv(path, index=False)
    print(f"  -> Saved {len(df)} records to {path}")
    return df


# ============================================================
# Dataset 3: slow_moving_products.csv (1000 records)
# ============================================================
def generate_slow_moving(n=1000):
    print(f"Generating slow_moving_products.csv ({n} records)...")
    records = []

    for i in range(n):
        prod_idx = np.random.choice(len(PRODUCTS))
        prod = PRODUCTS[prod_idx]
        product_id = f"{prod[0]}_{i:04d}"
        product_name = prod[1]
        category = prod[2]
        unit_price = PRODUCT_PRICES[prod[0]]
        popularity = prod[5]

        force_slow = np.random.random() < 0.38

        if force_slow:
            avg_monthly_sales = round(np.random.uniform(0.5, 8), 1)
            stock_level = int(np.random.uniform(30, 200))
            days_since_last_sale = int(np.random.uniform(31, 120))
            reorder_level = int(np.random.uniform(10, 30))
            turnover_rate = round(np.random.uniform(0.05, 0.49), 2)
        else:
            avg_monthly_sales = round(np.random.uniform(8, 80) * (popularity / 5), 1)
            stock_level = int(np.random.uniform(15, 150))
            days_since_last_sale = int(np.random.uniform(0, 30))
            reorder_level = int(np.random.uniform(10, 40))
            turnover_rate = round(np.random.uniform(0.5, 3.0), 2)

        is_slow = 1 if (turnover_rate < 0.5 and days_since_last_sale > 30) else 0

        records.append({
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "unit_price": unit_price,
            "avg_monthly_sales": avg_monthly_sales,
            "stock_level": stock_level,
            "days_since_last_sale": days_since_last_sale,
            "reorder_level": reorder_level,
            "turnover_rate": turnover_rate,
            "is_slow_moving": is_slow,
        })

    df = pd.DataFrame(records)
    slow_pct = df["is_slow_moving"].mean() * 100
    print(f"  -> Slow-moving ratio: {slow_pct:.1f}%")
    path = os.path.join(OUTPUT_DIR, "slow_moving_products.csv")
    df.to_csv(path, index=False)
    print(f"  -> Saved {len(df)} records to {path}")
    return df


# ============================================================
# Dataset 4: best_selling_products.csv (1000 records)
# ============================================================
def generate_best_selling(n=1000):
    print(f"Generating best_selling_products.csv ({n} records)...")
    records = []

    for i in range(n):
        prod_idx = np.random.choice(len(PRODUCTS))
        prod = PRODUCTS[prod_idx]
        product_id = f"{prod[0]}_{i:04d}"
        product_name = prod[1]
        category = prod[2]
        unit_price = PRODUCT_PRICES[prod[0]]
        popularity = prod[5]

        months_available = int(np.random.uniform(3, 34))

        force_best = np.random.random() < 0.27

        if force_best:
            avg_monthly_sales = round(np.random.uniform(40, 150) * (popularity / 5), 1)
            total_qty_sold = int(avg_monthly_sales * months_available * np.random.uniform(0.85, 1.15))
            total_revenue = round(total_qty_sold * unit_price, 2)
            popularity_score = round(np.random.uniform(71, 98), 1)
        else:
            avg_monthly_sales = round(np.random.uniform(2, 50) * (popularity / 5), 1)
            total_qty_sold = int(avg_monthly_sales * months_available * np.random.uniform(0.8, 1.2))
            total_revenue = round(total_qty_sold * unit_price, 2)
            popularity_score = round(np.random.uniform(5, 70), 1)

        is_best_seller = 1 if popularity_score > 70 else 0

        records.append({
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "unit_price": unit_price,
            "total_qty_sold": total_qty_sold,
            "total_revenue": total_revenue,
            "avg_monthly_sales": avg_monthly_sales,
            "months_available": months_available,
            "popularity_score": popularity_score,
            "is_best_seller": is_best_seller,
        })

    df = pd.DataFrame(records)
    best_pct = df["is_best_seller"].mean() * 100
    print(f"  -> Best-seller ratio: {best_pct:.1f}%")
    path = os.path.join(OUTPUT_DIR, "best_selling_products.csv")
    df.to_csv(path, index=False)
    print(f"  -> Saved {len(df)} records to {path}")
    return df


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("IS Buddies - Dataset Generator")
    print("School & Office Supplies Store")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}\n")

    df1 = generate_product_demand(1200)
    print()
    df2 = generate_sales_history(1500)
    print()
    df3 = generate_slow_moving(1000)
    print()
    df4 = generate_best_selling(1000)

    print("\n" + "=" * 60)
    print("All datasets generated successfully!")
    print(f"  product_demand.csv      : {len(df1)} records")
    print(f"  sales_history.csv       : {len(df2)} records")
    print(f"  slow_moving_products.csv: {len(df3)} records")
    print(f"  best_selling_products.csv: {len(df4)} records")
    print("=" * 60)
