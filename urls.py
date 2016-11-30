# coding=utf-8
import os
from tornado.web import url, StaticFileHandler
from constance import BASE_DIR
from handlers.handlers import *

urls = [
    # 生成图片验证码
    url(r'/api/imageCode', ImageCode, name='ImageCode'),
    # 发送短信验证码
    url(r'/api/sendMsg', SendMsg, name='SendMsg'),
    # 短信验证和密码验证
    url(r'/api/registe', Registe, name='Registe'),
    # 登录模块
    url(r'/api/login', Login, name='Login'),
    # 验证是否登录
    url(r'/api/check_login', check_login, name='check_login'),
    # 登出账号
    url(r'/api/logout', Logout, name='Logout'),
    # 获取用户中心的个人信息
    url(r'/api/profile', Profile, name='Profile'),
    # 上传个人头像
    url(r'/api/profile/avatar', Avatar, name='Avatar'),
    # 修改个人姓名
    url(r'/api/profile/name', SetName, name='SetName'),
    # 设置用户真实姓名
    url(r'/api/profile/auth', Auth, name='Auth'),
    # 获取所有地区
    url(r'/api/areas', Areas, name='Areas'),
    # 向服务器发送房屋基本信息和详细信息
    url(r'/api/house', House, name='House'),
    # 上传房屋的照片
    url(r'/api/house/image', HouseImage, name='HouseImage'),
    # 获取用户的所有图片
    url(r'/api/house/myhouse', MyHouse, name='MyHouse'),
    # 获取前五个最新发布的房源
    url(r'/api/house/latest', LatestHouse, name='LatestHouse'),
    # 主页
    url(r'/(.*)', StaticFileHandler,
        {'path': os.path.join(BASE_DIR, 'html'), 'default_filename': 'index.html'}),
]
