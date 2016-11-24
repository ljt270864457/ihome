#coding=utf-8

import sys
sys.path.append('..')
from uuid import uuid4
import logging
import config
from response_code import RET
import json
from constance import *

class Session(object):
	'''
	session格式：data是序列化之后的数据
	'sess_session_id':data


	cookie格式：
	'session_id':session中的key
	'''
	def __init__(self,request_handler):
		self.request_handler = request_handler
		# seesion的键是cookie中的值
		self.session_id = self.request_handler.request.get_secure_cookie('session_id')
		if not session_id:
			self.session_id = uuid4().hex
			self.data = {}
		else:
			try:
				ret = self.redis.get('sess_%s'%self.session_id)
			except Exception as e:
				logging.error(e)
				self.data = {}
			if not ret:
				self.data = {}
			else:
				self.data = json.loads(ret)

	'''
	1.存储session
	2.设置cookie
	'''
	def save(self):
		json_data = json.dumps(self.data)
		try:
			self.redis.setnx('sess_%s'%self.session_id,SESSION_EXPIRE_SECONDS,json_data)
		except Exception as e:
			logging.error(e)
		else:
			self.request_handler.request.set_secure_cookie('session_id','sess_%s'%self.session_id)

	''' 
	1.删除cookie
	2.删除session
	'''
	def clear(self):
		self.request_handler.request.clear_cookie('session_id')
		try:
			self.redis.delete('sess_%s'%self.session_id)
		except Exception as e:
			logging.error(e)
