-- For a new install, import is_buddies_flask-1.sql to create all tables.
-- For an existing install, run `python migrate_db.py` to add new fields/tables
-- and link existing named customers to their sales.
CREATE DATABASE IF NOT EXISTS is_buddies_flask
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
