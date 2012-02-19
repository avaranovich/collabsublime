import difflib
import functools
import os
import json
import socket, asyncore
from threading import Thread
from AgentClient import AgentClient
from JsonComposer import JsonComposer

def itsdone(result):
  print "Done! result=%r" % (result)

def afterInit(agentClient):
	print "got initialized agentClient!"
	jsonComposer = JsonComposer()
	jsonComposer.filename = "foo.txt"
	agentClient.sendCommand(json.dumps(jsonComposer.linkFileJson()))

def listen():
	port = int(open('../cccp/agent/dist/cccp.port', 'r').read())
	client = AgentClient("localhost", port, afterInit)
	asyncore.loop()

clientThread = Thread(target=listen)
clientThread.start()

#client.sendRpc(data, callback=itsdone)

x = raw_input("please type OK to exit: ")
exit(0)

