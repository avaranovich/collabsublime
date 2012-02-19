import difflib
import functools
import os
import json
import socket, asyncore
from threading import Thread
from AgentClient import AgentClient


class JsonComposer:
	def __init__(self):
		self.host = 'localhost'
		self.port = int(open('../cccp/agent/dist/cccp.port', 'r').read())
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connected = False
		self.filename = ""
		self.callid = 0
    
	def callId(self):
		self.callid = self.callid + 1      
		return self.callid
	
   	def rpcSend(self, msg, wait):
		if not self.connected:
			self.s.connect((self.host, self.port)) 
			self.connected = True
		hexed = "0000" + hex(len(msg))[2:]
		toSend = hexed + msg
		print "Sendisng: " + toSend
		self.s.send(toSend)
		if wait:
			data = self.s.recv(1024)
			print 'Received', repr(data)
		return True
    
	def initConnectionJson(self):
		cid = self.callId()
		print cid
		return ({"swank":"init-connection", "args":[{"protocol": "http", "host": "localhost", "port" : 8585}], "callId" : self.callId()})
    
	def linkFileJson(self):
		return ({"swank":"link-file", "args":[{"id": "id", "file-name": self.filename }], "callId" : self.callId()})
    
	def unlinkFileJson(self):
		return ({"swank":"unlink-file", "args":[{ "file-name": self.filename }], "callId" : self.callId()})
    
	def editFileJson(self, op, pos, s):
		return ({"swank": "edit-file", "file-name": self.filename, "args":[{"retain": pos}, { op: s}], "callId" : self.callId()})

#old sync verion
#jc = JsonComposer()
#jc.filename = "foo.txt"
#print json.dumps(jc.initConnectionJson())
#jc.rpcSend(json.dumps(jc.initConnectionJson()), False)
#jc.rpcSend(json.dumps(jc.unlinkFileJson()), False)

def itsdone(result):
  print "Done! result=%r" % (result)

def afterInit(clientAgent):
	#here we have the initialized clientAgent
	print "afterInit! result=%r" % (result)	
  

def listen():
	port = int(open('../cccp/agent/dist/cccp.port', 'r').read())
	client = AgentClient("localhost", port, callback=afterInit)
	asyncore.loop()

clientThread = Thread(target=listen)
clientThread.start()

#client.sendRpc(data, callback=itsdone)

x = raw_input("please type OK to exit: ")
if(x == "OK"):
	exit(0)

