from flask import Blueprint


collect_blueprint = Blueprint("collect", __name__, url_prefix="/collect")

import omnimatsoo.handlers.collect
