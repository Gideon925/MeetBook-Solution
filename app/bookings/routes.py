from datetime import datetime

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.bookings import bookings
from app.extensions import db
from app.models import User, ProviderProfile, ProviderListing, Booking


def booking_form(provider, selected_listing=None, form_data=None):
    return render_template(
        "booking_form.html",
        provider=provider,
        selected_listing=selected_listing,
        form_data=form_data or {},
        today=datetime.now().strftime("%Y-%m-%d")
    )


@bookings.route("/create/<int:profile_id>", methods=["GET", "POST"])
@login_required
def create_booking(profile_id):

    if current_user.account_type != "customer":
        flash("Only customer accounts can make bookings.", "error")
        return redirect(url_for("home"))

    provider = (
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

    if provider.user_id == current_user.id:
        flash("You cannot book your own service.", "error")
        return redirect(url_for("home"))

    listing_id = (
        request.form.get("listing_id")
        if request.method == "POST"
        else request.args.get("listing_id")
    )

    selected_listing = None

    if listing_id:
        try:
            listing_id = int(listing_id)
        except (ValueError, TypeError):
            flash("Invalid product or service selection.", "error")
            return redirect(
                url_for(
                    "providers.provider_storefront",
                    profile_id=provider.id
                )
            )

        selected_listing = ProviderListing.query.filter_by(
            id=listing_id,
            provider_profile_id=provider.id,
            is_available=True
        ).first()

        if selected_listing is None:
            flash(
                "This product or service is no longer available.",
                "error"
            )
            return redirect(
                url_for(
                    "providers.provider_storefront",
                    profile_id=provider.id
                )
            )

        if not selected_listing.catalogue_item.is_active:
            flash("This catalogue item is no longer active.", "error")
            return redirect(
                url_for(
                    "providers.provider_storefront",
                    profile_id=provider.id
                )
            )

    if request.method == "POST":

        address = request.form.get("service_address", "").strip()
        state = request.form.get("state", "").strip()
        city = request.form.get("city", "").strip()
        date_text = request.form.get("preferred_date", "").strip()
        time_text = request.form.get("preferred_time", "").strip()
        customer_notes = request.form.get(
            "service_description", ""
        ).strip()

        form_data = request.form

        if not all([address, state, city, date_text, time_text]):
            flash("Please complete all required booking fields.", "error")
            return booking_form(provider, selected_listing, form_data)

        if selected_listing is None and not customer_notes:
            flash("Please describe the service you need.", "error")
            return booking_form(provider, selected_listing, form_data)

        try:
            preferred_date = datetime.strptime(
                date_text, "%Y-%m-%d"
            ).date()

            preferred_time = datetime.strptime(
                time_text, "%H:%M"
            ).time()

            requested_datetime = datetime.combine(
                preferred_date, preferred_time
            )

            if requested_datetime < datetime.now():
                flash(
                    "Your selected booking date and time cannot be in the past.",
                    "error"
                )
                return booking_form(
                    provider, selected_listing, form_data
                )

        except ValueError:
            flash(
                "Please enter a valid booking date and time.",
                "error"
            )
            return booking_form(provider, selected_listing, form_data)

        if selected_listing:
            item_name = selected_listing.catalogue_item.name
            item_unit = selected_listing.unit or "unit"

            booking_description = (
                f"Selected product/service: {item_name}\n"
                f"Unit: {item_unit}\n"
                f"Customer request: "
                f"{customer_notes or 'No additional notes'}"
            )

            booking_price = selected_listing.price

        else:
            booking_description = customer_notes
            booking_price = provider.starting_price

        booking = Booking(
            customer_id=current_user.id,
            provider_profile_id=provider.id,
            service_description=booking_description,
            service_address=address,
            state=state,
            city=city,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            estimated_price=booking_price,
            status="Pending"
        )

        try:
            db.session.add(booking)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "We could not submit your booking. Please try again.",
                "error"
            )
            return booking_form(provider, selected_listing, form_data)

        flash(
            "Your booking request has been submitted successfully.",
            "success"
        )

        return redirect(url_for("bookings.my_bookings"))

    return booking_form(provider, selected_listing)


@bookings.route("/my-bookings")
@login_required
def my_bookings():

    if current_user.account_type != "customer":
        flash("This page is for customers.", "error")
        return redirect(url_for("home"))

    customer_bookings = (
        Booking.query
        .filter_by(customer_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return render_template(
        "my_bookings.html",
        bookings=customer_bookings
    )


@bookings.route("/provider-bookings")
@login_required
def provider_bookings():

    if current_user.account_type != "provider":
        flash("Only service providers can access this page.", "error")
        return redirect(url_for("home"))

    profile = ProviderProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        flash("Please create your business profile first.", "error")
        return redirect(url_for("auth.provider_dashboard"))

    provider_bookings_list = (
        Booking.query
        .filter_by(provider_profile_id=profile.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return render_template(
        "provider_bookings.html",
        bookings=provider_bookings_list
    )


@bookings.route(
    "/provider-bookings/<int:booking_id>/respond",
    methods=["POST"]
)
@login_required
def respond_to_booking(booking_id):

    if current_user.account_type != "provider":
        flash("Only providers can respond to booking requests.", "error")
        return redirect(url_for("home"))

    profile = ProviderProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        flash("Your provider profile was not found.", "error")
        return redirect(url_for("auth.provider_dashboard"))

    booking = Booking.query.filter_by(
        id=booking_id,
        provider_profile_id=profile.id
    ).first_or_404()

    if booking.status != "Pending":
        flash(
            "This booking has already been processed.",
            "error"
        )
        return redirect(url_for("bookings.provider_bookings"))

    action = request.form.get("action", "").strip().lower()

    if action == "accept":
        booking.status = "Accepted"
        flash("Booking accepted successfully.", "success")

    elif action == "reject":
        booking.status = "Rejected"
        flash("Booking rejected successfully.", "success")

    else:
        flash("Invalid booking action.", "error")
        return redirect(url_for("bookings.provider_bookings"))

    db.session.commit()

    return redirect(url_for("bookings.provider_bookings"))
