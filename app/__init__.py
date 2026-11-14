
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import current_user, logout_user

from config import Config
from app.extensions import db, migrate, login_manager, csrf


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import models.
    from app import models

    # Import blueprints.
    from app.auth import auth
    from app.providers import providers
    from app.admin import admin
    from app.bookings import bookings
    from app.ai import ai

    # Register blueprints.
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(providers, url_prefix="/providers")
    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(bookings, url_prefix="/bookings")
    app.register_blueprint(ai, url_prefix="/ai")

    # Load logged-in users.
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(models.User, int(user_id))

    # Check account status on every request.
    @app.before_request
    def check_account_status():
        if current_user.is_authenticated and not current_user.is_active:
            logout_user()

            flash(
                "Your account has been deactivated. Please contact support.",
                "error"
            )

            return redirect(url_for("auth.login"))

    # Homepage.
    @app.route("/")
    def home():
        return render_template("home.html")

    return app
