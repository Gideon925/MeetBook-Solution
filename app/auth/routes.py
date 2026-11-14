from datetime import datetime, timezone
from flask import render_template, request, redirect, url_for, flash
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from app.auth import auth
from app.extensions import db
from app.models import (
    User,
    ProviderProfile,
    ProviderListing,
    Booking,
    SubscriptionPlan,
    UserSubscription
)
def redirect_user(user):
    if user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if user.account_type == "provider":
        return redirect(url_for("auth.provider_dashboard"))

    return redirect(url_for("bookings.my_bookings"))


@auth.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect_user(current_user)

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        email = request.form.get("email", "").strip() or None
        account_type = request.form.get("account_type", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not phone_number or not password:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("auth.register"))

        if account_type not in ["customer", "provider", "business_owner"]:
            flash("Please select a valid account type.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(phone_number=phone_number).first():
            flash("This phone number is already registered.", "error")
            return redirect(url_for("auth.register"))

        if email and User.query.filter_by(email=email).first():
            flash("This email is already registered.", "error")
            return redirect(url_for("auth.register"))

        user = User(
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            account_type=account_type,
            provider_status=(
                "Pending" if account_type == "provider"
                else "Not Applicable"
            )
        )

        user.set_password(password)

        db.session.add(user)
        db.session.flush()
        
        free_plan = SubscriptionPlan.query.filter_by(
            code="free_monthly",
            is_active=True
        ).first()
        
        if not free_plan:
            db.session.rollback()
            flash("Registration is temporarily unavailable. Please try again.", "error")
            return redirect(url_for("auth.register"))
        
        subscription = UserSubscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status="active",
            starts_at=datetime.now(timezone.utc),
            ends_at=None,
            auto_renew=False
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        login_user(user)

        return redirect_user(user)

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect_user(current_user)

    if request.method == "POST":

        phone_number = request.form.get("phone_number", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(
            phone_number=phone_number
        ).first()

        if user and user.check_password(password):

            if not user.is_active:
                flash("Your account is inactive. Please contact support.", "error")
                return redirect(url_for("auth.login"))

            login_user(user)

            return redirect_user(user)

        flash("Incorrect phone number or password.", "error")

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))


@auth.route("/provider-dashboard")
@login_required
def provider_dashboard():

    if current_user.account_type != "provider":
        return redirect(url_for("home"))

    profile = ProviderProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    listing_count = 0
    available_listing_count = 0
    booking_count = 0
    pending_booking_count = 0

    if profile:

        listing_count = ProviderListing.query.filter_by(
            provider_profile_id=profile.id
        ).count()

        available_listing_count = ProviderListing.query.filter_by(
            provider_profile_id=profile.id,
            is_available=True
        ).count()

        booking_count = Booking.query.filter_by(
            provider_profile_id=profile.id
        ).count()

        pending_booking_count = Booking.query.filter_by(
            provider_profile_id=profile.id,
            status="Pending"
        ).count()

    return render_template(
        "provider_dashboard.html",
        profile=profile,
        listing_count=listing_count,
        available_listing_count=available_listing_count,
        booking_count=booking_count,
        pending_booking_count=pending_booking_count
    )
