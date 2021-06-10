from flask import request, jsonify, current_app
from omnimatsoo.handlers import collect_blueprint
from omnimatsoo.entities import PlaybackStatistics
from omnimatsoo.services import ServiceClients as SVC


@collect_blueprint.route("/", methods=["POST"])
def _():
    result = request.get_json(force=True)
    current_app.logger.debug(f"Received: {result}")
    try:
        SVC.playback_benchmark.add(PlaybackStatistics(**result))
    except Exception as ex:
        current_app.logger.error(f"Unable to parse received payload: {ex}")
        raise

    return jsonify("")


@collect_blueprint.route("/", methods=["GET"])
def get_all():
    return jsonify(SVC.playback_benchmark.list())
