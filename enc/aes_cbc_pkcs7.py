#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import base64
from Crypto.Cipher import AES

class AesCBCPkcs7:
	def __init__(self, passwd):
		sha256 = hashlib.sha256()
		sha256.update(bytes(passwd, encoding='utf-8'))
		key = sha256.hexdigest()
		self.key = key[0:32].encode('utf-8')
		self.iv = key[32:48].encode('utf-8')

	def pkcs7padding(self, text):
		bs = 16
		length = len(text)
		bytes_length = len(text.encode('utf-8'))
		padding_size = length if (bytes_length == length) else bytes_length
		padding = bs - padding_size % bs
		padding_text = chr(padding) * padding
		self.coding = chr(padding)
		return text + padding_text

	def encrypt(self, text):
		return base64.b64encode(AES.new(self.key, AES.MODE_CBC, self.iv).encrypt(self.pkcs7padding(text).encode('utf-8'))).decode('utf-8')

	def decrypt(self, text):
		return AES.new(self.key, AES.MODE_CBC, self.iv).decrypt(base64.b64decode(text)).decode('utf-8')
