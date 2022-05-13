<<<<<<< HEAD
from src.cardano.base import Keys, Node

key = Keys()
node = Node()
=======
from src.cardano.base import Keys

key = Keys()
# node = Node()
>>>>>>> remotes/origin/dev

# tx_id = node.get_txid()
# print(tx_id)
# result = node.query_protocol()
# print(result)
# result = node.query_tip_exec()
# print(result)


# key = Keys()
# wallet_name1 = 'Payment wallet'
# result = key.generateCardanoKeys(wallet_name1)

# wallet_name2 = 'ForMinting'
# result = key.generateCardanoKeys(wallet_name2)

keys1 = key.deriveAllKeys(24, 'MasterGetFair')

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
# wallet_name = 'ForMinting'
# nmemonic_size = 24
# key.deriveAllKeys(nmemonic_size,wallet_name)

wallet_names = ['wallet01', 'wallet02', 'wallet03']

# keyHashes = []
# for name in wallet_names:
#     key_info = key.deriveAllKeys(24, name)
#     hash = key_info['hash_verification_key']
#     keyHashes.append(hash)

# type = "atLeast"
# required = 2
# scriptName = '3multisig'
# # multisig_script = node.create_multisig_script(scriptName, type, required, keyHashes)

# script_address = key.create_address_script(scriptName)
# print(script_address)
# witness = 2
# # script_address = 'addr_test1wrsg430cfkehezut0r9yyl9y6d6vaa4dydkg2wy260ake8c2ft6hp'
# # script_address = 'addr_test1wq9hxaynns7n349gdxwu375twnweqqy8vngnnhqhx43gutg6zls8t'

# transactions = node.get_transactions(script_address)
# print(transactions)
# balance = node.get_balance(script_address)
# print(balance)

#########
# Build the components of the transaction
#########

# script_address = 'addr_test1vqt0wg92urd7pm5y50lvzulkvw2h888k60429ueykc2d6ngltua59'
# balance = node.get_balance(script_address)
# params = {
#   "message": {
#     "tx_info": {
#       "address_origin": [
#         script_address,
#         ],
#       "address_destin": [
#         {
#           "address": "addr_test1qqw2zefrz6qrg25ru9mnd50w7m7egvxuwc5t3hrtuxnk2zet6zvkquse655sw7xegn9akwcjgytlfqs2vw2ulenw7y9qmggcvg",  # noqa: E501
#           "amount": {
#                 "quantity": 5000000,
#                 "unit": "lovelace"
#             },
#           "assets": {},
#         },
#       ],
#       "change_address": script_address,
#       "metadata":{
#         "4567":
#             "Retirar fondos del script"
#       },
#       "mint": {
#           "name": "556Prueba",
#           "amount": 45122333365,
#           "policyID": "f2a5629e0c50614a1aa805c56de5537a55957eca4c02f0ad002ba981"
#         },
#       "script_path": './priv/wallets/3multisig/3multisig.script',
#       "witness": witness,
#     }
#   }
# }
# node.build_tx_components(params)

# #########
# # Witnessing the transaction
# #########
# sign_wallets = ['wallet01', 'wallet03']
# for wallet_name in sign_wallets:
#   node.sign_witness(wallet_name)

# node.assemble_tx(sign_wallets)

<<<<<<< HEAD
# #########
# # Submit the transaction
# #########
# node.submit_transaction()
=======
script_address = key.create_address_script(name)
print(script_address)
>>>>>>> remotes/origin/dev
