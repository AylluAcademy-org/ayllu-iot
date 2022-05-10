# Keys class 

### Keys class helps you generate keys and addresses.
One of the major limitations with Cardano-cli is that keys generated are not easy to integrate with wallet keys generated from Yoroi, Eternl, etc.

This class helps you create Keys from mnemonics and generate the equivalent key files like in Cardano-cli. So you can create your own keys and use them from the wallet and from the cli. This could be useful to anyone who wants to keep track of generated keys from CLI in commercial wallets.

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

All keys will be store at './priv/wallets/<name_provided>

You can take a backup and delete the folder. Store your keys in a private location. The script does not keep any additional log or backup.

> :warning: **Warning:** Your nmenomics are the most important piece of information and the ultimate way of recovering your keys.

> :memo: **Note:** This libary does not keep backup or logs of any of these files after the initial creation.

> :warning: **Warning:** Keep in mind that if you rerun the above code with the same <mark>wallet_name</mark>, your previously generated keys will be overwritten.  


2. Multisig functionality

This library also provides the functionality to create a multisig script. This is useful when you want to provide authorization for transactions from multiple keys.

For more details see: [Multisignatures](https://github.com/input-output-hk/cardano-node/blob/c6b574229f76627a058a7e559599d2fc3f40575d/doc/reference/simple-scripts.md).

For multisig you need multiple wallets that will be allowed to sign the transaction (witness) and a script file with the conditions to spend the ADAs from the script address which locks the funds. 

In some of the following steps, we used the Node Class available in this library to sign and submit the transaction into Cardano Blockchain. For more details using the Node Class refer to NodeClass_usage.md file.

The steps are:

    1. Create multiple keys and addresses
    2. Hash the verification keys
    3. Create the script file
    4. Build the script address
    5. Lock funds in the script address
    6. Confirm the reception of the ADA by querying the script address
    7. Build transaction to send funds from script address to any address
    8. Witness and sign the transaction with the require keys (i.e. at least 2 signing keys)
    9. Submit the transaction

Steps 1, 2, 3 and 4 can be done with the following code

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
scriptName = '3multisig'
multisig_script = key.create_multisig_script(scriptName, type, required, keyHashes)

script_address = key.create_address_script(scriptName)
print(script_address)
```
> This example is generating 3 keys from the same instance. In a real example, any key should be generated individually. Then the script file only needs the address public hash from each individual key to build the script. 

At the end of these steps, 3 keys, 1 script file and 1 script address associated with the script were generated.

5. Lock funds in the script address. If in testnet, faucet can be used to lock some funds.

6. Once ADA is sent to the script address, you can query the address to confirm the reception of the ADAs.

```python
from src.cardano.base import Node

script_address = 'addr_test1wq9hxaynns7n349gdxwu375twnweqqy8vngnnhqhx43gutg6zls8t'

transactions = node.get_transactions(wallet_id= script_address)
print(transactions)
balance = node.get_balance(script_address)
print(balance)
```
You can use <Mark>get_transactions</Mark> or <Mark>get_balance</Mark> from the Node class.
The get transactions method from the Node class returns a json response with the address balance.

7. Build transaction to send funds from script address to any address

```python
from src.cardano.base import Node
script_address = 'addr_test1wq9hxaynns7n349gdxwu375twnweqqy8vngnnhqhx43gutg6zls8t'
destin_address = 'addr_test1qzmuq5ymy58emta7lwzr4sgrpyp7679svq62ltltu9nsgla0yzn06hf399g6wmcqce90gxqujpzu7duaenk2t2vy3gjspdsx02'
quantiy = 5000000
change_address = script_address
metadata = {}
mint = {}
script_path = './priv/wallets/3multisig/3multisig.script'
witness = 2

params = {
  "message": {
    "tx_info": {
      "address_origin": [
        script_address,
        ],
      "address_destin": [
        {
          "address": destin_address,
          "amount": {
                "quantity": quantity,
                "unit": "lovelace"
            },
          "assets": {},
        },
      ],
      "change_address": change_address,
      "metadata": metadata,
      "mint": mint,
      "script_path": script_path,
      "witness": witness,
    }
  }
}
node.build_tx_components(params)
```
At the end of this command, the transaction file is created. This file is stored in ./priv/transactions/tx.draft

8. Witness and sign the transaction with at least 2 signing keys

```python
from src.cardano.base import Node
sign_wallets = ['wallet01', 'wallet03']
for wallet_name in sign_wallets:
  node.sign_witness(wallet_name)

node.assemble_tx(sign_wallets)
```
> This example is signing the transaction file with 2o3 keys from the same instance. In a real example, any key should sign individually the transaction file, previously shared. Then each signed transaction file should be shared to run the <Mark>assemble_tx()</Mark> which finally generates the tx.signed file to be submitted on-chain. 


The file is sotred in ./priv/transactions/tx.signed

9. Submit the transaction

```python
from src.cardano.base import Node
node.submit_transaction()
```