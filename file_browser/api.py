#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from session.session import Session
from sanic.log import logger
from sanic import Blueprint
import sanic.response as response
import pyinotify
import asyncio
import shutil
import json
import time
import os

BP = Blueprint(__name__, url_prefix="/dir")
root_dir = '/'

def get_root_dir():
	global root_dir
	return root_dir

def set_root_dir(path):
	global root_dir
	root_dir = os.path.abspath(path)
	logger.info(__name__ + " ROOT DIR: " + root_dir)

class DirObserver:
	mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO
	ERRNO_out_of_scope = -1
	ERRNO_json_decode = -2

	class EventHandler(pyinotify.ProcessEvent):
		def __init__(self, observer):
			self.ob = observer

		def process_IN_CREATE(self, event):
			asyncio.run(self.ob.send(self.ob.ls()))
			logger.debug(__name__ + " ADD[E]: " + event.pathname)

		def process_IN_DELETE(self, event):
			asyncio.run(self.ob.send(self.ob.ls()))
			logger.debug(__name__ + " RM[E]: " + event.pathname)

		def process_IN_MOVED_TO(self, event):
			asyncio.run(self.ob.send(self.ob.ls()))
			logger.debug(__name__ + " MV[E]: " + event.pathname)

	def __init__(self, ws, pwd, session_id):
		self.session = Session.get(session_id)
		self.ws = ws
		self.hd = DirObserver.EventHandler(self)
		self.wm = pyinotify.WatchManager()
		self.nf = pyinotify.ThreadedNotifier(self.wm, self.hd)
		self.nf.daemon = True
		self.pwd = pwd
		self.nf.start()
		self.wm.add_watch(self.pwd, DirObserver.mask, rec = False)

	def __del__(self):
		self.nf.stop()
		del self.nf
		del self.wm
		del self.hd

	def good():
		return ((None != self.session) and self.session.good())

	def send(self, msg):
		if None != self.session:
			self.ws.wend(self.session.encrypt(msg))

	def file_size(self, byte):
		KB = byte / 1024
		if KB < 1:
			return str(byte)

		MB = KB / 1024
		if MB < 1:
			return str(round(KB, 1)) + 'K'

		GB = MB / 1024
		if GB < 1:
			return str(round(MB, 1)) + 'M'
		else:
			return str(round(GB, 1)) + 'G'

	def json_response(self, ok, op, msg = None, en = 0):
		ret = {
			'ret' : ok,
			'op' : op,
			'errno' : en,
			'msg' : msg
		}
		logger.debug(__name__  + " RESP : " + json.dumps(ret))
		return json.dumps(ret)

	def cp(self, path_org, path_new, force):
		if os.path.isdir(path):
			shutil.copytree(path_org, path_new)
		else:
			pass

	def mv(self, path_org, path_new):
		os.rename(path_org, path_new)
		logger.debug(__name__ + " MV: " + path_org + "," + path_new)

	def md(self, name):
		path = os.path.abspath(self.pwd + '/' + name)
		os.mkdir(path)
		logger.debug(__name__ + " MD: " + path)

	def dl(self, name):
		pass
		return self.json_response(True, 'dl', None)

	def op(self, name):
		path = os.path.abspath(self.pwd + '/' + name)
		if os.path.isdir(path):
			return self.cd(path)
		else:
			pass
			return self.json_response(True, 'op', None)

	def cd(self, path):
		if get_root_dir() in path:
			wd = self.wm.get_wd(self.pwd)
			self.pwd = path
			self.wm.rm_watch(wd)
			self.wm.add_watch(self.pwd, DirObserver.mask, rec = False)
			logger.debug(__name__ + " CD: " + path)
			return self.ls()
		else:
			return self.json_response(False, 'cd', 'Switch directory beyond the scope of the root path', DirObserver.ERRNO_out_of_scope)

	def rm(self, name):
		path = os.path.abspath(self.pwd + '/' + name)
		if os.path.isdir(path):
			os.removedirs(path)
		else:
			os.remove(path)
		logger.debug(__name__ + " RM: " + path)

	def ls(self):
		data = []
		for n in os.listdir(self.pwd):
			f = os.path.abspath(self.pwd + '/' + n)
			data.append({
				'name' : n,
				'path' : f,
				'size' : self.file_size(os.path.getsize(f)),
				'ctime' : time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(f))),
				'islink' : os.path.islink(f),
				'isdir' : os.path.isdir(f)
			})

		return self.json_response(True, 'ls', data)

	async def serve(self):
		if not self.good():
			return
		await self.send(ob.ls())
		while self.session.good():
			try:
				data = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
				logger.debug(__name__ + " Received: " + data)
				if not data.strip():
					continue

				try:
					cmd = json.loads(data)
				except json.decoder.JSONDecodeError:
					continue

				sn = self.session.decrypt(cmd['sn'])
				if not session.check(sn["token"], sn["number"]):
					continue

				op = self.session.decrypt(cmd['args'][0])
				if 'ls' == op:
					await self.send(ob.ls())
				elif 'op' == op:
					await self.send(ob.op(self.session.decrypt(cmd['args'][1])))
				elif 'dl' == op:
					await self.send(ob.dl(self.session.decrypt(cmd['args'][1])))
				elif 'rm' == op:
					ob.rm(self.session.decrypt(cmd['args'][1]))
				elif 'md' == op:
					ob.md(self.session.decrypt(cmd['args'][1]))
				elif 'mv' == op:
					ob.mv(self.session.decrypt(cmd['args'][1]), self.session.decrypt(cmd['args'][2]))
				elif 'cp' == op:
					ob.cp(self.session.decrypt(cmd['args'][1]), self.session.decrypt(cmd['args'][2]))
				elif 'xx' == op:
					break

			except asyncio.TimeoutError:
				continue
			except Exception as e:
				logger.debug(ob.json_response(False, op, str(e), e.errno))
				continue

'''
request: {
	"sn" : ..
	"args" : [..]
}

args[0] : ls, rm, mv, md(mkdir), op(open), dl(download), cp, cpf
'''
@BP.websocket("/<session_id>")
async def browse_handle(request, ws, session_id):
	ob = DirObserver(ws, root_dir, session_id)
	ob.serve()
	del ob

@BP.post("/<session_id>/op/<cmd_id>")
async def open_handle(request):
	pass

@BP.post("/<session_id>/dl/<cmd_id>")
async def download_handle(request):
	pass
