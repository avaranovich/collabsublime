import sublime

class JsonComposer:
	def __init__(self, host, port):
		self.callid = 0
		print "JsonComposer with host", host, "and port", port
		self.host = host
		self.port = port
    
	def callId(self):
		self.callid = self.callid + 1      
		return self.callid

	def initConnectionJson(self):
		return ({"swank":"init-connection", "args":[{"protocol": "http",  "host": self.host, "port" : self.port}], "callId" : self.callId()})
    
	def linkFileJson(self, fileId, filename):
		return ({"swank":"link-file", "args":[{"id": fileId , "file-name": filename }], "callId" : self.callId()})
    
	def unlinkFileJson(self, filename):
		return ({"swank":"unlink-file", "args":[{ "file-name": filename }], "callId" : self.callId()})
    
	def editFileJson(self, filename, op, posf, posb, s):
		return ({"swank": "edit-file", "file-name": filename, "args":[{"retain": posf + 1}, { op: s}, {"retain": posb}], "callId" : self.callId()})