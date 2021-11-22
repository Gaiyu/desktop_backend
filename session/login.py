#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
from sanic import Blueprint
import sanic.response as response
from enc.aes_cbc_pkcs7 import AesCBCPkcs7
from Crypto.Hash import SHA256 as PASSWD_HASH
from session.session import Session

BP = Blueprint(__name__, url_prefix="/login")

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
	if (None != session) and (not session.logined()):
		auth = json.loads(session.rsa_key.decrypt(request.json["auth"]))
		passwd_hash = PASSWD_HASH.new(auth["passwd"].encode('utf-8')).hexdigest()
		if session.db.verify_password(session.account, passwd_hash):
			session.renew()
			ret_key = AesCBCPkcs7(auth["key"]).encrypt(session.login())
			token = session.encrypt(session.token)
			return response.json({
				'k': ret_key,
				't': token,
				's': session.rsa_key.sign(ret_key)
			})

	return response.empty(status = 403)
