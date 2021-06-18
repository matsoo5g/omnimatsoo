from flask import Blueprint
from flask_cors import CORS

collect_blueprint = Blueprint("collect", __name__, url_prefix="/collect")
aggr_blueprint = Blueprint("aggr", __name__, url_prefix="/aggr")
CORS(collect_blueprint)
CORS(aggr_blueprint)

import omnimatsoo.handlers.collect
import omnimatsoo.handlers.aggr
