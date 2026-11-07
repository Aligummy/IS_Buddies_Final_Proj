import click
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config

def ensure_database(uri):
    """Create the MySQL database if it does not exist yet."""
    url = make_url(uri)
    server = create_engine(url._replace(database=None))
    with server.begin() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    server.dispose()


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    ensure_database(app.config["SQLALCHEMY_DATABASE_URI"])
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from .auth import bp as auth_bp
    from .views import bp as main_bp
    from .api import bp as api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Exempt API endpoints from CSRF (they use JSON, not forms)
    csrf.exempt(api_bp)

    from .models import User

    with app.app_context():
        db.create_all()

    @app.cli.command("create-admin")
    @click.argument("username")
    @click.password_option()
    def create_admin(username, password):
        """Create an active admin (or instructor) account: flask create-admin NAME"""
        u = User(full_name=username, email=f"{username}@local", username=username,
                 role="admin", status="active")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        click.echo(f"Admin '{username}' created.")

    return app
