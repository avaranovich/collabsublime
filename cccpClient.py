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

# global registration for files to be under change tracking
GLOBAL_REG = {}

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

	# running id to help the agent
	def callId(self):
		self.callid = self.callid + 1      
		return self.callid
	
	# sends a JSON message over the socket
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

	# JSON for connection intialisation with the agent
	def initConnectionJson(self):
		cid = self.callId()
		print cid
		return ({"swank":"init-connection", "args":[{"protocol": "http", "host": "slowb127.uni-koblenz.de", "port" : 8585}], "callId" : self.callId()})

	# JSON for linking a file
	def linkFileJson(self):
		return ({"swank":"link-file", "args":[{"id": "id", "file-name": self.filename }], "callId" : self.callId()})

	# JSON for unlinking a file
	def unlinkFileJson(self):
		return ({"swank":"unlink-file", "args":[{ "file-name": self.filename }], "callId" : self.callId()})

	# JSON for reporting changes ("insert" or "delete")
	def editFileJson(self, op, pos, text):
		return ({"swank": "edit-file", "file-name": self.filename, "args":[{"retain": pos}, { op: text}], "callId" : self.callId()})



# Core class for change tracking
class TrackChangesCore:  
	def __init__(self):
		self.savePoint = False
		self.oldText = ""
		self.jsonComposer = JsonComposer()
		self.jsonComposer.rpcSend(json.dumps(self.jsonComposer.initConnectionJson()), False)

	# computes diffs between s1 and s2	 
	def get_diff(self, s1, s2):
		s = difflib.SequenceMatcher(None, s1, s2)
		unchanged = [(m[1], m[1] + m[2]) for m in s.get_matching_blocks()]
		diffs = []
		prev = unchanged[0]
		for u in unchanged[1:]:
				diffs.append((prev[1], u[0]))
				prev = u
		return diffs

	# processes diffs
	def processDiffs(self, view, diffs, currentText):
		print "got some diffs. Sending"
		for d in diffs:
			if d[0] != d[1]:
				self.jsonComposer.rpcSend(json.dumps(self.jsonComposer.editFileJson("insert", d[0], view.substr(Region(d[0],d[1])))), True)	
		self.oldText = currentText;		
			  
	# gets diffs		  
	def track_sync(self, view, currentText, filename):
		try:
			if not self.savePoint:
				with open(filename, "rU") as f:
					originalText = f.read().decode('utf8')
				self.jsonComposer.filename = filename
				self.oldText = originalText
				self.savePoint = True
			diffs = self.get_diff(self.oldText, currentText)
			# execute diff processing
			sublime.set_timeout(functools.partial(self.processDiffs, view, diffs, currentText),1)
		except:
			pass

	# gets currents text and starts diff processing in a new thread		
	def track(self, view):
		currentText = view.substr(Region(0, view.size()))
		filename = view.file_name()
		self.diff_thread = Thread(target=self.track_sync, args=(view, currentText, filename))
		self.diff_thread.start()

# command class for linking a file
class LinkfileCommand(sublime_plugin.TextCommand):
	def run(self, edit):		
		global GLOBAL_REG
		GLOBAL_REG[self.view.file_name()] = True
		jsonComposer = JsonComposer();
		jsonComposer.filename = self.view.file_name() 
		jsonComposer.rpcSend(json.dumps(jsonComposer.linkFileJson()), False)

# command class for unlinking a file
class UnlinkfileCommand(sublime_plugin.TextCommand):
	def run(self, edit):		
		global GLOBAL_REG
		if GLOBAL_REG.has_key(self.view.file_name()):
			del GLOBAL_REG[self.view.file_name()]
		jsonComposer = JsonComposer();
		jsonComposer.filename = self.view.file_name() 
		jsonComposer.rpcSend(json.dumps(jsonComposer.unlinkFileJson()), False)		

# event listener for changes
class TrackChangesWhenTypingListener(sublime_plugin.EventListener):
	def __init__(self):
		self.timer = None
		self.pending = True
		self.jsonComposer = JsonComposer()
		self.trackChangesCore = TrackChangesCore()
	
	# nothing to do			   
	def handle_timeout(self, view):
		return 
	
	# nothing to do
	def on_idle(self, view): 
		return
   
    # checks if file is under change tracking and calls change tracker
	def on_modified(self, view):
		global GLOBAL_REG
		if GLOBAL_REG.has_key(view.file_name()):
			self.trackChangesCore.track(view) 