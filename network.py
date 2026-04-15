from Block import Block
from Transaction import Transaction
import socket
import threading
from util import *
from hashlib import sha256
import shutil
import time

END_MSG='#END#'
# DO NOT EDIT
class Node:
	def __init__(self, host, port,backend_addr, ID):
		self.port=port 
		self.host=host
		self.Network=[socket]
		self.enable=True
		self.backend_addr= backend_addr
		self.soc=socket.socket()
		self.state_sender=socket.socket()
		self.connected=False
		self.userID = ID
		self.PACKET_SIZE =4096
		self.msg_count=0
		self.recv_buffer = ""
		threading.Thread(target = self.listen).start()

	def reset_sockets(self, assign_new_port=False):
		self.connected = False
		self.awaiting_response = False
		self.pending_request_type = None
		self.pending_request_started_at = 0
		for sock in (self.soc, self.state_sender):
			try:
				sock.close()
			except:
				pass
		self.soc = socket.socket()
		self.state_sender = socket.socket()
		if assign_new_port:
			self.port = get_free_port()

	def start_connection(self):
		if not self.connected:
			try:
				self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.soc.settimeout(5.0)
				self.soc.bind(("0.0.0.0", self.port))
				self.soc.connect(self.backend_addr)
				self.state_sender.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.state_sender.settimeout(5.0)
				self.state_sender.bind(("0.0.0.0", self.port + 1))
				self.state_sender.connect((self.backend_addr[0], self.backend_addr[1]+1))
				self.connected = True
				print("Connected to backend", flush=True)
			except Exception as e:
				print("Failed to connect to backend:", e, flush=True)
				self.reset_sockets(assign_new_port=True)
				raise
			finally:
				try:
					self.soc.settimeout(None)
				except:
					pass
				try:
					self.state_sender.settimeout(None)
				except:
					pass

	def listen(self):
		"""
		This method listens to messages from backend.
		"""
		while self.enable:
			if not self.connected:
				time.sleep(0.1)
				continue
			try:
				data = self.soc.recv(self.PACKET_SIZE).decode("utf-8")
				if not data:
					continue
				self.recv_buffer += data
				self.recv_buffer = self.recv_buffer.lstrip('X')
				while END_MSG in self.recv_buffer:
					message, self.recv_buffer = self.recv_buffer.split(END_MSG, 1)
					message = message.rstrip('X')
					self.recv_buffer = self.recv_buffer.lstrip('X')
					if message:
						self.handleTransmission(message)
			except Exception as e:
				if self.enable:
					print("listen error:", e)

	def handleTransmission(self, message):
		delimiter = '|'
		parts = message.split(delimiter, 2)
		if len(parts) != 3:
			return
		type, sender, data = parts
		if type == 'pending_chain':
			self.awaiting_response = False
			self.pending_request_type = None
			self.pending_request_started_at = 0
			chain = self.json_to_chain(data)
			self.save_pending_chain(chain, sender)
		elif type == 'retry':
			self.awaiting_response = False
			self.pending_request_type = None
			self.pending_request_started_at = 0
			print("Backend has no longer chain yet, please try again after some time...")
		elif type == 'timeout':
			self.awaiting_response = False
			self.pending_request_type = None
			self.pending_request_started_at = 0
			print("User timed out. Resetting backend connection.", flush=True)
			self.reset_sockets(assign_new_port=True)

	def mux_msg(self,message):
		message+=END_MSG
		message_list=[]
		for idx in range(0,len(message),self.PACKET_SIZE):
			msg=message[idx:self.PACKET_SIZE+idx]
			if len(msg)!=self.PACKET_SIZE:
				msg=msg+'X'*(self.PACKET_SIZE-len(msg))
			message_list.append(msg)
		return message_list

	def send_states(self):
		"""
		This method on end sends the current state of a node's Blockchain to the backend.
		Sends only if there's a change in the chain.
		"""
		hash_headers_new= None
		current_chain,_ = load_valid_chain()
		hash_headers=[self.compute_hash(block) for block in current_chain]	
		if hash_headers_new!=hash_headers:
			try:
				self.start_connection()
				delimiter='|'
				type='state'
				packet=type+delimiter+self.userID+delimiter+self.chain_to_json(current_chain)+delimiter+' '.join(hash_headers)
				packets = self.mux_msg(str(packet))
				for p in packets:
					self.state_sender.sendall(p.encode('utf-8'))
			except Exception as e:
				print("Failed to send state:", e, flush=True)
				self.reset_sockets(assign_new_port=True)

	def json_to_chain(self,js):
		"""
		Converts json chain to a list chain
		"""
		chain_json=json.loads(js)
		chain=[]
		for key in chain_json:
			block=chain_json[key]
			block_new=Block(block['index'],block['transactions'],block['time_stamp'],block['previous_hash'],block['miner'],block['nonce'])
			chain.append(block_new)
		return chain
		
	def save_pending_chain(self, chain, senderID): 
		"""
		Saves a recieved pending chain from backed to the pending chain folder
		"""
		block_count=chain[0].index
		DIR='pending_chains'

		userdir=DIR+'/{}'.format(senderID)
		shutil.rmtree(userdir, ignore_errors=True)
		os.mkdir(DIR+'/{}'.format(senderID))
		print("Chain received from", senderID)
		for block in chain:
			send_dir="{}/{}/block{}.block".format(DIR,senderID,block_count)
			save_object(block,send_dir)
			block_count+=1
	def chain_to_json(self,chain):
		"""
		Converts a list chain to a json chain
		"""
		chain_json={}
		for block in chain:
			chain_json[str(block.index)]=block.__dict__
		chain_json=json.dumps(chain_json)
		return chain_json

	def broadcast(self,chain):
		"""
		This method sends the current chain to the backend to broadcast to all the nodes.
		"""
		chain_json=self.chain_to_json(chain)
		type='broadcast'
		delimiter='|'
		packet=type+delimiter+self.userID+delimiter+chain_json
		try:
			self.start_connection()
			packets = self.mux_msg(packet)
			print(f"Broadcasting chain in {len(packets)} packet(s)", flush=True)
			for p in packets:
				self.soc.sendall(p.encode('utf-8'))
		except Exception as e:
			print("Failed to broadcast chain:", e, flush=True)
			self.reset_sockets(assign_new_port=True)

	def request(self, chain, requested):
		"""
		This method requests the longest or all the chains present in the network depending on 'requested' variable
		"""
		hash_headers=[self.compute_hash(block) for block in chain]
		delimiter='|'
		type='request_' + requested
		packet=type+delimiter+self.userID+delimiter+' '.join(hash_headers)
		try:
			self.start_connection()
			packets = self.mux_msg(packet)
			for p in packets:
				self.soc.sendall(p.encode('utf-8'))
		except Exception as e:
			print(f"Failed to send {type}:", e, flush=True)
			self.reset_sockets(assign_new_port=True)

	def compute_hash(self,block):
		"""	
		Computes the hash of the block by treating all the contents of the block object as a dict.
		"""
		block_string = json.dumps(block.__dict__, sort_keys=True)
		return sha256(block_string.encode()).hexdigest()
		
	def disconnect(self):
		self.enable = False
		self.soc.close()
		self.state_sender.close()
		os._exit(1)
