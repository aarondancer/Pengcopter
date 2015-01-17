#!/usr/bin/env python

import liblo, sys

try:
    server = liblo.Server(5001)
except liblo.ServerError, err:
    print str(err)
    sys.exit()

def concentration_callback(path, args):
    print (sum(args) / float(len(args)))

def acc_callback(path, args):
	print (sum(args) / float(len(args)))

server.add_method("/muse/elements/experimental/concentration", 'f', concentration_callback)
server.add_method("/muse/acc", 'fff', acc_callback)

# loop and dispatch messages every 100ms
while True:
    server.recv(1000)
