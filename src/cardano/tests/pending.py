from src.cardano.base import Keys, Node
from src.cardano.base import Wallet
import src.cardano.utils as utils

key= Keys()
# node = Node()

# keys1 = key.deriveAllKeys(24,'wallet01')

# key.generateCardanoKeys('policy')
# name = 'policy'
# key_hash = key.keyHashing(name)
# # print(key_hash)
# type= "atLeast"
# keyHashes = [key_hash]
# key.create_multisig_script(name, type,1, keyHashes)
# script_addr = key.create_address_script(name)
# print(script_addr)

# key= Keys()
# wallet_name = 'wallet01'
# nmemonic_size = 24
# key.deriveAllKeys(nmemonic_size,wallet_name)

wallet_names = ['wallet01', 'wallet02', 'wallet03']

keyHashes = []
for name in wallet_names:
    key_info = key.deriveAllKeys(24, name)
    hash = key_info['hash_verification_key']
    keyHashes.append(hash)

type = "atLeast"
required = 2
multisig_script = key.create_multisig_script(name, type, required, keyHashes)

script_address = key.create_address_script(name)
print(script_address)