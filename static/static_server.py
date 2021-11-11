#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import os
from sanic import Blueprint
from sanic.log import logger
from sanic.response import file

BP = Blueprint(__name__, url_prefix="/")
root_dir = '/app/dist/'

JS_DIR = '/js/'
IMG_DIR = '/img/'
CSS_DIR = '/css/'
FONTS_DIR = '/fonts/'
INDEX_HTML = '/index.html'
FAVICON = '/favicon.ico'

def get_root_dir():
	global root_dir
	return root_dir

def set_root_dir(path):
	global root_dir
	root_dir = os.path.abspath(path)
	logger.info(__name__ + " ROOT DIR: " + root_dir)
	BP.static(uri = '/js', file_or_directory = os.path.abspath(root_dir + JS_DIR))
	BP.static(uri = '/img', file_or_directory = os.path.abspath(root_dir + IMG_DIR))
	BP.static(uri = '/css', file_or_directory = os.path.abspath(root_dir + CSS_DIR))
	BP.static(uri = '/fonts', file_or_directory = os.path.abspath(root_dir + FONTS_DIR))
	BP.static(uri = '/', file_or_directory = os.path.abspath(root_dir + INDEX_HTML), name = '/')
	BP.static(uri = '/desktop', file_or_directory = os.path.abspath(root_dir + INDEX_HTML), name = '/desktop')
	BP.static(uri = '/favicon.ico', file_or_directory = os.path.abspath(root_dir + FAVICON), name = '/favicon.ico')
