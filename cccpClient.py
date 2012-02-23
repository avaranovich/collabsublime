# source code adopted from https://github.com/alek-sys/ChangeTracker
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

#global exception handling
def global_exception_handler(type, value, traceback):
	logging.error(value)
	logging.exception(traceback)
	print value

sys.excepthook = global_exception_handler

# global registration for files to be under change tracking, this stores an associated JsonComposer
GLOBAL_REG = {}

AGENT_CLIENT = None

INSERTING = False

logging.basicConfig(filename='collaboration.log',level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('socket is created')
s = sublime.load_settings("Collaboration.sublime-settings")

# Core class for change tracking
class TrackChangesCore:  
	def __init__(self):
		self.savePoint = False
		self.oldText = ""
		self.window = None
		self.jsonComposer = JsonComposer(s.get('host') or "localhost", s.get('port') or 8885)
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
			global AGENT_CLIENT
			AGENT_CLIENT = AgentClient(self.afterInit, self.itsdone)
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
				global AGENT_CLIENT 
				AGENT_CLIENT.sendCommand(json.dumps(self.jsonComposer.editFileJson(view.file_name(), "insert", d[0], view.size()-d[0] , view.substr(Region(d[0],d[1])))))	
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
	
# command class for linking a file
class LinkfileCommand(sublime_plugin.TextCommand):

	def run(self, edit):		
		# get fileId from user
		self.view.window().show_input_panel("Enter fileId to link to:", "", self.on_done, None, None)
		
	def on_done(self, fileId):
		global GLOBAL_REG
		GLOBAL_REG[self.view.file_name()] = True
		jsonComposer = JsonComposer(s.get('host') or "localhost", s.get('port') or 8885)
		global AGENT_CLIENT	
		if not AGENT_CLIENT.connected:
			cccpBase =  os.environ['CCCP'] 
			print 'CCCP agent location: ' + cccpBase
			portFile = cccpBase + '/cccp.port' df
			port = int(open(portFile, 'r').read())
			AGENT_CLIENT.initConnection("localhost", port)
		AGENT_CLIENT.sendCommand(json.dumps(jsonComposer.linkFileJson(fileId, self.view.file_name())))

	def	description(self):
		return "Links the current file to the cccp agent. Running this command will eventually insert preceding edits."	

# command class for unlinking a file
class UnlinkfileCommand(sublime_plugin.TextCommand):
	def run(self, edit):		
		global GLOBAL_REG
		if GLOBAL_REG.has_key(self.view.file_name()):
			del GLOBAL_REG[self.view.file_name()]
		jsonComposer = JsonComposer(s.get('host') or "localhost", s.get('port') or 8885);
		global AGENT_CLIENT	
		AGENT_CLIENT.sendCommand(json.dumps(jsonComposer.unlinkFileJson(self.view.file_name())))
	
	def	description(self):
		return "Unlinks the current file from the cccp agent."


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
		lock = Lock()
		lock.acquire()
		global INSERTING
		if INSERTING == False :
			global GLOBAL_REG
			if GLOBAL_REG.has_key(view.file_name()):
				self.trackChangesCore.track(view) 
		lock.release()		
