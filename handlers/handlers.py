# encoding=utf-8
import sys
import logging
sys.path.append('..')
from utils.captcha.captcha import captcha
from baseHandler import baseHandler
from utils.toolKit import *
from constance import IMG_EXPIRE_SECONDS, SMS_EXPIRE_SECONDS
from response_code import RET
import json
import random
import hashlib
from libs.yuntongxun.CCP import ccp

# 主页


class IndexHandler(baseHandler):
    def get(self):
        urls = dict(login_url=self.reverse_url('LoginHandler'),
                    registe_url=self.reverse_url('RegisteHandler')
                    )
        self.render('index.html', **urls)


# 注册页
class RegisteHandler(baseHandler):
    def get(self):
        self.render('register.html')


# 登录页
class LoginHandler(baseHandler):
    def get(self):
        self.render('login.html')


class ImageCode(baseHandler):
    def get(self):
        preCode = self.get_argument('pcode', '')
        curCode = self.get_argument('ccode', '')
        if preCode:
            try:
                self.redis.delete('image_code_%s' % preCode)
            except Exception as e:
                logging.error(e)

        # name 图片验证码名称
        # text 图片验证码文本
        # image 图片验证码二进制数据
        name, text, image = captcha.generate_captcha()
        try:
            self.redis.setex('image_code_%s' %
                             curCode, IMG_EXPIRE_SECONDS, text)
        except Exception as e:
            logging.error(e)
            self.write('')
        else:
            self.set_header('Content-Type', 'img/jpg')
            self.write(image)


class SendMsg(baseHandler):
    def post(self):
        """
         1.判断三个参数是否齐全
         2.对比验证码与redis中存储的是否一致，不一致，返回错误信息
         3.如果一致,生成随机数
         4.将随机数存储到redis中
         5.将数据发送给用户
            info = {
            # 手机号
            "mobile":mobile,
            # 验证码
            'imageCode':imageCode,
            # 图片的ID
            'codeId':imageCodeId
        }
        """
        mobile = self.json_args.get("mobile")
        imageCode = self.json_args.get("imageCode")
        codeId = self.json_args.get("codeId")

        # 参数完整性验证
        if not all((mobile, imageCode, codeId)):
            return self.write(dict(errorno=RET.PARAMERR, errmsg=u'参数不完整'))
        # 手机号相关验证
        if not ReTools.isPhoneNum(mobile):
            return self.write(dict(errorno=RET.PARAMERR, errmsg=u'请输入正确的手机号'))
        # 验证手机号是否存在
        else:
            sql = "select  up_mobile from ih_user_profile where up_mobile=%s"
            try:
                ret = self.db.get(sql, mobile)
            except Exception as e:
                return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
            else:
                if ret:
                    return self.write(dict(errorno=RET.DATAEXIST, errmsg=u'手机号已被注册'))

        # 判断图片验证码
        code = 'image_code_%s' % codeId
        try:
            redis_imgcode = self.redis.get(code)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errorno=RET.DBERR, errmsg=u'Redis数据库查询错误'))
        else:
            if not redis_imgcode:
                return self.write(dict(errorno=RET.NODATA, errmsg=u'没有查询到的数据'))
            if imageCode.lower() != redis_imgcode.lower():
                return self.write(dict(errorno=RET.DATAERR, errmsg=u'验证码匹配错误'))

        # 设置短信验证码
        note = "%04d" % random.randint(0, 9999)
        try:
            self.redis.setex('sms_code_%s' % mobile, SMS_EXPIRE_SECONDS, note)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库有误'))
        else:
            ccp.sendTemplateSMS(mobile, [note, SMS_EXPIRE_SECONDS / 60], 1)
            return self.write(dict(errorno=RET.OK, errmsg=u'OK'))


class Registe(baseHandler):
    '''
    1.接收用户发来的短信验证码、密码、重复密码
    2.验证短信验证码与redis中的验证码是否一致
    3.验证两次密码是否一致
    4.对密码进行sha1加密
    4.如果都一致，将用户信息存入到MySQL
    5.跳转到登录页

    info={
            "mobile":mobile,
            "phoneCode":phoneCode,
            "passwd":passwd,
            "passwd2":passwd2
        }
    '''

    def post(self):
        mobile = self.json_args.get('mobile')
        phoneCode = self.json_args.get('phoneCode')
        passwd = self.json_args.get('passwd')
        passwd2 = self.json_args.get('passwd2')
        if not all((mobile, phoneCode, passwd, passwd2)):
            return self.write(dict(errorno=RET.PARAMERR, errmsg=u'参数不完整'))
        try:
            real_sms = self.redis.get('sms_code_%s' % mobile)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errorno=RET.DBERR, errmsg=u'Redis数据库查询错误'))
        else:
            if not real_sms:
                return self.write(dict(errorno=RET.NODATA, errmsg=u'没有查询到的数据'))
            if real_sms != phoneCode:
                return self.write(dict(errorno=RET.DATAERR, errmsg=u'验证码匹配错误'))
            if passwd != passwd2:
                return self.write(dict(errorno=RET.PARAMERR, errmsg=u'两次输入的密码不一致'))
            else:
                passwd = hashlib.sha1(passwd).hexdigest()
                sql = "insert into ih_user_profile(up_name,up_mobile,up_passwd,up_admin) values(%(name)s,%(mobile)s,%(passwd)s,%(admin)s)"
                try:
                    ret = self.db.execute(
                        sql, name=mobile, mobile=mobile, passwd=passwd, admin=0)
                except Exception as e:
                    logging.error(e)
                    return self.write(dict(errorno=RET.DBERR, errmsg=u'MySQL数据库查询错误'))
                else:
                    if not ret:
                        return self.write(dict(errorno=RET.DBERR, errmsg=u'MySQL数据库插入失败'))
                    else:
                        self.write(dict(errorno=RET.OK, errmsg=u'/login'))


class Login(baseHandler):
    def post(self):
        '''
        1.获取手机号和密码
        2.验证参数完整性
        3.与数据库中的账号密码进行比对
        4.如果无误，跳转到主页
        info = {
            "mobile": mobile,
            "passwd": passwd,
        };
        '''
        mobile = self.json_args.get('mobile')
        passwd = self.json_args.get('passwd')
        if not all((mobile, passwd)):
            return self.write(dict(errorno=RET.PARAMERR, errmsg=u'请输入完整的信息'))
        passwd = hashlib.sha1(passwd).hexdigest()
        sql = 'select up_passwd from ih_user_profile where up_mobile = %(mobile)s'
        try:
            ret = self.db.get(sql, mobile=mobile)
        except Exception as e:
            logging.login(e)
            return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
        else:
            if not ret:
                return self.write(dict(errorno=RET.NODATA, errmsg=u'没有查询到数据'))
            else:
                real_passwd = ret.get('up_passwd')
            if passwd != real_passwd:
                return self.write(dict(errorno=RET.PWDERR, errmsg=u'密码错误'))
            else:
                self.write(dict(errorno=RET.OK, errmsg=u'/'))
                # self.redirect('/')

if __name__ == '__main__':
    print dir(Login)
