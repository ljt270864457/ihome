# coding=utf-8
import os
from tornado.web import url, StaticFileHandler
from constance import BASE_DIR
from handlers.handlers import *

urls = [
    url(r'/', IndexHandler, name='IndexHandler'),
    url(r'/registe', RegisteHandler, name='RegisteHandler'),
    url(r'/login', LoginHandler, name='LoginHandler'),
    # 生成图片验证码
    url(r'/api/imageCode', ImageCode, name='ImageCode'),
    # 发送短信验证码
    url(r'/api/sendMsg', SendMsg, name='SendMsg'),
    # 短信验证和密码验证
    url(r'/api/registe', Registe, name='Registe'),
    # 登录模块
    url(r'/api/login', Login, name='Login'),
    url(r'/(.*)', StaticFileHandler,
        {'path': os.path.join(BASE_DIR, 'html'), 'default_filename': 'index.html'}),
]
