from flask import Blueprint
<<<<<<< HEAD
analysis_bp = Blueprint('analysis', __name__)
=======
# 'api' adalah nama internal, karena ini akan melayani /api
analysis_bp = Blueprint('api', __name__)
>>>>>>> 1a28d7f5a860d74198facd1c65210be6a133fa59
from . import routes