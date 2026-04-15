from hashlib import sha256

def SignString(string,private_key):
	'''
	This method signs a string with the given private key
	'''
	string_encoded=string.encode()
	hash = int.from_bytes(sha256(string_encoded).digest(), byteorder='big')
	signature = pow(hash, private_key['d'], private_key['n'])
	return signature

def VerifySignature(string,signature,public_key):
	'''
	This method verifies if a string is signed with a private key corresponding to the given public key
	'''
	string_encoded=string.encode()
	hash = int.from_bytes(sha256(string_encoded).digest(), byteorder='big')
	hashSignature = pow(signature, public_key['e'], public_key['n'])
	return hash == hashSignature

def calculateHash(string):
	string_encoded=string.encode()
	hash = int.from_bytes(sha256(string_encoded).digest(), byteorder='big')
	return hash

def UnlockSignature(string,signature,public_key):
	'''
	This method verifies if a string is signed with a private key corresponding to the given public key
	'''
	string_encoded=string.encode()
	hash = int.from_bytes(sha256(string_encoded).digest(), byteorder='big')
	hashSignature = pow(signature, public_key['e'], public_key['n'])
	return hashSignature

def hashPubKey(pubKey):
    string = str(pubKey['e']) + ":" + str(pubKey['n'])
    return calculateHash(string)


def stringifyTransaction(Tx):
    '''
    operates on the Transaction object and converts it a string.
    This is useful for the purposes of computing a transaction hash
    This excludes the hash of the transaction which may be computed by getHash(stringifyTransaction(Tx))
    '''

    outputString="Transaction:"
    outputString+="COINBASE:"+str(Tx['COINBASE'])
    i = 0
    for inp in Tx['inputs']:
        outputString+="input" + str(i)+ ":"
        outputString+="prev_txn_id" + str(inp[0]) #this should be the hash of the parent transaction
        outputString+="output_number" + str(inp[1])
        outputString+="sig" + str(inp[2])
        outputString+="pubkey_rec" + str(inp[3])
        i+=1
    
    i = 0
    for output in Tx['outputs']:
        outputString+="output" + str(i)+ ":"
        outputString+="value:" + str(output[0])
        outputString+="pubkey_hash:" + str(output[1])
        i+=1
        
    return outputString

def stringifyTransactionExcludeSig(Tx): 
    '''
    This function is exactly the same as the above one but excludes the signature in the inputs
    This is necessary for computing the hash of the _current_ transaction for signing purposes
    Recall that a signature should include BOTH the hash of the parent transaction and everything in the current transaction except any signatures!
    '''
    outputString="Transaction:"
    outputString+="COINBASE:"+str(Tx['COINBASE'])
    i = 0
    for inp in Tx['inputs']:
        outputString+="input" + str(i)+ ":"
        outputString+="prev_txn_id" + str(inp[0]) #this should be the hash of the parent transaction
        outputString+="output_number" + str(inp[1])
        outputString+="pubkey_rec" + str(inp[3])
        i+=1
    
    i = 0
    for output in Tx['outputs']:
        outputString+="output" + str(i)+ ":"
        outputString+="value:" + str(output[0])
        outputString+="pubkey_hash:" + str(output[1])
        i+=1
        
    return outputString