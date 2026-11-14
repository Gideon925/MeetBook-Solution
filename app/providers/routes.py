

from decimal import Decimal, InvalidOperation

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.providers import providers
from app.extensions import db
from app.models import User, ProviderProfile, CatalogueItem, ProviderListing


# Official MeetBook Solutions divisions
DIVISIONS = [
    "Food",
    "Home",
    "Business",
    "Connect",
    "Moving",
    "Pet Care",
    "Mobility",
    "Health",
]


def get_provider_profile():
    """Return the current approved provider's profile, or None."""

    if current_user.account_type != "provider":
        flash("Only provider accounts can access this page.", "error")
        return None

    if not current_user.is_active:
        flash("Your account is inactive. Contact support.", "error")
        return None

    if current_user.provider_status != "Approved":
        flash("Your provider account must be approved first.", "error")
        return None

    profile = ProviderProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        flash("Please create your business profile first.", "error")
        return None

    return profile


def get_owned_listing(listing_id, profile):
    """Find a listing only if it belongs to the current provider."""

    return (
        ProviderListing.query
        .filter_by(
            id=listing_id,
            provider_profile_id=profile.id
        )
        .first_or_404()
    )


# ---------------------------------------------------------
# CUSTOMER PROVIDER SEARCH
# ---------------------------------------------------------

@providers.route("/search")
def search_providers():

    service = request.args.get("service", "").strip()
    location = request.args.get("location", "").strip()

    query = (
        ProviderProfile.query
        .join(User)
        .filter(
            User.account_type == "provider",
            User.is_active.is_(True),
            User.provider_status == "Approved"
        )
    )

    if service:

        search_term = f"%{service}%"

        matching_listing_profiles = (
            db.session.query(ProviderListing.provider_profile_id)
            .join(CatalogueItem)
            .filter(
                ProviderListing.is_available.is_(True),
                CatalogueItem.is_active.is_(True),
                or_(
                    CatalogueItem.name.ilike(search_term),
                    CatalogueItem.category.ilike(search_term),
                    CatalogueItem.division.ilike(search_term),
                    ProviderListing.description.ilike(search_term)
                )
            )
        )

        query = query.filter(
            or_(
                ProviderProfile.business_name.ilike(search_term),
                ProviderProfile.service_category.ilike(search_term),
                ProviderProfile.description.ilike(search_term),
                ProviderProfile.id.in_(matching_listing_profiles)
            )
        )

    if location:

        location_words = location.split()

        for word in location_words:

            location_term = f"%{word}%"

            query = query.filter(
                or_(
                    ProviderProfile.city.ilike(location_term),
                    ProviderProfile.state.ilike(location_term),
                    ProviderProfile.lga.ilike(location_term),
                    ProviderProfile.neighbourhood.ilike(location_term)
                )
            )

    providers_found = (
        query
        .order_by(ProviderProfile.created_at.desc())
        .all()
    )

    return render_template(
        "provider_search.html",
        providers=providers_found,
        service=service,
        location=location
    )


# ---------------------------------------------------------
# CREATE PROVIDER PROFILE
# ---------------------------------------------------------

@providers.route("/profile", methods=["GET", "POST"])
@login_required
def create_profile():

    if current_user.account_type != "provider":
        flash("Only provider accounts can create provider profiles.", "error")
        return redirect(url_for("home"))

    if not current_user.is_active:
        flash("Your account is inactive. Contact support.", "error")
        return redirect(url_for("auth.logout"))

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
            price = float(starting_price) if starting_price else None

            if years < 0 or (price is not None and price < 0):
                raise ValueError

        except ValueError:
            flash(
                "Please enter valid experience and pricing values.",
                "error"
            )
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


# ---------------------------------------------------------
# VIEW PROVIDER PROFILE
# ---------------------------------------------------------

@providers.route("/profile/view")
@login_required
def view_profile():

    if current_user.account_type != "provider":
        return redirect(url_for("home"))

    if not current_user.is_active:
        flash("Your account is inactive. Contact support.", "error")
        return redirect(url_for("auth.logout"))

    profile = ProviderProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return redirect(url_for("providers.create_profile"))

    return render_template(
        "view_provider_profile.html",
        profile=profile
    )


# ---------------------------------------------------------
# MANAGE PROVIDER PRODUCTS AND SERVICES
# ---------------------------------------------------------

@providers.route("/listings", methods=["GET", "POST"])
@login_required
def manage_listings():

    profile = get_provider_profile()

    if not profile:
        return redirect(url_for("auth.provider_dashboard"))

    divisions = DIVISIONS

    selected_division = request.values.get("division", "Food")

    if selected_division not in divisions:
        selected_division = "Food"

    if request.method == "POST":

        catalogue_id = request.form.get("catalogue_item_id", "")
        price_text = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        unit = request.form.get("unit", "").strip()

        try:
            catalogue_item = db.session.get(
                CatalogueItem,
                int(catalogue_id)
            )

            price = Decimal(price_text)

            if (
                not catalogue_item
                or not catalogue_item.is_active
                or catalogue_item.division != selected_division
                or not price.is_finite()
                or price <= 0
            ):
                raise ValueError

        except (ValueError, TypeError, InvalidOperation):
            flash(
                "Please select a valid item and enter a price above zero.",
                "error"
            )
            return redirect(url_for(
                "providers.manage_listings",
                division=selected_division
            ))

        existing = ProviderListing.query.filter_by(
            provider_profile_id=profile.id,
            catalogue_item_id=catalogue_item.id
        ).first()

        if existing:
            flash(
                "You have already added this item to your business.",
                "error"
            )
            return redirect(url_for(
                "providers.manage_listings",
                division=selected_division
            ))

        listing = ProviderListing(
            provider_profile_id=profile.id,
            catalogue_item_id=catalogue_item.id,
            price=price,
            description=description,
            unit=unit,
            is_available=True
        )

        db.session.add(listing)
        db.session.commit()

        flash("Your item has been added successfully.", "success")

        return redirect(url_for(
            "providers.manage_listings",
            division=selected_division
        ))

    catalogue_items = (
        CatalogueItem.query
        .filter_by(
            division=selected_division,
            is_active=True
        )
        .order_by(
            CatalogueItem.category,
            CatalogueItem.name
        )
        .all()
    )

    listings = (
        ProviderListing.query
        .filter_by(provider_profile_id=profile.id)
        .order_by(ProviderListing.created_at.desc())
        .all()
    )

    return render_template(
        "provider_listings.html",
        divisions=divisions,
        selected_division=selected_division,
        catalogue_items=catalogue_items,
        listings=listings
    )


# ---------------------------------------------------------
# EDIT A PROVIDER LISTING
# ---------------------------------------------------------

@providers.route("/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit_listing(listing_id):

    profile = get_provider_profile()

    if not profile:
        return redirect(url_for("auth.provider_dashboard"))

    listing = get_owned_listing(listing_id, profile)

    if request.method == "POST":

        price_text = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        unit = request.form.get("unit", "").strip()

        try:
            price = Decimal(price_text)

            if not price.is_finite() or price <= 0:
                raise ValueError

        except (ValueError, TypeError, InvalidOperation):
            flash("Please enter a valid price above zero.", "error")
            return redirect(url_for(
                "providers.edit_listing",
                listing_id=listing.id
            ))

        listing.price = price
        listing.description = description
        listing.unit = unit

        db.session.commit()

        flash("Your listing has been updated successfully.", "success")

        return redirect(url_for(
            "providers.manage_listings",
            division=listing.catalogue_item.division
        ))

    return render_template(
        "edit_provider_listing.html",
        listing=listing
    )


# ---------------------------------------------------------
# CHANGE LISTING AVAILABILITY
# ---------------------------------------------------------

@providers.route("/listings/<int:listing_id>/toggle", methods=["POST"])
@login_required
def toggle_listing_availability(listing_id):

    profile = get_provider_profile()

    if not profile:
        return redirect(url_for("auth.provider_dashboard"))

    listing = get_owned_listing(listing_id, profile)

    listing.is_available = not listing.is_available

    db.session.commit()

    if listing.is_available:
        flash("Your listing is now available.", "success")
    else:
        flash("Your listing is now unavailable.", "success")

    return redirect(url_for(
        "providers.manage_listings",
        division=listing.catalogue_item.division
    ))


# ---------------------------------------------------------
# DELETE A PROVIDER LISTING
# ---------------------------------------------------------

@providers.route("/listings/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):

    profile = get_provider_profile()

    if not profile:
        return redirect(url_for("auth.provider_dashboard"))

    listing = get_owned_listing(listing_id, profile)
    division = listing.catalogue_item.division

    db.session.delete(listing)
    db.session.commit()

    flash("Your listing has been deleted.", "success")

    return redirect(url_for(
        "providers.manage_listings",
        division=division
    ))


# ---------------------------------------------------------
# PUBLIC PROVIDER STOREFRONT
# ---------------------------------------------------------

@providers.route("/store/<int:profile_id>")
def provider_storefront(profile_id):
    """Public page showing a provider's available products and services."""

    profile = (
        ProviderProfile.query
        .join(User)
        .filter(
            ProviderProfile.id == profile_id,
            User.account_type == "provider",
            User.is_active.is_(True),
            User.provider_status == "Approved"
        )
        .first_or_404()
    )

    listings = (
        ProviderListing.query
        .filter_by(
            provider_profile_id=profile.id,
            is_available=True
        )
        .order_by(ProviderListing.created_at.desc())
        .all()
    )

    return render_template(
        "customer_storefront.html",
        profile=profile,
        listings=listings
    )


# ---------------------------------------------------------
# EDIT PROVIDER BUSINESS PROFILE
# ---------------------------------------------------------

@providers.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():

    profile = get_provider_profile()

    if not profile:
        return redirect(url_for("auth.provider_dashboard"))

    if request.method == "POST":

        business_name = request.form.get("business_name", "").strip()
        service_category = request.form.get("service_category", "").strip()
        description = request.form.get("description", "").strip()
        state = request.form.get("state", "").strip()
        city = request.form.get("city", "").strip()
        lga = request.form.get("lga", "").strip()
        neighbourhood = request.form.get("neighbourhood", "").strip()
        business_address = request.form.get("business_address", "").strip()
        experience = request.form.get("years_of_experience", "0").strip()
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
            return redirect(url_for("providers.edit_profile"))

        if service_category not in DIVISIONS:
            flash("Please select one of the official MeetBook divisions.", "error")
            return redirect(url_for("providers.edit_profile"))

        try:
            years = int(experience)
            price = Decimal(starting_price) if starting_price else None

            if years < 0:
                raise ValueError

            if price is not None and (
                not price.is_finite() or price < 0
            ):
                raise ValueError

        except (ValueError, TypeError, InvalidOperation):
            flash("Enter valid experience and starting-price values.", "error")
            return redirect(url_for("providers.edit_profile"))

        profile.business_name = business_name
        profile.service_category = service_category
        profile.description = description
        profile.state = state
        profile.city = city
        profile.lga = lga
        profile.neighbourhood = neighbourhood
        profile.business_address = business_address
        profile.years_of_experience = years
        profile.starting_price = float(price) if price is not None else None

        db.session.commit()

        flash("Your business profile has been updated successfully.", "success")
        return redirect(url_for("providers.view_profile"))

    return render_template(
        "edit_provider_profile.html",
        profile=profile,
        divisions=DIVISIONS
    )


