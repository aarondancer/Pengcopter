#!/usr/bin/env python

from liblo import *
from math import sqrt
import sys, time

class PengServer(Server):

	def __init__(self):
		Server.__init__(self, 5001)

	global acc
	global clevel
	clevel = 0.0
	acc = 0.0

	def printAcc(self):
		print self.acc

	@make_method("/muse/elements/experimental/concentration", 'f')
	def concentration_callback(self, path, args):
		self.clevel = 1 - sqrt((sum(args) / float(len(args))))
		print  self.acc * self.clevel

	@make_method("/muse/acc", 'fff')
	def acc_callback(self, path, args):
		self.acc = args[0]

try:
	server = PengServer()
except ServerError, err:
	print str(err)
	sys.exit()

# loop and dispatch messages every 100ms
while True:
	server.recv(100)
	# time.sleep(0.01)