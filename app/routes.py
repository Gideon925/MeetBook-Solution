
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.providers import providers
from app.extensions import db
from app.models import User, ProviderProfile


# CUSTOMER: SEARCH FOR SERVICE PROVIDERS
@providers.route("/search")
def search_providers():

    service = request.args.get("service", "").strip()
    location = request.args.get("location", "").strip()

    results = (
        ProviderProfile.query
        .join(User)
        .filter(
            User.account_type == "provider",
            User.provider_status == "Approved"
        )
    )

    if service:
        results = results.filter(
            or_(
                ProviderProfile.service_category.ilike(f"%{service}%"),
                ProviderProfile.business_name.ilike(f"%{service}%"),
                ProviderProfile.description.ilike(f"%{service}%")
            )
        )

    if location:
        results = results.filter(
            or_(
                ProviderProfile.city.ilike(f"%{location}%"),
                ProviderProfile.state.ilike(f"%{location}%"),
                ProviderProfile.lga.ilike(f"%{location}%"),
                ProviderProfile.neighbourhood.ilike(f"%{location}%")
            )
        )

    providers_found = results.order_by(
        ProviderProfile.created_at.desc()
    ).all()

    return render_template(
        "provider_search.html",
        providers=providers_found,
        service=service,
        location=location
    )


# PROVIDER: CREATE BUSINESS PROFILE
@providers.route("/profile", methods=["GET", "POST"])
@login_required
def create_profile():

    if current_user.account_type != "provider":
        return redirect(url_for("home"))

    if current_user.provider_status != "Approved":
        flash("Your provider account must be approved first.", "error")
        return redirect(url_for("auth.provider_dashboard"))

    existing_profile = ProviderProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if existing_profile:
        return redirect(url_for("providers.view_profile"))

    if request.method == "POST":

        business_name = request.form.get("business_name", "").strip()
        service_category = request.form.get("service_category", "").strip()
        description = request.form.get("description", "").strip()
        state = request.form.get("state", "").strip()
        city = request.form.get("city", "").strip()
        lga = request.form.get("lga", "").strip()
        neighbourhood = request.form.get("neighbourhood", "").strip()
        business_address = request.form.get("business_address", "").strip()

        experience = request.form.get("years_of_experience", "0")
        starting_price = request.form.get("starting_price", "").strip()

        if not all([
            business_name,
            service_category,
            description,
            state,
            city,
            lga
        ]):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("providers.create_profile"))

        try:
            years = int(experience)

            if years < 0:
                raise ValueError

            price = float(starting_price) if starting_price else None

            if price is not None and price < 0:
                raise ValueError

        except ValueError:
            flash("Please enter valid experience and pricing values.", "error")
            return redirect(url_for("providers.create_profile"))

        profile = ProviderProfile(
            user_id=current_user.id,
            business_name=business_name,
            service_category=service_category,
            description=description,
            state=state,
            city=city,
            lga=lga,
            neighbourhood=neighbourhood,
            business_address=business_address,
            years_of_experience=years,
            starting_price=price
        )

        db.session.add(profile)
        db.session.commit()

        flash("Your provider profile has been created.", "success")

        return redirect(url_for("providers.view_profile"))

    return render_template("provider_profile.html")


# PROVIDER: VIEW BUSINESS PROFILE
@providers.route("/profile/view")
@login_required
def view_profile():

    profile = ProviderProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return redirect(url_for("providers.create_profile"))

    return render_template(
        "view_provider_profile.html",
        profile=profile
    )
