import difflib
import functools
import os
import json
import socket, asyncore
from threading import Thread
from AgentClient import *

def itsdone(result):
  print "Done! result=%r" % (result)

def afterInit(agentClient):
	print "got it!"

def listen():
	port = int(open('../cccp/agent/dist/cccp.port', 'r').read())
	client = AgentClient("localhost", port, afterInit)
	jsonComposer = JsonComposer()
	jsonComposer.filename = "foo.txt"
	client.sendCommand(json.dumps(jsonComposer.linkFileJson()))
	asyncore.loop()

clientThread = Thread(target=listen)
clientThread.start()

#client.sendRpc(data, callback=itsdone)

x = raw_input("please type OK to exit: ")
exit(0)

