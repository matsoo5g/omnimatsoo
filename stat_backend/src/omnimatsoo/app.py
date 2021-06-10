import logging
from flask import Flask, g
from omnimatsoo.handlers import collect_blueprint
from omnimatsoo.kvstorage import SUPPORTED, Client
from omnimatsoo.services import ServiceClients


def create_app():
    app = Flask(__name__)
    app.register_blueprint(collect_blueprint)
    config_logger(app.logger)
    Client.init(SUPPORTED.MEMORY)
    ServiceClients.init_services()
    return app


def config_logger(logger):
    logger.setLevel(logging.DEBUG)
