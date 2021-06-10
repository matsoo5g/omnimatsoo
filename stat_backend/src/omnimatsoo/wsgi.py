import os

from tornado import httpserver, wsgi, ioloop
from tornado.netutil import bind_unix_socket

from omnimatsoo.app import create_app


def start():
    app = create_app()
    http_server = httpserver.HTTPServer(wsgi.WSGIContainer(app))
    if socket_path := os.environ.get("APP_SOCKET_PATH"):
        socket = bind_unix_socket(socket_path)
        http_server.add_socket(socket)
    else:
        port = os.environ.get("APP_PORT") or 5000
        http_server.listen(port=port, address="0.0.0.0")
    ioloop.IOLoop.current().start()
