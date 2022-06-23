# Node class 

### Node class helps you to use Cardano CLI in a simplified manner.
Cardano CLI is the main gate to interact with the Cardano Blockhcain, from creating keys, sending funds and mingting new tokens.

This class helps you build different transactions to submmit into the blockchain. 

***

### Basic usage

1. Query the blockchain

> These are the most simple methods and a quick way to check the status of the node and a confirmation that you can interact with the blockchain. 

Available methods are:

- id_to_address(wallet_id)
- get_txid()
- query_protocol(saving_path)
- query_tip_exec()
- get_transactions(wallet_id)
- get_balance(wallet_id)
- utxo_selection(addr_origin_tx, quantity, deplete)
- tx_min_fee(tx_in_count, tx_out_count)
- sign_witness(signing_key_name)
- create_multisig_script(script_name, type, required, hashes)
- create_policy_id(script_name)
- sign_transaction(wallet_id, policyid)
- submit_transaction(name)
- minting(*args, **kwargs)
- build_tx_components(params)
- assemble_tx (witness_wallet_name_array)

***

1. Minting tokens

In this example we are going to mint a token. The steps are as follows:

    1. Generate keys for minting and for payment (using Keys Class)
    2. Fund the payment address.
    3. Create the Policy script file and the PolicyID
    4. Build, sign and submit the transaction

1. Generate keys for minting and for payment (using Keys Class)

Use the Keys Class to generate keys as explained in keysClass_usage.md file. In this example we are going to generate only the cardano CLI keys (.skey and .vkey) but keep in mind that you cannot generate mnemonics or root keys from these keys so it is recommended that you generate the nmemonics and root key first to then derive the rest of the keys as explained in the keysClass_usage.md file. 

```python
from src.cardano.base import Keys, Node

key = Keys()
node = Node()
wallet_name1 = 'Payment wallet'
result = key.generateCardanoKeys(wallet_name1)

wallet_name2 = 'ForMinting'
result = key.generateCardanoKeys(wallet_name2)

result = node.deriveBaseAddress(wallet_name1)

key_hash = key.keyHashing(wallet_name2)
```

Output: Keys stored in './priv/wallets/ForMinting' under the name 'ForMinting'
Base address: 'addr_test1qrp2m43wryxjm95jhq02q4vg8tjq82k5t6paay87u90xyxz6rf3adxm3anceu8wd3zv4gmr4kl5kl3qth4mlqd8alhls4kpp0t'
Key hash of the verification payment key: '63fa5cac030042139c83d75171af9b349373a21036de6ca9c749ca61'

2. Fund the payment address

After funding there are 2 methods to check the address balance <Mark>get_transactions</Mark> and <Mark>get_balance</Mark>

```python
from src.cardano.base import Node
node = Node()

address = 'addr_test1qrp2m43wryxjm95jhq02q4vg8tjq82k5t6paay87u90xyxz6rf3adxm3anceu8wd3zv4gmr4kl5kl3qth4mlqd8alhls4kpp0t'

transactions = node.get_transactions(wallet_id= address)
print(transactions)
balance = node.get_balance(script_address)
print(balance)
```

3. Create the Policy script file and the PolicyID

```python
from src.cardano.base import Node, Keys

node= Node()

wallet_name2 = 'ForMinting'
key_hash = key.keyHashing(wallet_name2)
script_name = 'ForMinting'
type = ''
required = ''

result = node.create_multisig_script(script_name, type, required, [key_hash])
```
type and required fields are needed for multisig scripts. In this case it is a simple script with only one key.

> Notice that the hash must be passed as an list even if it is only one