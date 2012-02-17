# source code adopted from https://github.com/alek-sys/ChangeTracker
import difflib
import functools
import os
import sublime
import sublime_plugin
import json
import socket
from sublime import Region
from threading import Thread


# composes "swank" JSON to be sent to the cccp agent
class JsonComposer:
	def __init__(self):
		self.host = 'localhost'
		self.port = int(open('/Users/tschmorleiz/Projects/101/cccp/agent/dist/cccp.port', 'r').read())
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connected = False
		#if not self.connected:
		#	self.s.connect((self.host, self.port)) 
		#	self.connected = True
		self.filename = ""
		self.callid = 0

	def callId(self):
		self.callid = self.callid + 1      
		return self.callid
	

	def rpcSend(self, msg, wait):
		hexed = "0000" + hex(len(msg))[2:]
		toSend = hexed + msg
		print "Sending: " + toSend 
		#self.s.send(toSend)
		#if wait:
		#	data = self.s.recv(1024)
		#	print 'Received', repr(data)
		self.s.close()
		return True

	def initConnectionJson(self):
		cid = self.callId()
		print cid
		return ({"swank":"init-connection", "args":[{"protocol": "http", "host": "slowb127.uni-koblenz.de", "port" : 8585}], "callId" : self.callId()})

	def linkFileJson(self):
		return ({"swank":"link-file", "args":[{"id": "id", "file-name": self.filename }], "callId" : self.callId()})

	def unlinkFileJson(self):
		return ({"swank":"unlink-file", "args":[{ "file-name": self.filename }], "callId" : self.callId()})

	def editFileJson(self, op, pos, s):
		return ({"swank": "edit-file", "file-name": self.filename, "args":[{"retain": pos}, { op: s}], "callId" : self.callId()})



class TrackChangesCore:  

	def __init__(self):
		self.savePoint = False
		self.oldText = ""
		self.jsonComposer = JsonComposer()
		self.jsonComposer.rpcSend(json.dumps(self.jsonComposer.initConnectionJson()), False)

		 
	def get_diff(self, s1, s2):
		s = difflib.SequenceMatcher(None, s1, s2)
		unchanged = [(m[1], m[1] + m[2]) for m in s.get_matching_blocks()]
		diffs = []
		prev = unchanged[0]
		for u in unchanged[1:]:
				diffs.append((prev[1], u[0]))
				prev = u
		return diffs

	def processDiffs(self, view, diffs, currentText):
		print "got some diffs. Sending"
		for d in diffs:
			if d[0] != d[1]:
				self.jsonComposer.rpcSend(json.dumps(self.jsonComposer.editFileJson("insert", d[0], view.substr(Region(d[0],d[1])))), True)	
		self.oldText = currentText;		
			  

	def track_sync(self, view, currentText, filename):
		try:
			with open(filename, "rU") as f:
				originalText = f.read().decode('utf8') 
			if not self.savePoint:
				self.jsonComposer.filename = filename
				self.oldText = originalText
				self.savePoint = True
			diffs = self.get_diff(self.oldText, currentText)
			# execute diff processing
			sublime.set_timeout(functools.partial(self.processDiffs, view, diffs, currentText),1)
		except:
			pass

	def track(self, view):
		print "foo"
		currentText = view.substr(Region(0, view.size()))
		filename = view.file_name()
		self.diff_thread = Thread(target=self.track_sync, args=(view, currentText, filename))
		self.diff_thread.start()

class TrackChangesWhenTypingListener(sublime_plugin.EventListener):
	def __init__(self):
		self.timer = None
		self.pending = True
		self.jsonComposer = JsonComposer()
		self.trackChangesCore = TrackChangesCore()
				   
	def handle_timeout(self, view):
		self.on_idle(view)

	def on_idle(self, view): 
		print ""
  
	def on_modified(self, view):
		self.trackChangesCore.track(view)

	def on_post_save(self, view):
		if self.pending:
			self.jsonComposer.filename = view.file_name()
			self.jsonComposer.rpcSend(json.dumps(self.jsonComposer.linkFileJson()), False)
			self.pending = False