import asyncore, socket, json
import Queue
from threading import Thread, Lock
import logging
from JsonComposer import JsonComposer

logging.basicConfig(filename='collaboration.log',level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('socket is created')

class EditFile:
	def __init__(self, message):
		#unhex = message[6:]
		jsonr = json.loads(message)
		self.filename = jsonr[1]['value']
		self.offset = int(jsonr[2][1]['value'])
		self.text = str(jsonr[2][3]['value'])

class AgentClient(asyncore.dispatcher):
	def __init__(self, afterInitCallback, afterReceivedCallback):
		self.afterReceived = afterReceivedCallback
		self.afterInitCallback = afterInitCallback
		self.buffer = ""
		self.connected = False
		# queue stores commands to be send
		self.cmd_q = Queue.Queue()
		# queue stores replies from the agent
		self.reply_q = Queue.Queue()

	def _initAsyncLoop(self, host, port, afterInit):
		asyncore.dispatcher.__init__(self)
		print host, port
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect( (host, port) )
		# start downloader in new thread
		downloader = Thread(target=self.downloadCommands)
		downloader.start()
		# inform  via callback
		self.connected = True
		afterInit(self)
		asyncore.loop()

 	def initConnection(self, host, port):
		try:
			init = Thread(target=self._initAsyncLoop, args=(host, port, self.afterInitCallback)
			init.start()
	 	except Exception as e:
			#logging.error("error while creating AgentClient")
			msg = '{0} ; {0} ; {0} ; {0}'.format(e, repr(e), e.message, e.args)
			#logging.error(msg)
			print msg
			pass
			# TODO: notify a user that plugin will not work, because it was not able to set up the connection; perhaps the agent is not running?

    # sends command by putting it in the queue
	def sendCommand(self, msg):
		self.cmd_q.put(msg)

    # gets command one at a time and passes it to rpcSend()
	def downloadCommands(self):
		print "Command downloader started"
		while True:
			print "Command downloader waiting for new message..."
			msg = self.cmd_q.get()
			self.rpcSend(msg)	
			print "Command sent " + msg
			self.cmd_q.task_done()

	# hex message and add to buffer
	def rpcSend(self,msg):
		hexed = "0000" + hex(len(msg))[2:]
		toSend = hexed + msg
		#self.buffer = toSend
		print "Sending..."
		try:	
			self.send(toSend)
		except Exception as e:
			#logging.error("Error while sending message to agent " + host + ":" + port)
			emsg = '{0} ; {0} ; {0} ; {0}'.format(e, repr(e), e.message, e.args)
			#logging.error(emsg)
			print emsg

	def handle_connect(self):
		print "Connected to the agent"
		pass
		
	def handle_write(self):
		#sent = self.send(self.buffer)
		#self.buffer = self.buffer[sent:]
		pass

	def handle_close(self):
		print "Connection closed"
		self.close()

	def handle_read(self):
		data = self.recv(8192)
		print "received " + data
		#decimalLength = int(length, 16)
		#print "received 6 bytes; message length: " + length +  "(" + decimalLength + ")"
		#data = self.recv(decimalLength)
		#for now we just support EditFile
		print data[6:]
		res = EditFile(data[6:].strip())
		print "received data from agent"
		self.afterReceived(res)
		
	def writable(self):
		return (len(self.buffer) > 0)
