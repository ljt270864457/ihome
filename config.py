# coding=utf-8
import os
import torndb

# 项目所在目录
base_dir = os.path.dirname(__file__)

# settings配置
SETTING = {
    'static_path': os.path.join(base_dir, 'static'),
    'template_path': os.path.join(base_dir, 'html'),
    'cookie_secret': '4RgAdrMqRQ6Y/K4Wzx5Aaar8zIdGaEHmpX5dFtm4l2c=',
    'xsrf_cookies': True,
    'login_url': '/login.html',
    'debug': True,
}


# MySQL设置
MySQL_CONFIG = dict(
    host="192.168.196.130",
    database="ihome",
    user="root",
    password="123456",
)

# Redis设置
REDIS_CONFIG = dict(
    host="192.168.196.130",
    port=6379
)

# log设置
LOG_PATH = os.path.join(base_dir, 'logs/log')
LOG_LEVEL = 'debug'
