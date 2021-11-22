#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import getopt
from sanic import Sanic
from sanic.response import empty
import static.static_server as StaticServer
import file_browser.file_browser as FileBrowser
import session.login as Login
import desktop.api as Desktop

app = Sanic(__name__)

#@app.exception(Exception)
#async def ignore_exceptions(request, exception):
	#return empty(status = 403)

def help():
	print(__file__ + ' -d <初始NAS共享根目录> -w <前端页面dist目录>')
	sys.exit()

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hDd:w:")
	except getopt.GetoptError:
		help()

	debug = False
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			help()
		elif opt in ('-d'):
			FileBrowser.set_root_dir(arg)
		elif opt in ('-w'):
			StaticServer.set_root_dir(arg)
		elif opt in ('-D'):
			debug = True

	app.blueprint(StaticServer.BP)
	app.blueprint(FileBrowser.BP)
	app.blueprint(Login.BP)
	app.blueprint(Desktop.BP)
	app.run(debug = debug, access_log = debug, host="0.0.0.0", port=8000)

if __name__ == "__main__":
	main(sys.argv[1:])
