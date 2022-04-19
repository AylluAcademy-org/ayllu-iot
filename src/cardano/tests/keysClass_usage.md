# Keys class 

### Keys class helps you generate keys and addresses.
One of the major limitations with Cardano-cli is that keys generated are not easy to integrate with wallet keys generate from Yoroi, Eternl, etc.

This class helps you create Keys from mnemonics and generate the equivalent key files like in Cardano-cli. So you can create your own keys and use them from the wallet and from the cli. This is helpful if you are a stake pool operator and you want to manage your keys from any known wallet. 

***

### Basic usage

1. Generating the keys

> You can use the following methods separately but it is recommended that you use <mark>deriveAllKeys()</mark> method to get all the keys with a json file summary. 

Available methods are:

- generate_mnemonic(size)
- deriveRootKey(mnemonic)
- deriveExtendedSigningStakeKey(root_key)
- deriveExtendedSigningPaymentKey(root_key)
- deriveExtendedVerificationPaymentKey(payment_signing_key)
- deriveExtendedVerificationStakeKey(stake_signing_key)
- derivePaymentAddress(payment_verification_key)
- convertPaymentKey(payment_signing_key, name)
- convertStakeSigningKey(stake_signing_key, name)
- deriveBaseAddress(ayment_vkey,stake_vkey, name)
- keyHashing(name)
- deriveAllKeys(size, name)
- generateCardanoKeys(name)
- create_multisig_script(script_name, type, required, hashes)
- create_address_script(script_name)

***

By using the deriveAllKeys method, you can create all the keys with just few lines of code: 

```python
from src.cardano.base import Keys

key= Keys()
wallet_name = 'wallet01'
nmemonic_size = 24
key.deriveAllKeys(nmemonic_size,wallet_name)
```
Above code will return something similar to this:

    ##################################
    Find all the keys and address details in: ./priv/wallets/wallet01/wallet01.json
    ##################################

All the keys will be store at './priv/wallets/<name_provided>

You can take a backup and delete the folder. Store your keys in a private location. This library does not keep any log or backup.

> :warning: **Warning:** Your nmenomics are the most important piece of information and the ultimate way of recovering your keys.

> :memo: **Note:** This libary does not keep backup or logs of any of these files.

> :warning: **Warning:** Keep in mind that if you rerun the above code with the same <mark>wallet_name</mark>, your previously generated keys will be overwritten.  


2. Multisig functionality

This library also provides the functionality to create a multisig script. This is useful when you want provide authorization for transactions from multiple keys.

For more details see: [Multisignatures](https://github.com/input-output-hk/cardano-node/blob/c6b574229f76627a058a7e559599d2fc3f40575d/doc/reference/simple-scripts.md).

For multisig you need multiple wallets that will be allowed to sign the transaction and a script file with the conditions to spend adas from the script address locking the funds. 

The steps are:

    1. Create multiple keys and addresses
    2. Hash the verification keys
    3. Create the script file
    4. Build the script address
    5. Lock funds the script address
    6. Unlock funds from the script address

```python
from src.cardano.base import Keys

key= Keys()
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
```