from src.cardano.base import Keys
from src.cardano.base import Wallet

wallet= Wallet()
key= Keys()

nmemonic = wallet.generate_mnemonic(24)
root_key = key.deriveRootKey(nmemonic)
print(root_key)
stake = key.deriveExtendedSigningStakeKey(root_key)
payment = key.deriveExtendedSigningPaymentKey(root_key)
print(stake, ' ', payment)

payment_public_account_key = key.deriveExtendedVerificationPaymentKey(payment)
stake_public_account_key = key.deriveExtendedVerificationStakeKey(stake)
print(payment_public_account_key, '', stake_public_account_key)

payment_address = key.derivePaymentAddress(payment_public_account_key)
print(payment_address)

# Convert from cardano wallet keys to cardano-cli keys

""" 
Convert payment signing keys
"""
payment_skey, payment_vkey, payment_addr = key.convertPaymentKey(payment)
print(payment_skey, '', payment_vkey ,'',payment_addr)

"""
Convert stake signing keys
"""
stake_skey, stake_vkey, stake_addr = key.convertStakeSigningKey(stake)
print(stake_skey, '', stake_vkey ,'',stake_addr)

base_addr = key.deriveBaseAddress(payment_vkey ,stake_vkey)
print(base_addr)