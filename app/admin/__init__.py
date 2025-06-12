from flask import Blueprint

# Create the admin blueprint
admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin'
)

# Import routes to register view functions
from . import routes  # noqa: F401, E402
