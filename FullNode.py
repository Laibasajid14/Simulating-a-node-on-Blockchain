from logging.config import valid_ident
import time
import pickle
from Block import Block
import os
import re
from hashing import *
import datetime
import json
from util import *
from network import Node
import sys
import copy
import shutil

"""
Establishing connection with backend
"""


class FullNode:
    def __init__(self, id):
        """
		DO NOT EDIT
		"""
        self.DIFFICULTY = 4  # Difficulty setting
        self.STUDENT_ID = id  # Do not edit, this is your student ID

        self.unconfirmed_transactions = []  # Raw 5 TXNs that you will get from the mempool
        self.all_unconfirmed_transactions = []  # all Raw unconfirmed txns from mempool
        self.valid_but_unconfirmed_transactions = {}
        self.valid_chain, self.confirmed_transactions = load_valid_chain()  # Your valid chain, all the TXNs in that valid chain
        self.corrupt_transactions = {}  # Initialize known invalid TXNs. To be appended to (by you, later). These are transactions whose signatures don't match or their output > input
        self.UTXO_Database_Pending = {}  # This is a temporary UTXO database you may use.
        self.UTXO_Database = {}

    def last_block(self):
        """
		DO NOT EDIT
		returns last block of the valid chain loaded in memory
		"""
        self.valid_chain.sort(key=self.sortHelper)
        return self.valid_chain[-1]

    ## PART ONE - UTXO Database Construction##

    ## Add code for part 1 here (You can make as many helper function you want)
    def verifyTransaction(self, Tx):
        pass

    def findValidButUnconfirmedTransactions(self):
        # find 5 valid transactions that are NOT in a block yet
        pass

	## PART TWO - Mining and Proof-Of-Work ##
	# Mine Blocks -- skip genesis block
    # Suggested steps:
    # 1. Update UTXO if update==True
    # 2. Copy to pending
    # 3. Collect valid transactions
    # 4. Create block
    # 5. Run proof_of_work
    # 6. Append and save block
    # 7. Update UTXO
    def mine(self, startingNonce=0, update=True):
        """
        Mines a new block containing valid unconfirmed transactions.

        Because proof_of_work may exit early without finding a valid hash,
        mine() is designed to be called repeatedly until it succeeds.
        The calling loop in main.py already handles this — study it before
        implementing this function, as your return values must match what
        it expects.

        Parameters:
            startingNonce (int): The nonce value to start searching from.
                                 Passed in by main.py — 0 on the first call,
                                 and whatever this function last returned on
                                 subsequent calls.
            update (bool): Whether to rebuild the UTXO database and collect
                           fresh transactions. Passed in by main.py — True on
                           the first call only, False on resume calls.

        Returns:
            0              if a block was successfully mined.
            nonce (int)    if proof_of_work exited early; main.py will pass
                           this back in as startingNonce on the next call.

        You should check what proof_of_work returns and handle both cases.
        """
        # Save block to physical memory here.
        # Syntax to store block: save_object(new_block,"valid_chain/block{}.block".format(new_block.index))
        return

    def proof_of_work(self, block):
        """
        Performs Proof-Of-Work on the given block by iterating the nonce until
        the block hash meets the difficulty condition (self.DIFFICULTY leading zeros)
        AND the nonce is a multiple of 10.

        To avoid blocking the program indefinitely, this function exits early
        after a fixed number of iterations if no valid hash is found yet.
        In that case, return (0, block.nonce) so the caller knows to resume
        from this nonce in the next call.

        If a valid hash IS found, return (computed_hash, block.nonce).

        Returns: (hash_string, nonce)  on success
                 (0, nonce)            on early exit (limit reached, keep trying)
        """
        pass

    def computeBlockHash(self, block):  # Compute the aggregate transaction hash.
        block_string = json.dumps(block.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def sortHelper(self, block):
        return block.index

    def sortHelperNumber(self, Tx):
        return Tx['number']

    def update_UTXO(self, till=-1):
        # Update your UTXO database according to your VALID_CHAIN folder.
        return

    def showAccounts(self):
        """return a dictionary with mapping from pubkeyHash to total crypto available
		Uses the PENDING UTXO database
		"""
        return

    ## PART TWO ##

    def validate_pending_chains(self):
        """
		DO NOT EDIT
		This method loads pending chains from the 'pending_chains' folder.
		It then calls verify_chain method on each chain performing a series of validity checks
		if all the tests pass, it replaces the current valid chain with pending chain and saves it in valid chain folder.
		"""
        Found = False

        self.valid_chain, self.confirmed_transactions = load_valid_chain()
        MAIN_DIR = "pending_chains"
        subdirectories = [name for name in os.listdir(MAIN_DIR) if os.path.isdir(os.path.join(MAIN_DIR, name))]
        if not subdirectories:
            print("No pending chains found to validate.")
            return False
        for directory in subdirectories:
            temp_chain = []
            DIR = MAIN_DIR + "/" + directory
            block_indexes = [name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]
            block_indexes.sort(key=lambda x: int(re.search(r'\d+', x).group()))
            for block_index in block_indexes:
                try:
                    with open(DIR + '/{}'.format(block_index), 'rb') as inp:
                        block = pickle.load(inp)
                        temp_chain.append(block)
                except:
                    pass
            last_block_index = temp_chain[0].index - 1
            if last_block_index >= len(self.valid_chain):
                print(f' last_block_index {last_block_index} >= len(self.valid_chain) {len(self.valid_chain)} ?')
                print("Rejected chain from", directory)
                shutil.rmtree(DIR, ignore_errors=True)
                continue

            last_block_hash = self.computeBlockHash(self.valid_chain[last_block_index])
            current_longest = self.valid_chain[:last_block_index + 1] + temp_chain
            if (self.verify_chain(current_longest, temp_chain, last_block_hash)):
                print("Replaced valid chain with chain from", directory)
                self.valid_chain = current_longest
                save_chain(current_longest)
                self.valid_chain, self.confirmed_transactions = load_valid_chain()
                Found = True
            else:
                print("Rejected chain from", directory)
            shutil.rmtree(DIR, ignore_errors=True)
        if not Found:
            print("No pending chain replaced your current valid chain.")
        return Found

    def verify_chain(self, current_longest, temp_chain, last_block_hash):
        # current_longest is the longest chain including any overlap with your valid chain
		# temp_chain is only the difference between your valid chain and the current longest chain
		# last_block_hash is the hash of the previous block of temp_chain[0]. If there is no overlap, for example, this should be
		# the hash of the genesis block
        # Steps to be followed:
        # Step 1: Check linkage
        # Step 2: Check indices
        # Step 3: Check PoW
        # Step 4: Rebuild UTXO and validate transactions
        """
		This method performs the following validity checks on the input temp, or pending, chain.
			- whether length of temp_chain is greater than current valid chain (consider checking indexes)
			- whether previous hashes of blocks correspond to calculated block hashes of previous blocks
			- whether the difficulty setting has been achieved
			- whether each transaction is valid
				- no two or more transactions have same id
				- the signature in transaction is valid
				- The UTXO calculation is correct (input = sum of outputs)
		Return True if all is good
		Return False if failed any one of the checks

		temp_chain: your peer's blocks/chain that is being tested
		current_longest: your valid chain + temp_chain/new blocks your peer mined
		last_block_hash: the hash of your last block
		"""
        return False

    def print_chain(self):
        """
		DO NOT EDIT
		Prints the current valid chain in the terminal.
		"""
        self.valid_chain, self.confirmed_transactions = load_valid_chain()

        self.valid_chain.sort(key=self.sortHelper)

        for block in self.valid_chain:
            print("***************************")
            print(f"Block index # {block.index}")

            for trans in block.transactions:
                # if not block.index: #This is because the first block is hard coded and may have a different format
                # 	print("Sender: {}".format(trans["sender"]['key']) )
                # 	print("Receiver: {}".format(trans['receiver']['key']))
                # 	print("Token: {}".format(trans["signature_token"]) )
                # 	print("UTXO input: {}".format(trans["UTXO_input"]))
                # 	print("Sender received: {}".format(trans["value_sender"]))
                # 	print("Receiver received: {}".format(trans["value_receiver"]))
                # 	print("ID: {}".format(trans["id"]))
                if block.index:
                    print(f'Transaction number {trans["number"]} with hash {trans["id"]}')

            print("---------------------------")

            print("nonce: {}".format(block.nonce))
            print("previous_hash: {}".format(block.previous_hash))
            print('hash: {}'.format(self.computeBlockHash(block)))
            print('Miner: {}'.format(block.miner))
            print("***************************")
            print("")
