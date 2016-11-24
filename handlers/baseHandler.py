# coding=utf-8
from tornado.web import RequestHandler, StaticFileHandler
import json


class baseHandler(RequestHandler):

    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    def initialize(self):
        pass

    def prepare(self):
        self.xsrf_token
        if self.request.headers.get('Content-Type', '').startswith('application/json'):
            self.json_args = json.loads(self.request.body)
        else:
            self.json_args = None

    def set_default_headers(self):
        pass

    def write_error(self, status_code, **kwargs):
        pass

    def get(self):
        pass

    def post(self):
        pass

    def current_user(self):
        pass

    def on_finish(self):
        pass

    def get_current_user(self):
        pass


class StaticFileHandler(StaticFileHandler):
    def __init__(self, *args, **kwargs):
        super(StaticFileHandler, self).__init__(*args, **kwargs)
        self.xsrf_token
