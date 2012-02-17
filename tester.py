class JsonComposer:
	def __init__(self):
		self.filename = ""
		self.callid = 0

	def callId(self):
		self.callid = self.callid + 1      
		return self.callid

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