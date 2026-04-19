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
        """
        Verifies a single transaction against UTXO_Database_Pending.

        For COINBASE transactions  → unconditionally add outputs to the
        pending UTXO set and return True.

        For regular transactions:
          1. Every input must reference a UTXO that exists in
             UTXO_Database_Pending (proves funds are unspent).
          2. The public key supplied in the input must hash to the
             pubkey_hash recorded in that UTXO (proves ownership).
          3. The RSA signature in each input must be valid (proves
             authorisation). Transactions that fail #2 or #3 are added
             to self.corrupt_transactions.
          4. Sum(inputs) >= Sum(outputs)  (no money created from thin air;
             any surplus is an implicit miner fee).

        If all checks pass the spent UTXOs are removed and new output
        UTXOs are inserted, then True is returned.
        If any check fails, the UTXO set is left untouched and False is
        returned.
        """
        # Ensure corrupt_transactions is a list so util.py can iterate it as
        # a list of tx dicts. __init__ sets it to {} (dict); convert on first use.
        if isinstance(self.corrupt_transactions, dict):
            self.corrupt_transactions = list(self.corrupt_transactions.values())

        # Already confirmed corrupt – skip immediately
        if any(t['id'] == Tx['id'] for t in self.corrupt_transactions):
            return False

        # Lazy-init pubkey tracker (assignment forbids editing __init__)
        if not hasattr(self, '_seen_pubkeys'):
            self._seen_pubkeys = set()

        # Coinbase
        if Tx['COINBASE']:
            # Reject duplicate coinbase transactions
            if Tx['id'] in self.UTXO_Database_Pending:
                return False
            # Mark this coinbase as seen (duplicate-prevention marker)
            self.UTXO_Database_Pending[Tx['id']] = True
            # Add coinbase outputs to the pending UTXO set
            for i, output in enumerate(Tx['outputs']):
                value, pubkey_hash = output[0], output[1]
                self._seen_pubkeys.add(pubkey_hash)
                self.UTXO_Database_Pending[(Tx['id'], i)] = (value, pubkey_hash)
            return True

        # Regular transaction
        total_input  = 0
        total_output = 0
        spent_utxos      = []       # keys to delete on success
        spent_in_this_tx = set()    # detect intra-tx double-spend

        for inp in Tx['inputs']:
            prev_txn_id   = inp[0]
            output_number = inp[1]
            sig           = inp[2]
            pubkey_rec    = inp[3]

            utxo_key = (prev_txn_id, output_number)

            # Guard: same UTXO referenced twice inside one transaction
            if utxo_key in spent_in_this_tx:
                return False

            # Guard: UTXO must exist (not yet spent)
            if utxo_key not in self.UTXO_Database_Pending:
                return False

            utxo_value, utxo_pubkey_hash = self.UTXO_Database_Pending[utxo_key]
            self._seen_pubkeys.add(utxo_pubkey_hash)  # track even if about to be spent

            # Guard: sender must own this UTXO
            if hashPubKey(pubkey_rec) != utxo_pubkey_hash:
                self.corrupt_transactions.append(Tx)
                return False

            # Guard: signature must be valid
            # Protocol: finalString = str(parentHash) + ':' + str(currentHash)
            # where parentHash = prevTxnId (already an int) and
            # currentHash = SHA256 hash (as int) of the tx string excluding sigs
            current_hash = calculateHash(stringifyTransactionExcludeSig(Tx))
            final_string = str(prev_txn_id) + ':' + str(current_hash)
            if not VerifySignature(final_string, sig, pubkey_rec):
                self.corrupt_transactions.append(Tx)
                return False

            total_input += utxo_value
            spent_utxos.append(utxo_key)
            spent_in_this_tx.add(utxo_key)

        for output in Tx['outputs']:
            total_output += output[0]

        # Guard: cannot spend more than you own
        if total_input < total_output:
            self.corrupt_transactions.append(Tx)
            return False

        for key in spent_utxos:
            del self.UTXO_Database_Pending[key]

        for i, output in enumerate(Tx['outputs']):
            self._seen_pubkeys.add(output[1])
            self.UTXO_Database_Pending[(Tx['id'], i)] = (output[0], output[1])

        return True

    def findValidButUnconfirmedTransactions(self):
        """
        Iterate over all_unconfirmed_transactions and collect up to 5 that
        pass verifyTransaction (which also updates UTXO_Database_Pending so
        subsequent transactions see already-spent UTXOs correctly).

        Results are stored in self.valid_but_unconfirmed_transactions (dict
        keyed by transaction id).
        """
        self.valid_but_unconfirmed_transactions = {}
        count = 0
        for Tx in self.all_unconfirmed_transactions:
            if count >= 5:
                break
            if self.verifyTransaction(Tx):
                self.valid_but_unconfirmed_transactions[Tx['id']] = Tx
                count += 1

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
        if update:
            # Step 1 & 2: Rebuild UTXO from confirmed chain, copy to pending
            self.update_UTXO()
            self.UTXO_Database_Pending = copy.deepcopy(self.UTXO_Database)

            # Step 3: Collect up to 5 valid unconfirmed transactions
            self.findValidButUnconfirmedTransactions()

            # Step 4: Assemble the candidate block
            transactions  = list(self.valid_but_unconfirmed_transactions.values())
            last          = self.last_block()
            previous_hash = self.computeBlockHash(last)

            self._pending_block = Block(
                index         = last.index + 1,
                transactions  = transactions,
                time_stamp    = str(datetime.datetime.now()),
                previous_hash = previous_hash,
                miner         = self.STUDENT_ID,
                nonce         = startingNonce,
            )
        else:
            # Resume: just update the nonce on the already-built block
            self._pending_block.nonce = startingNonce

        # Step 5: Run proof of work
        result_hash, nonce = self.proof_of_work(self._pending_block)

        if result_hash == 0:
            # Early exit – tell the caller what nonce to resume from
            return nonce

        # Step 6: Save the successfully mined block to disk and memory
        save_object(
            self._pending_block,
            "valid_chain/block{}.block".format(self._pending_block.index),
        )
        self.valid_chain.append(self._pending_block)

        # Step 7: Refresh the UTXO database to include the new block
        self.update_UTXO()
        return 0

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
        LIMIT = 100_000          # iterations before yielding control
        prefix = '0' * self.DIFFICULTY
        iterations = 0

        computed_hash = self.computeBlockHash(block)

        while not (computed_hash.startswith(prefix) and block.nonce % 10 == 0):
            block.nonce += 1
            computed_hash = self.computeBlockHash(block)
            iterations += 1
            if iterations >= LIMIT:
                return (0, block.nonce)

        return (computed_hash, block.nonce)

    def computeBlockHash(self, block):  # Compute the aggregate transaction hash.
        block_string = json.dumps(block.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def sortHelper(self, block):
        return block.index

    def sortHelperNumber(self, Tx):
        return Tx['number']

    def update_UTXO(self, till=-1):
        """
        Rebuild self.UTXO_Database by replaying every transaction in
        self.valid_chain up to block index `till` (exclusive; default = all).

        After rebuilding, self.UTXO_Database_Pending is synchronised with a
        deep copy of self.UTXO_Database so that subsequent verifyTransaction
        calls start from a clean confirmed state.

        UTXO entries have the form:
            key  : (txn_id, output_index)   – uniquely identifies an output
            value: (amount, pubkey_hash)     – who owns how much
        """
        self.UTXO_Database_Pending = {}
        self._seen_pubkeys = set()  # reset tracking alongside pending UTXO
        chain = sorted(self.valid_chain, key=self.sortHelper)

        if till == -1:
            till = len(chain)

        # Skip genesis block (index 0) per assignment spec
        for block in chain[1:till]:
            for Tx in block.transactions:
                self.verifyTransaction(Tx)

        # Commit the pending snapshot as the confirmed UTXO database
        self.UTXO_Database = copy.deepcopy(self.UTXO_Database_Pending)

    def showAccounts(self):
        """return a dictionary with mapping from pubkeyHash to total crypto available
		Uses the PENDING UTXO database
		"""
        # Start with 0 for every pubkey we have ever seen (includes fully-spent users)
        seen = getattr(self, '_seen_pubkeys', set())
        accounts = {pkh: 0 for pkh in seen}
        for key, val in self.UTXO_Database_Pending.items():
            # Skip coinbase duplicate-prevention markers (key=int, val=True)
            if not isinstance(key, tuple) or not isinstance(val, tuple):
                continue
            value, pubkey_hash = val
            accounts[pubkey_hash] = accounts.get(pubkey_hash, 0) + value
        return accounts

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
        # Step 1: Length check 
        if temp_chain[-1].index <= self.valid_chain[-1].index:
            return False

        # Step 2 & 3: Linkage and index continuity 
        prev_hash      = last_block_hash
        expected_index = temp_chain[0].index

        for block in temp_chain:
            if block.index != expected_index:
                return False
            if block.previous_hash != prev_hash:
                return False
            prev_hash = self.computeBlockHash(block)
            expected_index += 1

        # Step 3: Proof-of-Work 
        prefix = '0' * self.DIFFICULTY
        for block in temp_chain:
            block_hash = self.computeBlockHash(block)
            if not block_hash.startswith(prefix):
                return False
            if block.nonce % 10 != 0:
                return False

        # Step 4: Transaction validation with a local UTXO snapshot
        # Build the UTXO from the agreed-upon prefix of current_longest
        last_block_index = temp_chain[0].index - 1
        temp_utxo = {}

        for block in current_longest[1:last_block_index + 1]:  # skip genesis (index 0)
            for Tx in block.transactions:
                if Tx['COINBASE']:
                    for i, output in enumerate(Tx['outputs']):
                        temp_utxo[(Tx['id'], i)] = (output[0], output[1])
                else:
                    for inp in Tx['inputs']:
                        temp_utxo.pop((inp[0], inp[1]), None)
                    for i, output in enumerate(Tx['outputs']):
                        temp_utxo[(Tx['id'], i)] = (output[0], output[1])

        # Replay temp_chain transactions
        seen_ids = set()

        for block in temp_chain:
            for Tx in block.transactions:
                # No duplicate transaction IDs anywhere in the chain
                if Tx['id'] in seen_ids:
                    return False
                seen_ids.add(Tx['id'])

                if Tx['COINBASE']:
                    for i, output in enumerate(Tx['outputs']):
                        temp_utxo[(Tx['id'], i)] = (output[0], output[1])
                    continue

                # Regular transaction
                total_input  = 0
                total_output = 0
                spent_keys   = []

                for inp in Tx['inputs']:
                    prev_txn_id   = inp[0]
                    output_number = inp[1]
                    sig           = inp[2]
                    pubkey_rec    = inp[3]

                    key = (prev_txn_id, output_number)

                    if key not in temp_utxo:
                        return False

                    utxo_value, utxo_pubkey_hash = temp_utxo[key]

                    if hashPubKey(pubkey_rec) != utxo_pubkey_hash:
                        return False

                    current_hash = calculateHash(stringifyTransactionExcludeSig(Tx))
                    final_string = str(prev_txn_id) + ':' + str(current_hash)
                    if not VerifySignature(final_string, sig, pubkey_rec):
                        return False

                    total_input += utxo_value
                    spent_keys.append(key)

                for output in Tx['outputs']:
                    total_output += output[0]

                if total_input < total_output:
                    return False

                # Commit this transaction to the local UTXO snapshot
                for key in spent_keys:
                    del temp_utxo[key]

                for i, output in enumerate(Tx['outputs']):
                    temp_utxo[(Tx['id'], i)] = (output[0], output[1])

        return True

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
