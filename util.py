import pickle
from Block import Block
from Transaction import Transaction
import os
from hashing import *
import datetime
import json
import glob
import shutil
import socket

# DO NOT EDIT (but it may be helpful to read this thoroughly) #

def load_valid_chain():
    '''
    Loads and return valid chain and transactions presents in the valid chain
    '''
    new_chain=[]
    new_transactions =[]
    DIR = "valid_chain"
    length = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    for block_index in range(length):
        with open(DIR+'/block{}.block'.format(block_index), 'rb') as inp:
            block = pickle.load(inp)
            for tx in block.transactions:
                new_transactions.append(tx)
            new_chain.append(block)
    return new_chain, new_transactions

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Let OS pick a free port
        return s.getsockname()[1]

def load_unconfirmed_transactions(confirmed_transactions, corrupt_transactions):
        '''
        Takes confirmed and corrupt transactions, and returns disjoint unconfirmed transactions from the mempool
        '''
        DIR = "mempool/"
        #MAX_TRANSACTIONS = 5
        temp_transactions = []

        indexes=[i['id'] for i in confirmed_transactions] + [i['id'] for i in corrupt_transactions]

        files = [name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]
        for filename in files:
            with open(DIR + filename, 'rb') as inp:
                trans = pickle.load(inp)
                if trans.id not in indexes:
                    temp_transactions.append(trans.__dict__)
                #if len(temp_transactions) >= MAX_TRANSACTIONS:
                #    break
        return temp_transactions


def save_chain(chain):
        '''
        Takes any chain and saves to valid chain folder
        '''
        for path in glob.glob("valid_chain/*"):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        block_count=0
        for block in chain:
            save_object(block, "valid_chain/" + "block{}.block".format(block_count))
            block_count+=1

def save_object(obj, filename):
        '''
        helper function for above
        '''
        with open(filename, 'wb') as outp:  # Overwrites any existing file.
            pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)

def load_all_unconfirmed_transactions(confirmed_transactions, corrupt_transactions):
        '''
        Takes confirmed and corrupt transactions, and returns disjoint unconfirmed transactions from the mempool
        '''
        DIR = "mempool/"
        temp_txns = []
        indexes=[i['id'] for i in confirmed_transactions] + [i['id'] for i in corrupt_transactions]
        files = [name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]
        for filename in files:
            with open(DIR + filename, 'rb') as inp:
                trans = pickle.load(inp)
                if trans.id not in indexes:
                    temp_txns.append(trans.__dict__)
        return temp_txns