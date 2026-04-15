from Block import Block
from hashing import *
from util import *
from network import Node
import sys
from FullNode import FullNode
import socket

PUBLIC_BACKEND = "58.27.184.105"
PRIVATE_BACKEND = "172.17.5.96"

def can_connect(ip, port, timeout=1):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except:
        return False

def get_host(port):
    if can_connect(PRIVATE_BACKEND, port):
        return PRIVATE_BACKEND
    else:
        return PUBLIC_BACKEND
			
"""
DO NOT EDIT ANYTHING BELOW
"""
def commands():
	"""
	CLI to access the Blockchain class
	"""
	print("\"update_UTXO\" to update your UTXO database according to the blocks in your valid chain")
	print("\"mine\" to mine")
	print("\"validate\" to validate pending chains")
	print("\"ra\" to request all chains")
	print("\"rl\" to request longest chain")
	print("\"send state\" to send your current state to the backend")
	print("\"print\" to print saved chain")
	print("\"showAccounts\" to print all Accounts Balance")
	print("\"exit\" to exit")
	print("\"help\" to see available commands")
	
if __name__ == "__main__":	
    """
    Establishing connection with backend
    """
    # DO NOT EDIT
    backend_p=6960
    host = get_host(backend_p)
    backend=(host,backend_p)
    try:
        erp_id = int(input("Enter your ERP ID: "))

        port = get_free_port()

        id = str(erp_id)

    except:
        print("Invalid ID")
        sys.exit()
    """
    Node connection setup 
    """
    node=Node(host,port,backend, id)
    node.start_connection()
    commands()

    print("\nLoading (this may take a while)... ")
    N = FullNode(id)
    N.valid_chain, N.confirmed_transactions = load_valid_chain()
    N.unconfirmed_transactions = load_unconfirmed_transactions(N.confirmed_transactions, N.corrupt_transactions)
    N.all_unconfirmed_transactions = load_all_unconfirmed_transactions(N.confirmed_transactions, N.corrupt_transactions)
    node.send_states()

    while True:
        # reload everything fresh before each command
        N.valid_chain, N.confirmed_transactions = load_valid_chain()
        N.unconfirmed_transactions = load_unconfirmed_transactions(
            N.confirmed_transactions,
            N.corrupt_transactions
        )
        N.all_unconfirmed_transactions = load_all_unconfirmed_transactions(
            N.confirmed_transactions,
            N.corrupt_transactions
        )

        args = input("> ")

        if args == "update_UTXO":
            N.update_UTXO()
            print("UTXO database updated")

        elif args == "mine":
            print("Mining... this may take a while with difficulty", N.DIFFICULTY)
            startingNonce = 0
            update = True
            while True:
                startingNonce = N.mine(startingNonce, update=update)
                update = False  # only update UTXO on first call
                if startingNonce == 0:
                    print("Block successfully mined!")
                    break
                print(f"Still mining... tried up to nonce {startingNonce}")

        elif args == "validate":
            N.validate_pending_chains()

        elif args == "rl":
            print(f"Requested longest chain, check pending_chains folder")
            node.request(N.valid_chain, "longest")

        elif args == "ra":
            print("Requested all chains, check pending_chains folder")
            node.request(N.valid_chain, "all")

        elif args == "send state":
            node.send_states()
            print("State sent to backend")

        elif args == "print":
            N.print_chain()

        elif args == "showAccounts":
            N.showAccounts()

        elif args == "help":
            commands()

        elif args == "exit":
            node.disconnect()
            break
        else:
            print("Unknown command, type help to see available commands")
