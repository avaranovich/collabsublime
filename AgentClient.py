import asyncore, socket, json
import Queue

class AgentClient(asyncore.dispatcher):
	def __init__(self, host, port):
		try:
			asyncore.dispatcher.__init__(self)
			self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
			self.connect( (host, port) )
			#queue stores commands to be send
			self.cmd_q = Queue.Queue()
			#queue stores replies from the agent
        	self.reply_q = Queue.Queue()
			msg = json.dumps({"swank":"init-connection", "args":[{"protocol": "http", "host": "localhost", "port" : 8585}], "callId" : 1})
			hexed = "0000" + hex(len(msg))[2:]
			toSend = hexed + msg
			self.buffer = toSend	
	 	except Exception as e:
			logging.error("error while creating AgentClient")
			msg = '{0} ; {0} ; {0}'.format(e, repr(e), e.message, e.args)
			logging.error(msg)
			#TODO: notify a user that plugin will not work, because it was not able to set up the connection; perhaps the agent is not running?

	def handle_connect(self):
		print "connected to the agent"
		pass
		
	def handle_write(self):
		sent = self.send(self.buffer)
		self.buffer = self.buffer[sent:]

	def handle_close(self):
		print "closed"
		self.close()

	def handle_read(self):
		print self.recv(8192)
	
	def handle_error(self):
		print "error"  
		
	def writable(self):
		return (len(self.buffer) > 0)