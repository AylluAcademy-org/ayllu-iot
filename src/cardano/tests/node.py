from src.cardano.base import Node
from src.cardano.base import Keys

node = Node()
key = Keys()

# address = 'addr_test1qrp2m43wryxjm95jhq02q4vg8tjq82k5t6paay87u90xyxz6rf3adxm3anceu8wd3zv4gmr4kl5kl3qth4mlqd8alhls4kpp0t'

# transactions = node.get_transactions(wallet_id= address)
# print(transactions)
# balance = node.get_balance(address)
# print(balance)

# ##########################################
# wallet_name2 = 'ForMinting'

# key_hash = key.keyHashing(wallet_name2)

# script_name = 'ForMinting'
# type = ''
# required = ''

# result = node.create_multisig_script(script_name, type, required, [key_hash])


#############################################
address_origin = 'addr_test1qpu78mfpzpq2pspecsl496lzzeerlcmwkpl6udd4ny7emwhyze5w4t8hucl0c76k5v90yvjkzyag4l8v3nsau3w4d75q87z5xq'

address_destin = 'addr_test1qzz7l5yx4pvqcd3lgnay95g7mpn4vfce49htshwtpxw3ypyes4gaskwme3lygpq6elm702mfjcyt257lhz6rs80f0x0s50329z'

print(node.get_balance(address_destin))

metadata = {
    "1456": "Hola Mundo"
}

witness = 1

params = {
  "message": {
    "tx_info": {
      "address_origin": address_origin,
      "address_destin": [
        {
          "address": "addr_test1qzz7l5yx4pvqcd3lgnay95g7mpn4vfce49htshwtpxw3ypyes4gaskwme3lygpq6elm702mfjcyt257lhz6rs80f0x0s50329z",  # noqa: E501
          "amount": {
                "quantity": 5000000,
                "unit": "lovelace"
            },
          "assets": {},
        },
      ],
      "change_address": address_origin,
      "metadata": metadata,
      "mint": None,
      "script_path": None,
      "witness": witness,
    }
  }
}

result = node.build_tx_components(**params)
node.sign_transaction('ForMinting')
node.submit_transaction()