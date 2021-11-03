#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import time
import json
import random
import string
from threading import Timer
from sanic import Blueprint
import sanic.response as response
from enc.aes_cbc_pkcs7 import AesCBCPkcs7
from enc.rsa_oaep import RsaOAEP
from db.account_db import AccountDB
from Crypto.Hash import SHA256 as PASSWD_HASH

BP = Blueprint(__name__, url_prefix="/login")

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
		self.kok = None
		db_kok = Session.db.kok(self.account)
		if None != db_kok:
			self.rsa_key = RsaOAEP()
			self.kok = PASSWD_HASH.new(str(db_kok + self.id).encode('utf-8')).hexdigest()
			Session.active[self.id] = self
			self.bomb_planted()

	def key(self):
		if None == self.aes_key:
			self.aes_key = Session.random_string(16)
		return self.aes_key

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
		del Session.active[self.id]
		del self

	def renew(self, idle = RENEW_IDLE):
		if self.effective():
			self.detonate = False
			self.idle = idle

@BP.post("/")
async def pubkey_handle(request):
	session = Session(request.json["account"])
	if not session.effective():
		return response.empty(status = 403)

	key = AesCBCPkcs7(session.kok).encrypt(json.dumps({
		"n": session.rsa_key.n(),
		"e": session.rsa_key.e()
	}))

	ret = {
		"k": key,
		"s": session.rsa_key.sign(key),
		"i": session.id
	}

	return response.json(ret)

@BP.post("/<session_id>")
async def session_handle(request, session_id):
	session = Session.get(session_id)
	if (None != session) and (None == session.aes_key):
		auth = json.loads(session.rsa_key.decrypt(request.json["auth"]))
		passwd_hash = PASSWD_HASH.new(auth["passwd"].encode('utf-8')).hexdigest()
		if session.db.verify_password(session.account, passwd_hash):
			session.renew()
			ret_key = AesCBCPkcs7(auth["key"]).encrypt(session.key())
			return response.json({
				'k': ret_key,
				's': session.rsa_key.sign(ret_key)
			})

	return response.empty(status = 403)
