#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
from sanic import Blueprint
import sanic.response as response
from session.session import Session

BP = Blueprint(__name__, url_prefix="/desktop")

@BP.post("/<session_id>")
async def desktop_login(request, session_id):
	session = Session.get(session_id)
	if ((None == session) or (not session.good())):
		return response.redirect('/')
	sn = json.loads(session.decrypt(request.json["sn"]))
	if session.check(sn["token"], sn["number"]):
		session.renew()
		return response.empty()
	else:
		return response.empty(status = 403)

@BP.post("/<session_id>/logout")
async def desktop_logout(request, session_id):
	session = Session.get(session_id)
	if ((None != session) and session.good()):
		sn = json.loads(session.decrypt(request.json["sn"]))
		if session.check(sn["token"], sn["number"]):
			session.logout()
			return response.redirect('/')
	return response.empty(status = 403)
