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
import asyncore
from AgentClient import AgentClient
from JsonComposer import JsonComposer
from TrackChangesCore import TrackChangesCore

#global exception handling
def global_exception_handler(type, value, traceback):
	logging.error(value)
	logging.exception(traceback)
	print value

sys.excepthook = global_exception_handler

# global registration for files to be under change tracking, this stores an associated JsonComposer
AGENT_CLIENT = None
TRACK_CHANGES_CORE = None

logging.basicConfig(filename='collaboration.log',level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('socket is created')
s = sublime.load_settings("Collaboration.sublime-settings")
	
# command class for linking a file
class LinkfileCommand(sublime_plugin.TextCommand):
	def run(self, edit):	
		self.v = self.view	
		# get fileId from user
		self.view.window().show_input_panel("Enter fileId to link to:", "", functools.partial(self.on_done, self.view), None, None)
		
	def on_done(self, view, fileId):
		global TRACK_CHANGES_CORE
		print view
		print view.file_name()
		TRACK_CHANGES_CORE.addFile(view.file_name(), fileId)

	def	description(self):
		return "Links the current file to the cccp agent. Running this command will eventually insert preceding edits."	

# command class for unlinking a file
class UnlinkfileCommand(sublime_plugin.TextCommand):
	def run(self, edit):		
		global TRACK_CHANGES_CORE
		TRACK_CHANGES_CORE.reg = filter (lambda a: a != self.view.file_name(), TRACK_CHANGES_CORE.reg)
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
			global TRACK_CHANGES_CORE
			TRACK_CHANGES_CORE = TrackChangesCore(s, self.onInitialized)
		except Exception as e:
			logging.error("error inside constructor of class TrackChangesWhenTypingListener(sublime_plugin.EventListener")
			logging.error(e.message)
			print e.message
	
	def onInitialized(self, agentClient):
		print "onInitialized"
		global AGENT_CLIENT	
		AGENT_CLIENT = agentClient	

	# nothing to do
	def handle_timeout(self, view): 
		return 
	
	# nothing to do
	def on_idle(self, view): 
		return
   
    # checks if file is under change tracking and calls change tracker
	def on_modified(self, view):
		TRACK_CHANGES_CORE.track(view) 
				
