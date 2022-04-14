from src.cardano.base import Keys
from src.cardano.base import Wallet

key= Keys()

# keys1 = key.deriveAllKeys(24,'wallet01')

# script={
#     "keyHash": keys1['hash_verification_key'],
#     "type": "sig"
# }
# multisig_script = {
#     "type": "all",
#     "scripts": [script]
# }
# print(multisig_script)

output = key.generateCardanoKeys('','policy')

