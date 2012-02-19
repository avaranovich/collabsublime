import sublime

class JsonComposer:
	def __init__(self, host, port):
		self.filename = ""
		self.callid = 0
		print host, port
		self.host = host
		self.port = port
    
	def callId(self):
		self.callid = self.callid + 1      
		return self.callid

	def initConnectionJson(self):
		return ({"swank":"init-connection", "args":[{"protocol": "http",  "host": self.host, "port" : self.port}], "callId" : self.callId()})
    
	def linkFileJson(self):
		return ({"swank":"link-file", "args":[{"id": "id", "file-name": self.filename }], "callId" : self.callId()})
    
	def unlinkFileJson(self):
		return ({"swank":"unlink-file", "args":[{ "file-name": self.filename }], "callId" : self.callId()})
    
	def editFileJson(self, op, posf, posb,  s):
		return ({"swank": "edit-file", "file-name": self.filename, "args":[{"retain": posb}, { op: s}, {"retain": posf}], "callId" : self.callId()})