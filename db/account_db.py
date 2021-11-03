#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sqlite3
from Crypto.Hash import SHA256 as PASSWD_HASH

class AccountDB():
	def __init__(self, path:str = 'nas.db'):
		self.conn = sqlite3.connect(path)
		self.cur = self.conn.cursor()
		self.setup()

	def __del__(self):
		self.cur.close()
		self.conn.close()

	def setup(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS accounts(
				account TEXT PRIMARY KEY NOT NULL UNIQUE,
				password TEXT NOT NULL,
				admin INTEGER DEFAULT 0
			); ''')
		self.new_account("admin", PASSWD_HASH.new("admin".encode('utf-8')).hexdigest(), True)

	def reset(self):
		self.cur.execute(''' drop table account; ''')
		self.setup()

	def new_account(self, account:str, password:str, admin:bool = False):
		is_admin = 1 if admin else 0
		data = [(account, password, is_admin)]
		self.cur.executemany(''' INSERT OR IGNORE INTO accounts VALUES (?,?,?); ''', data)
		self.conn.commit()

	def del_account(self, account:str):
		self.cur.execute(''' DELETE FROM accounts WHERE account = '%s'; ''' % account)
		self.conn.commit()

	def verify_password(self, account:str, password:str):
		self.cur.execute(''' SELECT password FROM accounts WHERE account = '%s'; ''' % account)
		ret = self.cur.fetchall()
		if len(ret) < 1:
			return False
		return ret[0][0] == password

	def update_account(self, account:str, password:str, new_password:str):
		if self.verify_password(account, password):
			self.cur.execute(''' UPDATE accounts SET password = '%s' WHERE account = '%s'; ''' % (new_password, account))
			self.conn.commit()
			return self.verify_password(account, new_password)
		return False

	def kok(self, account:str):
		self.cur.execute(''' SELECT password FROM accounts WHERE account = '%s'; ''' % account)
		ret = self.cur.fetchall()
		if len(ret) < 1:
			return None
		return PASSWD_HASH.new(ret[0][0][0:16].encode('utf-8')).hexdigest()

	def accounts(self):
		self.cur.execute(''' SELECT account, admin FROM accounts; ''')
		return self.cur.fetchall()
