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
import logging
import sys
import traceback
from AgentClient import AgentClient
from JsonComposer import JsonComposer
import asyncore

#global exception handling
def global_exception_handler(type, value, traceback):
	logging.error(value)
	logging.exception(traceback)
	print value

sys.excepthook = global_exception_handler

# global registration for files to be under change tracking
GLOBAL_REG = {}

AGENT_CLIENT = None

logging.basicConfig(filename='collaboration.log',level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('socket is created')

# Core class for change tracking
class TrackChangesCore:  
	def __init__(self):
		self.savePoint = False
		self.oldText = ""
		self.client = None
		self.jsonComposer = JsonComposer()
		clientThread = Thread(target=self.listen)
		clientThread.start()

	def afterInit(self, agentClient):
		print "got initialized agentClient!"

	def itsdone(self, result):
  		print "Done! result=%r" % (result)	

	def listen(self):
		cccpBase = '/Users/tschmorleiz/Projects/101/cccp/agent/dist'

		print 'CCCP agent location:' + cccpBase
		portFile = cccpBase + '/cccp.port'
		port = int(open(portFile, 'r').read())
		self.client = AgentClient("localhost", port, self.afterInit, self.itsdone)
		asyncore.loop()
		
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
				self.client.sendCommand(json.dumps(self.jsonComposer.editFileJson("insert", d[0], view.substr(Region(d[0],d[1])))))	
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
	

# event listener for changes
class TrackChangesWhenTypingListener(sublime_plugin.EventListener):
	def __init__(self):
		# connnect to the agent via the global socket
		try:
			#-------------TODO: we need to put this into a separate thread
			# to be able to communicate with this thread, we need to provide callbacks from this UI thread"
			self.trackChangesCore = TrackChangesCore()
			#asyncore.loop() <--- this blocks the thread
			#-----------end TODO--------------------

			#AGENT_SOCKET.connect(("localhost", port)) old sync verions
		except Exception as e:
			logging.error("error inside constructor of class TrackChangesWhenTypingListener(sublime_plugin.EventListener")
			msg = '{0} ; {0} ; {0}'.format(e, repr(e), e.message, e.args)
			logging.error(msg)
			print msg
	
	# nothing to do
	def handle_timeout(self, view): 
		return 
	
	# nothing to do
	def on_idle(self, view): 
		return
   
    # checks if file is under change tracking and calls change tracker
	def on_modified(self, view):
		self.trackChangesCore.track(view) 
