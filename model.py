from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(150), nullable=False)

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=True
    )

    phone_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    account_type = db.Column(
        db.String(20),
        nullable=False
    )

    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<User {self.full_name}>"
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
