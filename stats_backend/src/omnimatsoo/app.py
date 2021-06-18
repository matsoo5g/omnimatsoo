import logging
from flask import Flask
from omnimatsoo.handlers import collect_blueprint, aggr_blueprint
from omnimatsoo.kvstorage import SUPPORTED, Client
from omnimatsoo.services import ServiceClients


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = True
    app.register_blueprint(collect_blueprint)
    app.register_blueprint(aggr_blueprint)
    config_logger(app.logger)
    Client.init(SUPPORTED.REDIS)
    ServiceClients.init_services()
    return app


def config_logger(logger):
    logger.setLevel(logging.DEBUG)
