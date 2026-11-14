
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request
)
from flask_login import (
    login_required,
    current_user,
    login_user,
    logout_user
)

from app.admin import admin
from app.models import User, ProviderProfile
from app.extensions import db


# Protect every admin page.
@admin.before_request
def protect_admin():

    # Allow the separate admin login page.
    if request.endpoint == "admin.login":
        return

    if not current_user.is_authenticated:
        return redirect(url_for("admin.login"))

    if not current_user.is_admin:
        flash("You are not authorised to access the admin area.", "error")
        return redirect(url_for("home"))


# Separate administrator login.
@admin.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":

        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            db.or_(
                User.email == identifier,
                User.phone_number == identifier
            )
        ).filter_by(is_admin=True).first()

        if user and user.is_active and user.check_password(password):

            login_user(user)

            flash("Administrator login successful.", "success")

            return redirect(url_for("admin.dashboard"))

        flash("Invalid administrator credentials.", "error")

    return render_template("admin_login.html")


# Administrator dashboard.
@admin.route("/")
def dashboard():

    total_users = User.query.count()

    total_providers = User.query.filter_by(
        account_type="provider"
    ).count()

    pending_providers = User.query.filter_by(
        account_type="provider",
        provider_status="Pending"
    ).count()

    approved_providers = User.query.filter_by(
        account_type="provider",
        provider_status="Approved"
    ).count()

    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_providers=total_providers,
        pending_providers=pending_providers,
        approved_providers=approved_providers,
        active_users=active_users,
        inactive_users=inactive_users
    )


# Administrator logout.
@admin.route("/logout")
def logout():

    logout_user()

    flash("Administrator logged out successfully.", "success")

    return redirect(url_for("admin.login"))


@admin.route("/providers")
def provider_applications():

    applications = (
        User.query.filter_by(account_type="provider")
        .order_by(User.created_at.desc())
        .all()
    )

    return render_template(
        "admin_providers.html",
        applications=applications
    )


@admin.route("/approve/<int:user_id>", methods=["POST"])
def approve_provider(user_id):

    provider = User.query.filter_by(
        id=user_id,
        account_type="provider"
    ).first_or_404()

    if not provider.is_active:
        flash("Reactivate this account before approving it.", "error")
        return redirect(url_for("admin.provider_applications"))

    provider.provider_status = "Approved"
    db.session.commit()

    flash("Provider approved successfully.", "success")

    return redirect(url_for("admin.provider_applications"))


@admin.route("/users")
def manage_users():

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "all")

    users_query = User.query

    if search:
        users_query = users_query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    if status == "active":
        users_query = users_query.filter_by(is_active=True)

    elif status == "inactive":
        users_query = users_query.filter_by(is_active=False)

    users = users_query.order_by(
        User.created_at.desc()
    ).all()

    return render_template(
        "admin_users.html",
        users=users,
        search=search,
        status=status
    )


@admin.route("/users/<int:user_id>/deactivate", methods=["POST"])
def deactivate_user(user_id):

    user = db.session.get(User, user_id)

    if not user:
        flash("User account not found.", "error")
        return redirect(url_for("admin.manage_users"))

    if user.id == current_user.id or user.is_admin:
        flash("This administrator account cannot be deactivated here.", "error")
        return redirect(url_for("admin.manage_users"))

    user.is_active = False
    db.session.commit()

    flash(f"{user.full_name}'s account has been deactivated.", "success")

    return redirect(url_for("admin.manage_users"))


@admin.route("/users/<int:user_id>/activate", methods=["POST"])
def activate_user(user_id):

    user = db.session.get(User, user_id)

    if not user:
        flash("User account not found.", "error")
        return redirect(url_for("admin.manage_users"))

    user.is_active = True
    db.session.commit()

    flash(f"{user.full_name}'s account has been reactivated.", "success")

    return redirect(url_for("admin.manage_users"))
