from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=True)

    phone_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(db.String(255), nullable=False)

    account_type = db.Column(db.String(20), nullable=False)

    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    provider_status = db.Column(
        db.String(30),
        default="Not Applicable",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.full_name}>"

class ProviderProfile(db.Model):
    __tablename__ = "provider_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    business_name = db.Column(db.String(150), nullable=False)
    service_category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    state = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    lga = db.Column(db.String(100), nullable=False)
    neighbourhood = db.Column(db.String(150))
    business_address = db.Column(db.String(255))

    years_of_experience = db.Column(db.Integer, default=0)
    starting_price = db.Column(db.Numeric(12, 2), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship("User", backref="provider_profile")

    def __repr__(self):
        return f"<ProviderProfile {self.business_name}>"

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    provider_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("provider_profiles.id"),
        nullable=False
    )

    service_description = db.Column(db.Text, nullable=False)
    service_address = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)

    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.String(20), nullable=False)

    estimated_price = db.Column(db.Numeric(12, 2), nullable=True)

    status = db.Column(
        db.String(30), default="Pending", nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    customer = db.relationship("User", backref="customer_bookings")
    provider = db.relationship(
        "ProviderProfile", backref="received_bookings"
    )

    def __repr__(self):
        return f"<Booking {self.id} - {self.status}>"


class CatalogueItem(db.Model):
    """Predefined food, product or service names provided by MeetBook."""

    __tablename__ = "catalogue_items"

    id = db.Column(db.Integer, primary_key=True)
    division = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    listing_type = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class ProviderListing(db.Model):
    """An item selected from the catalogue and offered by a provider."""

    __tablename__ = "provider_listings"

    id = db.Column(db.Integer, primary_key=True)

    provider_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("provider_profiles.id"),
        nullable=False
    )

    catalogue_item_id = db.Column(
        db.Integer,
        db.ForeignKey("catalogue_items.id"),
        nullable=False
    )

    price = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    unit = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    provider = db.relationship(
        "ProviderProfile",
        backref="listings"
    )

    catalogue_item = db.relationship("CatalogueItem")

    def __repr__(self):
        return f"<ProviderListing {self.id}>"

class State(db.Model):
    __tablename__ = 'states'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(10), nullable=False, unique=True)
    
    lgas = db.relationship('LGA', backref='state', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<State {self.name}>"


class LGA(db.Model):
    __tablename__ = 'lgas'
    
    id = db.Column(db.Integer, primary_key=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    
    service_areas = db.relationship('ServiceArea', backref='lga', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<LGA {self.name}>"


class ServiceArea(db.Model):
    __tablename__ = 'service_areas'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider_profiles.id'), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    lga_id = db.Column(db.Integer, db.ForeignKey('lgas.id'), nullable=False)
    
    state = db.relationship('State', backref='service_areas', lazy=True)

    def __repr__(self):
        return f"<ServiceArea Provider {self.provider_id} -> LGA {self.lga_id}>"


class AIConversation(db.Model):
    __tablename__ = "ai_conversations"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False,
        default="New chat"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    messages = db.relationship(
        "AIMessage",
        backref="conversation",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at"
    )

    user = db.relationship(
        "User",
        backref="ai_conversations"
    )

    def __repr__(self):
        return f"<AIConversation {self.id}>"


class AIMessage(db.Model):
    __tablename__ = "ai_messages"

    id = db.Column(db.Integer, primary_key=True)

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("ai_conversations.id"),
        nullable=False,
        index=True
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<AIMessage {self.id} - {self.role}>"


class SubscriptionPlan(db.Model):
    __tablename__ = "subscription_plans"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    billing_cycle = db.Column(db.String(20), nullable=False)

    price = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    message_limit = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<SubscriptionPlan {self.code}>"


class UserSubscription(db.Model):
    __tablename__ = "user_subscriptions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("subscription_plans.id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="active",
        nullable=False
    )

    starts_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    ends_at = db.Column(db.DateTime(timezone=True))

    auto_renew = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="subscriptions"
    )

    plan = db.relationship(
        "SubscriptionPlan",
        backref="subscriptions"
    )

    def __repr__(self):
        return f"<UserSubscription {self.user_id}>"


class SubscriptionPayment(db.Model):
    __tablename__ = "subscription_payments"

    id = db.Column(db.Integer, primary_key=True)

    subscription_id = db.Column(
        db.Integer,
        db.ForeignKey("user_subscriptions.id"),
        nullable=False
    )

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(
        db.String(10),
        default="NGN",
        nullable=False
    )

    payment_provider = db.Column(db.String(50))

    provider_reference = db.Column(
        db.String(150),
        unique=True,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )

    paid_at = db.Column(db.DateTime(timezone=True))

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    subscription = db.relationship(
        "UserSubscription",
        backref="payments"
    )

    def __repr__(self):
        return f"<SubscriptionPayment {self.id}>"
