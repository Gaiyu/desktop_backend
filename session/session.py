#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import random
import string
from threading import Timer
from enc.rsa_oaep import RsaOAEP
from db.account_db import AccountDB
from Crypto.Hash import SHA256 as PASSWD_HASH
from enc.aes_cbc_pkcs7 import AesCBCPkcs7

class Session:
	KOK_IDLE = 10
	RENEW_IDLE = 600
	active = {}
	db = AccountDB()

	@classmethod
	def random_string(cls, num):
		return ''.join(random.sample(string.ascii_letters + string.digits, num))

	@classmethod
	def get(cls, session_id):
		return Session.active.get(session_id, None)

	def __init__(self, account, idle = KOK_IDLE):
		self.idle = idle
		self.detonate = True
		self.id = Session.random_string(16)
		self.account = account
		self.rsa_key = None
		self.aes_key = None
		self.aes_passwd = None
		self.kok = None
		self.token = Session.random_string(32)
		self.sn = 0
		db_kok = Session.db.kok(self.account)
		if None != db_kok:
			self.rsa_key = RsaOAEP()
			self.kok = PASSWD_HASH.new(str(db_kok + self.id).encode('utf-8')).hexdigest()
			Session.active[self.id] = self
			self.bomb_planted()

	def good(self):
		return ((None != self.rsa_key) and (None != self.aes_key))

	def effective(self):
		return None != self.kok

	def bomb_planted(self):
		if not self.effective():
			return
		self.bomb = Timer(self.idle, self.explode)
		self.bomb.start()

	def explode(self):
		if not self.detonate:
			self.detonate = True
			self.bomb_planted()
			return
		self.logout()

	def check(self, token, sn):
		if ((token == self.token) and (sn > self.sn)):
			self.sn = sn
			return True
		return False

	def renew(self, idle = RENEW_IDLE):
		if self.effective():
			self.detonate = False
			self.idle = idle

	def encrypt(self, text):
		if None != self.aes_key:
			return self.aes_key.encrypt(text)
		return None

	def decrypt(self, text):
		if None != self.aes_key:
			return self.aes_key.decrypt(text)
		return None
		
	def logined(self):
		return None != self.aes_passwd

	def login(self):
		if None == self.aes_passwd:
			self.aes_passwd = Session.random_string(32)
			self.aes_key = AesCBCPkcs7(self.aes_passwd)
		return self.aes_passwd

	def logout(self):
		del Session.active[self.id]
		del self
