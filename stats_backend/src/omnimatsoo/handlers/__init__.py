from flask import Blueprint
from flask_cors import CORS

collect_blueprint = Blueprint("collect", __name__, url_prefix="/collect")
CORS(collect_blueprint)

import omnimatsoo.handlers.collect
