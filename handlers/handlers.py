# encoding=utf-8
import sys
import logging
sys.path.append('..')
import os
from utils.captcha.captcha import captcha
from baseHandler import baseHandler
from utils.toolKit import *
from constance import IMG_EXPIRE_SECONDS, SMS_EXPIRE_SECONDS, QN_DOMAIN,AREAS_EXPIRE_SECONDS,LATESTIMG_EXPIRE_SECONDS
from response_code import RET
import json
import random
import hashlib
from libs.yuntongxun.CCP import ccp
from utils.session import Session
from utils.deractor import required_login
from utils.saveImage import storage
import datetime


class ImageCode(baseHandler):
	'''
	url：/api/imageCode
	实现功能：生成图片验证码
	'''

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
	'''
	url：/api/sendMsg
	实现功能：发送短信验证码
	'''

	def post(self):
		"""
		 1.判断三个参数是否齐全
		 2.对比验证码与redis中存储的是否一致，不一致，返回错误信息
		 3.如果一致,生成随机数
		 4.将随机数存储到redis中
		 5.将数据发送给用户
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
	url:/api/registe
	实现功能：短信验证和密码验证
	'''

	def post(self):
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
				sql = "insert into ih_user_profile(up_name,up_mobile,up_passwd) values(%(name)s,%(mobile)s,%(passwd)s)"
				try:
					ret = self.db.execute(
						sql, name=mobile, mobile=mobile, passwd=passwd)
				except Exception as e:
					logging.error(e)
					return self.write(dict(errorno=RET.DBERR, errmsg=u'MySQL数据库查询错误'))
				else:
					if not ret:
						return self.write(dict(errorno=RET.DBERR, errmsg=u'MySQL数据库插入失败'))
					else:
						session = Session(self)
						session.data['user_id'] = ret
						session.data['user_name'] = mobile
						session.data['mobile'] = mobile
						session.save()
						self.write(dict(errorno=RET.OK, errmsg=u'OK'))


class Login(baseHandler):
	'''
	url:/api/login
	实现功能：登录
	'''

	def post(self):
		'''
		1.获取手机号和密码
		2.验证参数完整性
		3.与数据库中的账号密码进行比对
		4.如果无误，跳转到主页
		'''
		mobile = self.json_args.get('mobile')
		passwd = self.json_args.get('passwd')
		if not all((mobile, passwd)):
			return self.write(dict(errorno=RET.PARAMERR, errmsg=u'请输入完整的信息'))
		passwd = hashlib.sha1(passwd).hexdigest()
		sql = 'select up_user_id,up_name,up_passwd from ih_user_profile where up_mobile = %(mobile)s'
		try:
			ret = self.db.get(sql, mobile=mobile)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
		if not ret:
			return self.write(dict(errorno=RET.NODATA, errmsg=u'没有查询到数据'))
		else:
			real_passwd = ret.get('up_passwd')
		if passwd != real_passwd:
			return self.write(dict(errorno=RET.PWDERR, errmsg=u'密码错误'))
		else:
			session = Session(self)
			session.data['user_id'] = ret['up_user_id']
			session.data['user_name'] = ret['up_name']
			session.data['mobile'] = mobile
			session.save()
			self.write(dict(errorno=RET.OK, errmsg=u'OK'))


class check_login(baseHandler):
	'''
	url:/api/check_login
	实现功能：验证用户是否登录
	'''

	def get(self):
		'''
		调用get_current_user方法确定有没有登录

		'''
		ret = self.get_current_user()
		if not ret:
			return self.write(dict(errorno=RET.SESSIONERR, errmsg=u'用户没有登录'))
		else:
			userid = ret.get('user_id')
			sql = 'select up_name from ih_user_profile where up_user_id=%(id)s'
			try:
				query_result = self.db.get(sql, id=userid)
			except Exception as e:
				logging.error(e)
				return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
			else:
				userName = query_result.get('up_name')
				return self.write(dict(errorno=RET.OK, errmsg=u'OK', data=userName))


class Logout(baseHandler):
	'''
	url:/api/logout
	实现功能：删除用户的cookie和session
	'''
	@required_login
	def get(self):
		session = Session(self)
		session.clear()
		return self.write(dict(errorno=RET.OK, errmsg=u'已登出'))


class Profile(baseHandler):
	'''
	url:/api/profile
	实现功能：获取用户中心的个人信息
	'''

	@required_login
	def get(self):
		data = self.get_current_user()
		if not data:
			return self.write(dict(errorno=RET.SESSIONERR, errmsg=u'用户未登录'))
		else:
			user_id = data.get('user_id')
			sql = 'select up_name,up_mobile,up_avatar from ih_user_profile where up_user_id = %(user_id)s'
			try:
				query_data = self.db.get(sql, user_id=user_id)
			except Exception as e:
				return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
			if not query_data:
				return self.write(dict(errorno=RET.NODATA, errmsg=u'没有查询到数据'))
			else:
				userName = query_data.get('up_name')
				userMobile = query_data.get('up_mobile')
				avatar_url = query_data.get('up_avatar')
				if avatar_url:
					abs_img_url = os.path.join(QN_DOMAIN, avatar_url)
				else:
					abs_img_url = None
				return self.write(dict(errorno=RET.OK, errmsg=u'查询成功', name=userName, mobile=userMobile, img_url=abs_img_url))


class Avatar(baseHandler):
	'''
	url:/api/profile/avatar
	实现功能：上传头像
	'''
	@required_login
	def post(self):
		data = self.get_current_user()
		if not data:
			return self.write(dict(errorno=RET.SESSIONERR, errmsg=u'用户未登录'))
		else:
			mobile = data.get('mobile')
			files = self.request.files
			try:
				img_data = files['avatar'][0]['body']
				img_key = storage(img_data)
			except Exception as e:
				logging.error(e)
				return self.write(dict(errorno=RET.NODATA, errmsg=u'头像不能为空'))
			if not img_key:
				return self.write(dict(errorno=RET.IOERR, errmsg=u'文件上传错误'))
			else:
				absolute_url = os.path.join(QN_DOMAIN, img_key)
				sql = "update ih_user_profile set up_avatar = %(url)s where up_mobile=%(mobile)s"
				try:
					ret = self.db.execute(sql, url=img_key, mobile=mobile)
				except Exception as e:
					return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库更新错误'))
				else:
					return self.write(dict(errorno=RET.OK, errmsg=u'OK', img_url=absolute_url))


class SetName(baseHandler):
	'''
	url:/api/profile/name
	实现功能：修改昵称
	'''
	@required_login
	def post(self):
		'''
		1.修改mysql中的数据
		2.修改redis的数据
		'''

		user_id = self.get_current_user().get('user_id')
		mobile = self.get_current_user().get('mobile')
		userName = self.get_current_user().get('user_name')
		newName = self.json_args.get('name')
		# 判断用户名是否存在
		sql = 'select up_name from ih_user_profile where up_name=%(name)s'
		try:
			ret = self.db.get(sql, name=newName)
		except Exception as e:
			return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
		if ret:
			return self.write(dict(errorno=RET.DATAEXIST, errmsg=u'用户名已存在'))
		sql = "update ih_user_profile set up_name = %(name)s where up_user_id=%(userID)s"
		try:
			ret = self.db.execute(sql, name=newName, userID=user_id)
		except Exception as e:
			return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
		# 向redis中更新数据
		try:
			session = Session(self)
			session_id = 'sess_%s' % session.session_id

			json_data = json.dumps(
				dict(user_id=user_id, user_name=newName, mobile=mobile))
			self.redis.getset(session_id, json_data)
		except Exception as e:
			return self.write(dict(errorno=RET.DATAERR, errmsg=u'更新缓存失败'))
		else:
			return self.write(dict(errorno=RET.OK, errmsg='OK'))


# 设置用户真实姓名

class Auth(baseHandler):
	'''
	url:/api/profile/auth
	实现功能:
	1.get方式显示用户名
	2.post方式修改用户名
	3.如果验证成功之后，不能进行更改
	'''
	@required_login
	def get(self):
		userID = self.get_current_user().get('user_id')
		sql = "select up_real_name,up_id_card from ih_user_profile where up_user_id=%(userid)s"
		try:
			ret = self.db.get(sql, userid=userID)
		except Exception as e:
			return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
		if ret:
			real_name = ret.get('up_real_name')
			id_number = ret.get('up_id_card')
			id_number = id_number[0:4] + '*' * 10 + id_number[-4:]
			if not all((real_name, id_number)):
				return self.write(dict(errorno=RET.NODATA, errmsg=u'没有实名认证'))
			return self.write(dict(errorno=RET.OK, errmsg=u'OK', name=real_name, id_number=id_number))

	@required_login
	def post(self):
		userID = self.get_current_user().get('user_id')
		real_name = self.json_args.get('real_name')
		id_number = self.json_args.get('id_card')
		if not ReTools.isIDNumber(id_number):
			return self.write(dict(errorno=RET.PARAMERR, errmsg=u'身份证号码不正确'))
		if not all((real_name, id_number)):
			return self.write(dict(errorno=RET.PARAMERR, errmsg=u'身份证号码和真实姓名信息不完整'))
		sql = 'update ih_user_profile set up_real_name=%(name)s,up_id_card=%(id_number)s where up_user_id=%(userid)s '
		try:
			ret = self.db.execute(sql, name=real_name,
								  id_number=id_number, userid=userID)
		except Exception as e:
			return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
		return self.write(dict(errorno=RET.OK, errmsg=u'OK'))


class Areas(baseHandler):
	'''
	url:/api/areas
	实现功能:获取所有的城区名称
	'''

	def get(self): 
		try:
			areas = self.redis.get('area_info')
		except Exception as e:
			logging.error(e)
			return self.write(dict(errorno=RET.DBERR, errmsg=u'Redis数据库查询错误'))
		if areas:
			return self.write(dict(errorno=RET.OK, errmsg=u'OK', areas=json.loads(areas)))
		else:
			sql = 'SELECT ai_area_id,ai_name FROM ih_area_info;'
			try:
				datas = self.db.query(sql)
			except Exception as e:
				logging.error(e)
				return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
			else:
				areas = [{'id': data.get('ai_area_id'), 'area': data.get('ai_name')}
						 for data in datas]
				try:
					self.redis.setex('area_info',AREAS_EXPIRE_SECONDS,json.dumps(areas))
				except Exception as e:
					logging.error(e)
					return self.write(dict(errorno=RET.DBERR, errmsg=u'Redis数据库写入错误'))
				return self.write(dict(errorno=RET.OK, errmsg=u'OK', areas=areas))


class House(baseHandler):
	'''
	url:/api/house
	实现功能：向数据库中存储房屋基本信息和详细信息
	'''
	@required_login
	def post(self):
		userID = self.get_current_user().get('user_id')
		# 房屋标题
		title = self.json_args.get('title')
		# 每晚价格
		price = self.json_args.get('price')
		# 所在城区
		area_id = self.json_args.get('area_id')
		# 详细地址
		address = self.json_args.get('address')
		# 出租房间数目
		room_count = self.json_args.get('room_count')
		# 房屋面积
		acreage = self.json_args.get('acreage')
		# 户型描述
		unit = self.json_args.get('unit')
		# 房屋面积
		capacity = self.json_args.get('capacity')
		# 卧床配置
		beds = self.json_args.get('beds')
		# 押金数额
		deposit = self.json_args.get('deposit')
		# 最少入住天数
		min_days = self.json_args.get('min_days')
		# 最多入住天数
		max_days = self.json_args.get('max_days')
		# 配套设施
		facility = self.json_args.get('facility')
		if not all((userID,title,price,area_id,address,room_count,unit,capacity,beds,deposit,min_days,max_days,facility)):
			return self.write(dict(errorno=RET.PARAMERR,errmsg=u'参数不完整'))
		sql = 'insert into ih_house_info(hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count,hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days) values(%(userID)s,%(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s,%(unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s);'
		try:
			houseID = self.db.execute(sql,userID=userID,title=title,price=int(price)*100,area_id=area_id,address=address, room_count=room_count,acreage=acreage,unit=unit,capacity=capacity,beds=beds,deposit=int(deposit)*100,min_days=min_days,max_days=max_days)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
		else:
			facility_info=[(houseID,i)for i in facility]
			sql = "insert into ih_house_facility(hf_house_id,hf_facility_id) values(%s,%s)"
			try:
				query_data2 = self.db.executemany(sql,facility_info)
			except Exception as e:
				logging.error(e)
				sql1 = "delete from ih_house_facility where hf_house_id=%(houseID)s"
				sql2 = "delete from ih_house_info where hi_house_id=%(houseID)s"
				try:
					deletedata1 = self.db.execute_rowcount(sql,houseID=houseID)
					deletedata2 = self.db.execute_rowcount(sql,houseID=houseID)
				except Exception as e:
					logging.error(e)
					return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误,并且无法正常删除数据库'))
				else:
					return self.write(dict(errorno=RET.DBERR, errmsg=u'No data save'))
			if not query_data2:
				return self.write(dict(errorno=RET.DBERR, errmsg=u'数据插入失败'))
			else:				
				return self.write(dict(errorno=RET.OK, errmsg=u'OK',userID=userID,houseID=houseID))


class HouseImage(baseHandler):
	'''
	url:/api/house/image
	实现功能：把房屋图片路径存到数据库中，并将图片存入到七牛
	'''
	@required_login
	def post(self):
		try:
			userID = self.get_current_user().get('user_id')
			imgFile = self.request.files['house_image'][0]['body']
			houseID = self.get_argument('house_id')
			img_key = storage(imgFile)			
		except Exception as e:
			logging.error(e)
			return self.write(dict(errorno=RET.PARAMERR,errmsg=u'表单获取错误'))
		if not img_key:
			return self.write(dict(errorno=RET.IOERR, errmsg=u'文件上传错误'))		
		sql = "insert into ih_house_image(hi_house_id,hi_url) values(%(houseID)s,%(url)s);update ih_house_info set hi_index_image_url=%(urls)s where hi_house_id=%(houseIDs)s and hi_index_image_url is null;"
		try:
			ret = self.db.execute(sql, houseID=houseID, url=img_key,urls=img_key,houseIDs=houseID)
		except Exception as e:
			return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库更新错误'))
		else:
			absolute_url = os.path.join(QN_DOMAIN, img_key)
			sql = 'SELECT hi_house_id,hi_index_image_url,hi_title FROM ih_house_info order by hi_utime desc limit 5'
			try:
				ret = self.db.query(sql)
			except Exception as e:
				return self.write(dict(errorno=RET.DBERR, errmsg=u'数据库查询错误'))
			if not ret:
				return self.write(dict(errorno=RET.NODATA,errmsg=u'查询失败'))
			else:
				try:
					houses = [{'houseID':house.get('hi_house_id'),'title':house.get('hi_title'),'url':os.path.join(QN_DOMAIN,house.get('hi_index_image_url'))} for house in ret]
					self.redis.delete('LatestHouse')
					self.redis.setex('LatestHouse',LATESTIMG_EXPIRE_SECONDS,json.dumps(houses))
				except Exception as e:
					logging.error(e)
					return self.write(dict(errorno=RET.DBERR,errmsg=u'redis写入错误'))
				return self.write(dict(errorno=RET.OK, errmsg=u'OK', url=absolute_url))	


						
class MyHouse(baseHandler):
	'''
	url:/api/house/my
	实现功能：获取个人房屋基本信息
	info={
	
	}
	'''
	@required_login
	def get(self):
		info = []
		userID = self.get_current_user().get('user_id','')
		if userID:
			sql = 'select hi_house_id,hi_title,hi_price,hi_index_image_url,hi_ctime,ai_name  from ih_house_info  left join ih_area_info on hi_area_id=ai_area_id where hi_user_id=%s order by hi_ctime desc;'
			try:
				ret = self.db.query(sql,userID)
			except Exception as e:
				return self.write(dict(errorno = RET.DATAERR,errmsg=u'数据库查询错误'))			
			if not ret:
				return self.write(dict(errorno=RET.NODATA,errmsg=u'数据为空'))
			else:
				for data in ret:
					info.append(dict(
						houseID=data['hi_house_id'],
						title = data['hi_title'],
						price = int(data['hi_price']/100),
						url = os.path.join(QN_DOMAIN,data['hi_index_image_url']),
						ctime = (data['hi_ctime']+datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
						zone = data['ai_name']
						))
				return self.write(dict(errorno=RET.OK,errmsg='OK',info=info))

class LatestHouse(baseHandler):
	'''
	url: /api/house/latest
	实现功能：从缓存中加载前5条数据，如果不存在，那么就从mysql中查出前五条放到redis中
	'''
	def get(self):
		try:
			ret1 = self.redis.get('LatestHouse')
		except Exception as e:
			logging.error(e)
			return self.write(dict(errorno=RET.DATAERR,errmsg=u'redis操作有误'))
		if ret1:
			return self.write(dict(errorno=RET.OK,errmsg=u'OK',houses=json.loads(ret1)))
		else:
			sql = 'SELECT hi_house_id,hi_index_image_url,hi_title FROM ih_house_info order by hi_utime desc limit 5;'
			try:
				ret2 = self.db.query(sql)
			except Exception as e:
				logging.error(e)
				return self.write(dict(errorno=RET.DATAERR,errmsg=u'MySQL操作有误'))
			if not ret2:
				return self.write(dict(errorno=RET.NODATA,errmsg=u'No Data'))
			else:
				houses = [{'houseID':house.get('hi_house_id'),'title':house.get('hi_title'),'url':os.path.join(QN_DOMAIN,house.get('hi_index_image_url'))} for house in ret2]
				try:
					self.redis.setex('LatestHouse',LATESTIMG_EXPIRE_SECONDS,json.dumps(houses))
				except Exception as e:
					logging.error(e)
					return self.write(dict(errorno=RET.DATAERR,errmsg=u'写入redis有误'))
				return self.write(dict(errorno=RET.OK,errmsg=u'OK',houses=houses))




		



