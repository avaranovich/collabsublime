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
	def __init__(self, settings):
		self.savePoint = False
		self.oldText = ""
		self.window = None
		self.jsonComposer = JsonComposer(settings.get('host') or "localhost", settings.get('port') or 8885)
		self.agentClient = None
		# start listening in new thread
		clientThread = Thread(target=self.listen)
		clientThread.start()

	# callback, after intialization send init-connection command to agent
	def afterInit(self, agentClient):
		print "got initialized agentClient!"
		agentClient.sendCommand(json.dumps(self.jsonComposer.initConnectionJson()))

	def insertedit(self, result):
		lock = Lock()
		lock.acquire()
		global INSERTING
		INSERTING = True
		unhex = result[6:]
		jsonr = json.loads(unhex)
		filename = jsonr[1]['value']
		offset = int(jsonr[2][1]['value'])
		text = str(jsonr[2][3]['value'])
		print 'Inserting', text, 'at', offset
		for v in sublime.active_window().views():
			if v.file_name() == filename:
				edit = v.begin_edit()
				v.insert(edit, offset, text)
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
			asyncore.loop()
		except Exception as e:
			logging.error("Error while sending message to agent " + host + ":" + port)
			emsg = '{0} ; {0} ; {0} ; {0}'.format(e, repr(e), e.message, e.args)
			logging.error(emsg)
			print emsg
			pass
		
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
				self.agentClient.sendCommand(json.dumps(self.jsonComposer.editFileJson(view.file_name(), "insert", d[0], view.size()-d[0] , view.substr(Region(d[0],d[1])))))	
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

	# gets currents text and starts diff processing in a new thread		
	def track(self, view):
		currentText = view.substr(Region(0, view.size()))
		filename = view.file_name()
		self.diff_thread = Thread(target=self.track_sync, args=(view, currentText, filename))
		self.diff_thread.start()
		self.diff_thread.join()

if __name__ == "__main__":
    main()		