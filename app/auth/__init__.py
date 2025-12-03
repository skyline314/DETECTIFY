from flask import Blueprint

# Buat instance Blueprint
# 'auth' adalah nama internal untuk Blueprint ini
auth_bp = Blueprint('auth', __name__)

# Impor 'routes' di bagian bawah agar tidak circular import
from . import routes