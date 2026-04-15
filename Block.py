# DO NOT EDIT #
class Block:
	def __init__(self, index, transactions, time_stamp, previous_hash, miner, nonce=0):
		self.index = index
		self.transactions = transactions
		self.time_stamp = time_stamp
		self.previous_hash = previous_hash
		self.nonce = nonce
		self.miner = miner
