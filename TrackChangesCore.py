import difflib
import functools
import os
import sublime
import os
import sublime_plugin
import json
import socket
from threading import Thread, Lock
from sublime import Region
import logging
import sys
import traceback
from AgentClient import AgentClient
from JsonComposer import JsonComposer
import asyncore

INSERTING = False

# Core class for change tracking
class TrackChangesCore:  
	def __init__(self, settings, onInitialized):
		self.savePoint = False
		self.oldText = ""
		self.window = None
		self.agentClient = None
		self.onInitialized = onInitialized
		self.jsonComposer = JsonComposer(settings.get('host') or "localhost", settings.get('port') or 8885)
		# start listening in new thread
		clientThread = Thread(target=self.listen)
		clientThread.start()
		self.reg = []
		self.afterConnectionInitialized = None

	# callback, after intialization send init-connection command to agent
	def afterInit(self, agentClient):
		print "got initialized agentClient!"
		agentClient.sendCommand(json.dumps(self.jsonComposer.initConnectionJson()))
		if self.afterConnectionInitialized != None:
			print "afterConnectionInitialized"
			self.afterConnectionInitialized()

	def insertedit(self, result):
		lock = Lock()
		lock.acquire()
		global INSERTING
		INSERTING = True
		print result.op, result.text, "at", result.offset, "in", result.filename
		for v in sublime.active_window().views():
			if v.file_name() == result.filename:
				edit = v.begin_edit()
				if result.op == ':insert':
					v.insert(edit, result.offset, result.text)
				if result.op == ':delete':
					v.erase(edit, Region(result.offset, result.offset + len(result.text)))
				v.end_edit(edit)
				self.oldText = v.substr(Region(0, v.size()))
				if not self.savePoint:
					self.jsonComposer.filename = v.file_name()
					self.savePoint = True  
		INSERTING = False
		lock.release()
			

	# callback after command was sent
	def itsdone(self, result): 
		sublime.set_timeout(functools.partial(self.insertedit, result),1)
  		
  	# sets up AgentClient and listens
	def listen(self):
		try:
			self.agentClient = AgentClient(self.afterInit, self.itsdone)
			self.onInitialized(self.agentClient)
		except Exception as e:
			logging.error("Error while sending message to agent " + host + ":" + port)
			emsg = '{0} ; {0} ; {0} ; {0}'.format(e, repr(e), e.message, e.args)
			logging.error(emsg)
			print emsg
			pass
		
	# computes diffs between s1 and s2	 
	def get_diff(self, s1, s2):
		diffs = []
		s = difflib.SequenceMatcher(None, s1, s2)
		for tag, i1, i2, j1, j2 in s.get_opcodes():
			if tag == 'insert':
				diffs.append(("insert", j1, j2))
			if tag == 'delete':
				diffs.append(("delete", i1, i2))
		return diffs
 
	# processes diffs
	def processDiffs(self, view, diffs, currentText):
		print "got some diffs. Sending"
		for d in diffs: 
			if d[1] != d[2]:
				difftext = ""
				r1 = 0
				r2 = 0
				if d[0] == "insert":
					difftext = view.substr(Region(d[1],d[2]))
					r1 = d[1]
					if d[1] == 0:
						r1 = r1 + 1 
					r2 = view.size() - r1
				if d[0] == "delete":
					r1 = 0
					#difftext = self.oldText[d[1]:d[2]]
					#boffset = len(self.oldText) - 1
				if difftext != "":	
					self.agentClient.sendCommand(json.dumps(self.jsonComposer.editFileJson(view.file_name(), d[0], r1, r2, difftext)))	
		self.oldText = currentText;		
			  
	# gets diffs		  
	def track_sync(self, view, currentText, filename): 
		try:
			if not self.savePoint:   
				with open(filename, "rU") as f:
					originalText = f.read().decode('utf8')
				self.oldText = originalText
				self.savePoint = True       
			diffs = self.get_diff(self.oldText, currentText)    
			# execute diff processing
			sublime.set_timeout(functools.partial(self.processDiffs, view, diffs, currentText),1)
		except:
			pass

	def addFile(self, fileName, fileId):
		if not self.agentClient.connected:
			self.afterConnectionInitialized = self.agentClient.sendCommand(json.dumps(self.jsonComposer.linkFileJson(fileId, fileName)))
			cccpBase =  os.environ['CCCP'] 
			print 'CCCP agent location: ' + cccpBase
			portFile = cccpBase + '/cccp.port'
			port = int(open(portFile, 'r').read())
			self.agentClient.initConnection("localhost", port)
		else:
			self.agentClient.sendCommand(json.dumps(self.jsonComposer.linkFileJson(fileId, fileName)))
		self.reg.append(fileName)

	# gets currents text and starts diff processing in a new thread		
	def track(self, view):
		print "Tracking", view.file_name(), "?"
		if not view.file_name() in self.reg:
			print "No."
			return;
		print "Yes."
		lock = Lock()
		lock.acquire()
		global INSERTING
		if INSERTING == False :
			currentText = view.substr(Region(0, view.size()))
			filename = view.file_name()
			self.diff_thread = Thread(target=self.track_sync, args=(view, currentText, filename))
			self.diff_thread.start()
			self.diff_thread.join()
		lock.release()	

if __name__ == "__main__":
    main()		