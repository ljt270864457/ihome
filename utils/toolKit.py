# coding=utf-8

import re


# 正则验证类
class ReTools(object):
    @classmethod
    def isUserName(cls, strName):
        if len(strName.strip()) < 5 or len(strName.strip()) > 20:
            flag = False
            return flag
        else:
            p = re.compile(r'^[a-zA-Z]\w*')
            result = re.match(strName)
            if not result:
                flag = False
                return flag
            else:
                flag = True
                return flag

    @classmethod
    def isPasswd(cls, strPasswd):
        if len(strName.strip()) < 8 or len(strName.strip()) > 20:
            flag = False
            return flag
        else:
            flag = True
            return flag

    @classmethod
    def isEmail(cls, strEmail):
        """1.长度6-18，
           2.邮件地址需由字母、数字或下划线组成
           3.首字母是英文
        """
        if len(strName.strip()) < 6 or len(strName.strip()) > 18:
            flag = False
            errorMsg = u'密码要在6-18位'
            return flag
        else:
            p = re.compile(r'^([a-zA-Z]+\w*)@(\w+.com)(.cn)?')
            result = re.match()

    @classmethod
    def isPhoneNum(cls, strPhoneNum):
        '''
        1.手机号必须是11位
        2.必须是1开头
        '''
        if len(strPhoneNum.strip()) != 11:
            flag = False
            return flag
        else:
            p = re.compile(r'^1[0-9]{10}')
            if p.match(strPhoneNum):
                flag = True
                return flag
            else:
                flag = False
                return flag


if __name__ == '__main__':
    msg = ReTools.isUserName('a1111a')
    print msg[1].encode('utf-8')
