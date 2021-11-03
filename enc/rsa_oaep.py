#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from Crypto.Signature import pss as SIGN
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA1 as SIGN_HASH
import Crypto
import base64

class RsaOAEP:
	def __init__(self, bits:int = 2048, public_key_pem_file:str = None, private_key_pem_file:str = None):
		if None != private_key_pem_file:
			self.private_key = RSA.import_key(open(private_key_pem_file).read())
		else:
			self.private_key = RSA.generate(bits)
			self.public_key = self.private_key.publickey()

		if None != public_key_pem_file:
			self.public_key = RSA.import_key(open(public_key_pem_file).read())

	def n(self):
		return str(hex(self.public_key.n))[2:]

	def e(self):
		return self.public_key.e

	def encrypt(self, plaintext):
		ret = ''.encode('utf-8')
		try:
			cipher = PKCS1_OAEP.new(self.public_key)
			max_len = int(Crypto.Util.number.size(self.public_key.n) / 8 - 11)
			while plaintext:
				snippet = plaintext[:max_len].encode('utf-8')
				plaintext = plaintext[max_len:]
				ret += cipher.encrypt(snippet)
		except:
			return None
		else:
			return base64.b64encode(ret).decode('utf-8')

	def decrypt(self, base64_ciphertext):
		ret = ''.encode('utf-8')
		try:
			cipher = PKCS1_OAEP.new(self.private_key)
			max_len = int(Crypto.Util.number.size(self.private_key.n) / 8)
			ciphertext = base64.b64decode(base64_ciphertext)
			while ciphertext:
				snippet = ciphertext[:max_len]
				ciphertext = ciphertext[max_len:]
				ret += cipher.decrypt(snippet)
		except:
			return None
		else:
			return ret.decode('utf-8')

	def sign(self, data):
		signature = ''
		try:
			signature = SIGN.new(self.private_key).sign(SIGN_HASH.new(data.encode('utf-8')))
		except:
			return None
		else:
			return base64.b64encode(signature).decode('utf-8')

	def verify(self, data, base64_signature):
		try:
			SIGN.new(self.public_key).verify(SIGN_HASH.new(data.encode('utf-8')), base64.b64decode(base64_signature))
		except:
			return False
		else:
			return True
