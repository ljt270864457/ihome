# coding=utf-8

from tornado.web import Application, url, RequestHandler
from tornado.options import define, options, parse_command_line
import tornado.ioloop
import tornado.httpserver
import torndb
import redis
from handlers.baseHandler import baseHandler
import config
from urls import urls
from utils.toolKit import ReTools


define("port", default=8000, type=int, help="端口号")


class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.db = torndb.Connection(**config.MySQL_CONFIG)
        self.redis = redis.StrictRedis(**config.REDIS_CONFIG)


def main():
    port = options.port
    # options.logging = config.LOG_LEVEL
    # options.log_file_prefix = config.LOG_PATH
    parse_command_line()
    app = Application(urls, **config.SETTING)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port)
    tornado.ioloop.IOLoop().current().start()

if __name__ == '__main__':
    main()
