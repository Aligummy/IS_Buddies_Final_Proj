import sys
sys.path.insert(0, ".")
from sqlalchemy import text
from isbuddies import create_app, db

app = create_app()
with app.app_context():
    alters = [
        "ALTER TABLE `product` ADD COLUMN IF NOT EXISTS `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE `product` ADD COLUMN IF NOT EXISTS `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        "ALTER TABLE `sale` ADD COLUMN IF NOT EXISTS `payment_method` VARCHAR(32) DEFAULT 'Cash'",
        "ALTER TABLE `sale` ADD COLUMN IF NOT EXISTS `amount_tendered` DECIMAL(10,2) DEFAULT 0",
        "ALTER TABLE `users` ADD COLUMN IF NOT EXISTS `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP",
    ]
    for sql in alters:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print("OK:", sql)
        except Exception as e:
            db.session.rollback()
            print("ERR:", sql, e)
    print("Migration finished.")
