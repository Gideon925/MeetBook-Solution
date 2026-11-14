from flask import Blueprint

providers = Blueprint("providers", __name__)

from app.providers import routes
