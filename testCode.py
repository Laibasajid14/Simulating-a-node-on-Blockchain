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

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Let OS pick a free port
        return s.getsockname()[1]

if __name__ == "__main__":

    backend_p = 6960
    host = get_host(backend_p)
    backend = (host, backend_p)
    try:
        id = int(input("Enter your erp id: "))
        port = get_free_port()

    except:
        print("Invalid ID")
        sys.exit()
    """
    Node connection setup 
    """
    node = Node(host, port, backend, str(id))
    node.start_connection()
    N = FullNode(id)
    N.valid_chain, N.confirmed_transactions = load_valid_chain()
    N.unconfirmed_transactions = load_unconfirmed_transactions(N.confirmed_transactions, N.corrupt_transactions)
    N.all_unconfirmed_transactions = load_all_unconfirmed_transactions(N.confirmed_transactions, N.corrupt_transactions)
    node.send_states()

    N.valid_chain, N.confirmed_transactions = load_valid_chain()
    N.unconfirmed_transactions = load_unconfirmed_transactions(N.confirmed_transactions, N.corrupt_transactions)
    N.all_unconfirmed_transactions = load_all_unconfirmed_transactions(N.confirmed_transactions, N.corrupt_transactions)

    All_transaction = []

    N.valid_chain.sort(key=N.sortHelper)

    for blk in N.valid_chain:
        if not blk.index:
            continue
        print(blk.index, blk.miner, N.computeBlockHash(blk)[0:10], blk.previous_hash[0:10])
        for Tx in blk.transactions:
            print(N.verifyTransaction(Tx))

    for Tx in N.unconfirmed_transactions:
        All_transaction.append(Tx)

    for Tx in N.confirmed_transactions:
        if Tx.get("number", -100) != -100:
            All_transaction.append(Tx)

    print(len(All_transaction), len(N.unconfirmed_transactions), len(N.confirmed_transactions))

    All_transaction.sort(key=N.sortHelperNumber)

    your_marks = 0

    N.verifyTransaction(All_transaction[0])

    balance = N.showAccounts()

    if (not balance) or balance.get(97900424532147900438859704322823053922997230128479610197495596665802299846947) != 5000000000:
        print("You have not been able to pick up CoinBase transactions")
    else:
        your_marks += 5

    CantVerifyCB = False
    for i in range(10):
        if not N.verifyTransaction(All_transaction[i]) and i:
            CantVerifyCB = True

if not CantVerifyCB:
    your_marks += 5
else:
    print("Your code can not verify coinbase transactions")

if (not balance) or balance.get(
        97900424532147900438859704322823053922997230128479610197495596665802299846947) != 5000000000 and not CantVerifyCB:
    print("You seem to be considering coinbase transactions twice. There should no duplicate transactions")
else:
    your_marks += 5

balance = N.showAccounts()

N.verifyTransaction(All_transaction[10])

balance = N.showAccounts()

if (not balance) or balance.get(97900424532147900438859704322823053922997230128479610197495596665802299846947, -9999) != 0:  #####
    print("You are not removing a spent UTXO")
else:
    your_marks += 5

if (not balance) or balance.get(61368317325581018485444567640877575581714997222663672800401752329642593681898) != 9999999835:
    print("You are not updating the balance of a recipient in your UTXO database")
else:
    your_marks += 5

for i in range(16):
    N.verifyTransaction(All_transaction[i])

balance = N.showAccounts()

N.verifyTransaction(All_transaction[14])

for inp in N.unconfirmed_transactions[14]['inputs']:
    print("Bad transaction was trying to: ", hashPubKey(inp[3]))

if (not balance) or balance.get(43558234995138531315276814253345165558232202230712793313817517100022236863201) != 5000000000:
    print("You have allowed a transaction with a faulty signature.")
else:
    your_marks += 5

for i in range(1000):
    N.verifyTransaction(All_transaction[i])

balance = N.showAccounts()

if (not balance) or balance.get(97900424532147900438859704322823053922997230128479610197495596665802299846947) != 47783348 or \
        balance.get(61368317325581018485444567640877575581714997222663672800401752329642593681898) != 3987997543 or \
        balance.get(43558234995138531315276814253345165558232202230712793313817517100022236863201) != 1792825777 or \
        balance.get(40189016485892926282548271016069919390207554076965828391660538936131874139403) != 9942931921 or \
        balance.get(68957154921550612234866922340053330019704169724720129011905449946148775763014) != 60512845 or \
        balance.get(25710847192128860711870250207729231661178476158772968986907201458313275253420) != 2531522792 or \
        balance.get(870957153513604955099783510612415718372330343087099090278033937281925992370) != 1904043603 or \
        balance.get(99652275076723255094766834832004149220812205664595801229873801477016512014599) != 11664420824 or \
        balance.get(85128033328377724622986738793818727043753474774787377171671560282379194970854) != 13396149551 or \
        balance.get(87316322514699652727249331442542001328835646615455141794091667247614728216777) != 4671489268:
    print("You have allowed some transactions to double spend")
else:
    your_marks += 10

print(f"\nYour Marks: {your_marks} out of 40")

node.disconnect()

