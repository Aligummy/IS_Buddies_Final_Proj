from sqlalchemy import inspect, text

from isbuddies import create_app, db


app = create_app()

with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    column_migrations = {
        "product": {
            "created_at": "ALTER TABLE `product` ADD COLUMN `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "ALTER TABLE `product` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        },
        "sale": {
            "payment_method": "ALTER TABLE `sale` ADD COLUMN `payment_method` VARCHAR(32) DEFAULT 'Cash'",
            "amount_tendered": "ALTER TABLE `sale` ADD COLUMN `amount_tendered` DECIMAL(10,2) DEFAULT 0",
            "customer_id": "ALTER TABLE `sale` ADD COLUMN `customer_id` INT NULL",
        },
        "sale_item": {
            "returned_qty": "ALTER TABLE `sale_item` ADD COLUMN `returned_qty` INT NOT NULL DEFAULT 0",
        },
        "users": {
            "created_at": "ALTER TABLE `users` ADD COLUMN `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP",
        },
    }

    with db.engine.begin() as connection:
        for table_name, migrations in column_migrations.items():
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, statement in migrations.items():
                if column_name not in existing_columns:
                    connection.execute(text(statement))
                    print(f"Added {table_name}.{column_name}")

        sale_foreign_keys = inspector.get_foreign_keys("sale")
        has_customer_foreign_key = any(
            key.get("referred_table") == "customer"
            and key.get("constrained_columns") == ["customer_id"]
            for key in sale_foreign_keys
        )
        if not has_customer_foreign_key:
            connection.execute(text(
                "ALTER TABLE `sale` ADD CONSTRAINT `fk_sale_customer` "
                "FOREIGN KEY (`customer_id`) REFERENCES `customer` (`id`)"
            ))
            print("Added sale.customer_id foreign key")

        customer_names = connection.execute(text(
            "SELECT MIN(TRIM(`customer`)) FROM `sale` "
            "WHERE `customer` IS NOT NULL AND TRIM(`customer`) <> '' "
            "AND `customer_id` IS NULL GROUP BY LOWER(TRIM(`customer`))"
        )).scalars().all()
        for customer_name in customer_names:
            customer_id = connection.execute(text(
                "SELECT `id` FROM `customer` "
                "WHERE LOWER(`name`) = LOWER(:name) LIMIT 1"
            ), {"name": customer_name}).scalar()
            if customer_id is None:
                inserted = connection.execute(text(
                    "INSERT INTO `customer` (`name`, `created_at`) "
                    "VALUES (:name, CURRENT_TIMESTAMP)"
                ), {"name": customer_name})
                customer_id = inserted.lastrowid
            connection.execute(text(
                "UPDATE `sale` SET `customer_id` = :customer_id "
                "WHERE `customer_id` IS NULL "
                "AND LOWER(TRIM(`customer`)) = LOWER(:name)"
            ), {"customer_id": customer_id, "name": customer_name})
    print("Database migration complete.")
