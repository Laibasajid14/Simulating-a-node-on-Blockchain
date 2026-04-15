class Transaction:
    def _init_(self):
        self.id = 0 #this is just for convenience. It is supposed to be the HASH of the transaction
        self.COINBASE = False #is it a coinbase transaction?
        self.inputs = []
        self.outputs = []
        
        self.number = 0 #This is just the transaction number. It has NO actual purpose, just to make the transactions appear (roughly) in order in the mempool
        #It is not used in the hash function or any signature. 
        return