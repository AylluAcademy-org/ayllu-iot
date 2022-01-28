import subprocess
from itertools import groupby
from operator import itemgetter
import os
import json
import utils
import random
import requests
import sys

class Node():

    def __init__(self, working_dir):

        with open(working_dir + '/config_file.json') as file:
            params=json.load(file)

        self.CARDANO_NETWORK_MAGIC = params['node']['CARDANO_NETWORK_MAGIC']

        self.CARDANO_CLI_PATH = params['node']['CARDANO_CLI_PATH']

        self.CARDANO_NETWORK = params['node']['CARDANO_NETWORK']

        self.TRANSACTION_PATH_FILE = params['node']['transactions']
        if not os.path.exists(self.TRANSACTION_PATH_FILE):
            os.makedirs(self.TRANSACTION_PATH_FILE)

        self.KEYS_FILE_PATH = params['node']['keys_path']
        if not os.path.exists(self.KEYS_FILE_PATH):
            os.makedirs(self.KEYS_FILE_PATH, exist_ok=True)
        self.URL = params['node']['URL']

    def insert_command(self, index, step, command_string, opt_commands):
        """ function to insert commands to be executed in subprocess"""
        i = 0
        for opt_command in opt_commands:
            command_string.insert(index+i,str(opt_command))
            i += step
        print(command_string)
        return command_string, i

    def id_to_address(self, wallet_id):
        """ Convert id wallet to address"""
        if not wallet_id.startswith('addr' or 'DdzFF'):
            if os.path.exists(self.KEYS_FILE_PATH + '/' + wallet_id):
                with open(self.KEYS_FILE_PATH + '/' + wallet_id + '/' + wallet_id + '.payment.addr','r') as file:
                    address = file.readlines(1)[0]
            else:
                address=''
        else:
            address = wallet_id
        return address

    def query_protocol(self, saving_path=''):
        """Execute query protocol parameters.
        No params needed
        Return: json file with protocol.json parameters"""
        if saving_path == '':
            TRANSACTION_PATH_FILE = self.TRANSACTION_PATH_FILE
        else:
            TRANSACTION_PATH_FILE = saving_path

        command_string = [
            self.CARDANO_CLI_PATH,
            'query', 'protocol-parameters',
            '--out-file', TRANSACTION_PATH_FILE +'/protocol.json']
        if self.CARDANO_NETWORK == 'testnet':
            command_string, index = self.insert_command(3,1,command_string,['--testnet-magic',self.CARDANO_NETWORK_MAGIC])
        subprocess.check_output(command_string)

    def query_tip_exec(self):
        """Executes query tip. 
            No params needed
            Return: json with latest epoch, hash, slot, block, era, syncProgress
        """
        command_string = [
            self.CARDANO_CLI_PATH,
            'query', 'tip']
        if self.CARDANO_NETWORK == 'testnet':
            command_string, index = self.insert_command(3,1,command_string,['--testnet-magic',self.CARDANO_NETWORK_MAGIC])

        rawResult = subprocess.check_output(command_string)
        rawResult = rawResult.decode('utf-8')
        rawResult = json.loads(rawResult)
        return rawResult
        
    def get_transactions(self, wallet_id):
        """
        Get the list of transactions from the given addresses.
        :param address: Cardano Blockchain address or wallet id to search for UTXOs
        :return: ada_transactions, token_transactions
                ada_transactions: list of transactions with lovelace only
                token_transactions: list of transactions including custom tokens
        """
        address = self.id_to_address(wallet_id)
        command_string = [
            self.CARDANO_CLI_PATH,
            'query', 'utxo',
            '--address', address]
        if self.CARDANO_NETWORK == 'testnet':
            command_string, index = self.insert_command(5,1,command_string,['--testnet-magic',self.CARDANO_NETWORK_MAGIC])
        rawTipResult = subprocess.check_output(command_string)
        rawTipResult = rawTipResult.decode('utf-8')

        # Unpacking the results
        transactions = {}
        token_transactions = []
        for line in rawTipResult.splitlines():
            if 'lovelace' in line:
                transaction = {}
                trans = line.split()
                #if only lovelace
                transaction['hash'] = trans[0]
                transaction['id'] = trans[1]
                transaction['amounts'] = []
                tr_amount = {}
                tr_amount['token'] = trans[3]
                tr_amount['amount'] = trans[2]
                transaction['amounts'].append(tr_amount)
                # for each token
                for i in range(0, int((len(trans) - 4) / 3)):
                    tr_amount = {}
                    tr_amount['token'] = trans[3 + i * 3 + 3]
                    tr_amount['amount'] = trans[3 + i * 3 + 2]
                    transaction['amounts'].append(tr_amount)
                token_transactions.append(transaction)
                transactions['transactions'] = token_transactions
        return transactions

    def get_balance(self, wallet_id):
        """ Get the balance in dictionary format at the specified wallet address or from address base if wallet id is provided
            return: balance dictionary listing the balance of the assets contained in the wallet
        """
        # wallet.get_addresses(id)
        wallet_id = self.id_to_address(wallet_id)
        transactions = self.get_transactions(wallet_id)
        balance_dict = {}
        if transactions == {}:
            balance_dict['lovelace']=0
            balance_dict['assets']=0
        else:
            transactions = transactions['transactions']
            amounts = []
            for utxo in transactions:
                for amount in utxo['amounts']:
                    amounts.append(amount)
                amounts = sorted(amounts, key = itemgetter('token'))
                for key, value in groupby(amounts, key = itemgetter('token')):
                    balance = 0
                    for k in value:
                        balance = balance + int(k['amount'])
                    balance_dict[key]=balance
                    print(f'Total balance of "{key}" is "{balance}"')

        return balance_dict

    def utxo_selection(self, addr_origin_tx, quantity, deplete):
        """ Function based on the coin selection algorithm to properly handle the use of utxos in the wallet. 
        Rules are:
        1. If any of your UTXO matches the Target it will be used.
        2. If the "sum of all your UTXO smaller than the Target" happens to match the Target, they will be used. (This is the case if you sweep a complete wallet.)
        3. If the "sum of all your UTXO smaller than the Target" doesn't surpass the target, the smallest UTXO greater than your Target will be used.
        4. Else Bitcoin Core does 1000 rounds of randomly combining unspent transaction outputs until their sum is greater than or equal to the Target. If it happens to find an exact match, it stops early and uses that.
            Otherwise it finally settles for the minimum of

                the smallest UTXO greater than the Target
                the smallest combination of UTXO it discovered in Step 4.

        https://github.com/bitcoin/bitcoin/blob/3015e0bca6bc2cb8beb747873fdf7b80e74d679f/src/wallet.cpp#L1276
        https://bitcoin.stackexchange.com/questions/1077/what-is-the-coin-selection-algorithm
        """
        #Applying the coin selection algorithm
        minUTXO = 1000000
        TxHash = []
        TxHash_lower = []
        amount_lower = []
        TxHash_greater = []
        amount_greater = []
        utxo_found = False
        transactions = addr_origin_tx['transactions'][:]
        for utxo in transactions:
            for amount in utxo['amounts']:
                if amount['token']=='lovelace': 
                    if deplete:
                        TxHash.append('--tx-in')
                        TxHash.append([utxo['hash'] + '#' + utxo['id']])
                        amount_equal = int(amount['amount'])
                        utxo_found = True
                        break
                    if int(amount['amount']) == quantity:
                        TxHash.append('--tx-in')
                        TxHash.append(utxo['hash'] + '#' + utxo['id'])
                        amount_equal = int(amount['amount'])
                        utxo_found = True
                        break
                    elif int(amount['amount']) < quantity + minUTXO:
                        TxHash_lower.append(utxo['hash'] + '#' + utxo['id'])
                        amount_lower.append(int(amount['amount']))
                    elif int(amount['amount']) > quantity + minUTXO:
                        TxHash_greater.append(utxo['hash'] + '#' + utxo['id'])
                        amount_greater.append(int(amount['amount']))

        if not utxo_found:
            if sum(amount_lower) == quantity:
                TxHash.append('--tx-in')
                TxHash.append(TxHash_lower)
                amount_equal = sum(amount_lower)
            elif sum(amount_lower) < quantity:
                if amount_greater == []:
                    TxHash = []
                    amount_equal = 0
                amount_equal = min(amount_greater)
                index = [i for i, j in enumerate(amount_greater) if j == amount_equal][0]
                TxHash.append('--tx-in')
                TxHash.append(TxHash_greater[index])
            else:
                utxo_array = []
                amount_array = []
                for _ in range(999):
                    index_random = random.randint(0,len(transactions)-1)
                    utxo = transactions.pop(index_random)
                    utxo_array.append('--tx-in')
                    utxo_array.append(utxo['hash'] + '#' + utxo['id'])
                    for amount in utxo['amounts']:
                        if amount['token']=='lovelace': 
                            amount_array.append(int(amount['amount']))
                    if sum(amount_array) >= quantity + minUTXO:
                        amount_equal = sum(amount_array)
                        break
                TxHash = utxo_array

        return TxHash, amount_equal

    def tx_min_fee(self, tx_in_count,tx_out_count):
        """Calculates the expected min fees . 
            params:
                tx_in_count: number of utxo in input
                tx_out_count: number of utxo in output
            Return: Min fees value
        """
        command_string = [
            self.CARDANO_CLI_PATH,
            'transaction', 'calculate-min-fee',
            '--tx-body-file', self.TRANSACTION_PATH_FILE + '/tx.draft',
            '--tx-in-count', tx_in_count,
            '--tx-out-count', tx_out_count,
            '--witness-count', str(1),
            # '--byron-witness-count', str(0),
            '--protocol-params-file', self.TRANSACTION_PATH_FILE + '/protocol.json']
        if self.CARDANO_NETWORK == 'testnet':
            command_string, index = self.insert_command(11,1,command_string,['--testnet-magic',self.CARDANO_NETWORK_MAGIC])
        rawResult = subprocess.check_output(command_string)
        rawResult = rawResult.split()
        rawResult = rawResult[0]
        return rawResult

    def build_raw_tx(self, TxHash_array, addr_array, fee, metadata_json_file, mint, script):
        """
        Transaction build raw.
        :param: 
            TxHash: utxo hash of the origin address
            addr: address of the destin wallet
            fee: calculated fees for the transaction
            metadata_json_file: path to the json file with metadata
            mint: array that includes the mint balance of the token to be minted
            script: path to the policy script
        :return: tx_build file
        """
        command_string = [
            self.CARDANO_CLI_PATH,
            'transaction', 'build-raw',
            '--fee', str(fee),
            '--out-file', self.TRANSACTION_PATH_FILE + '/tx.draft']
        i = 0
        command_string, index = self.insert_command(3+i,1,command_string,TxHash_array)
        i = i + index
        command_string, index = self.insert_command(3+i,1,command_string,addr_array)
        i = i + index
        metadata = []
        if metadata_json_file != '':
            metadata.append('--metadata-json-file')
            metadata.append(metadata_json_file)
            command_string, index = self.insert_command(3+i,1,command_string,metadata)
        i = i + index
        mint_array = []
        if mint != []:
            mint_array.append(mint)
            mint_array.append('--minting-script-file')
            mint_array.append(script)
            command_string, index = self.insert_command(3+i,1,command_string,mint_array)

        subprocess.check_output(command_string)

    def create_minting_policy(self, wallet_id):
        """Function to create minting script, minting key and policyID
        params:wallet id
        return: policyID 
        """

        path = self.KEYS_FILE_PATH + '/' + wallet_id + '/' + 'minting/'
        if not os.path.exists(path):
            os.makedirs(path)
        
        # Generate key pairs for minting associated to specific policy script
        command_string = [
            'cardano-cli', 'address', 'key-gen', '--verification-key-file', path + wallet_id + '.policy.vkey',
        '--signing-key-file', path + wallet_id + '.policy.skey'
        ]
        subprocess.run(command_string)

        #Create policy script and save file policy.script
        command_string = [
        'cardano-cli', 'address', 'key-hash', '--payment-verification-key-file', path + wallet_id + '.policy.vkey'
        ]
        output = subprocess.Popen(command_string,stdout=subprocess.PIPE)

        policy_script = {
            "keyHash": str(output.communicate()[0].decode('utf-8')).rstrip(),
            "type": "sig"
        }

        with open(path + '/' + wallet_id + '.policy.script','w') as file:
            json.dump(policy_script, file, indent=4, ensure_ascii=True)

        # Generate policyID from the policy script file
        command_string = [
        'cardano-cli', 'transaction', 'policyid', '--script-file', path + wallet_id + '.policy.script'
        ]
        output = subprocess.Popen(command_string,stdout=subprocess.PIPE)
        policyID = str(output.communicate()[0].decode('utf-8')).rstrip()
        utils.save_files(path, wallet_id + '.policyID',str(policyID))
        return policyID

    def sign_transaction(self, wallet_id, policyid):
        """Sign the transaction based on tx_raw file.
            For the time being not handling multi-witness"""
        command_string = [
            self.CARDANO_CLI_PATH,
            'transaction', 'sign',
            '--tx-body-file', self.TRANSACTION_PATH_FILE + '/tx.draft',
            '--signing-key-file', self.KEYS_FILE_PATH + '/' + wallet_id + '/' + wallet_id + '.payment.skey',
            # '--testnet-magic', str(CARDANO_NETWORK_MAGIC),
            '--out-file', self.TRANSACTION_PATH_FILE + '/tx.signed']
        i = 0
        mint_array = []
        if policyid != '':
            mint_array.append('--signing-key-file')
            mint_array.append(self.KEYS_FILE_PATH + '/' + wallet_id + '/minting/' + policyid + '.policy.skey')
            command_string, index = self.insert_command(7+i,1,command_string,mint_array)  
            i = i + index       
        if self.CARDANO_NETWORK == 'testnet':
            command_string, index = self.insert_command(7+i,1,command_string,['--testnet-magic',self.CARDANO_NETWORK_MAGIC])
        
        subprocess.check_output(command_string)
    
    def submit_transaction(self):
        """Submit the transaction"""
        command_string = [
            self.CARDANO_CLI_PATH,
            'transaction', 'submit',
            '--tx-file', self.TRANSACTION_PATH_FILE + '/tx.signed']
        if self.CARDANO_NETWORK == 'testnet':
            command_string, index = self.insert_command(5,1,command_string,['--testnet-magic',self.CARDANO_NETWORK_MAGIC])
        
        rawResult= subprocess.check_output(command_string)
        print(rawResult)

    def transactions(self, params):
        """Handle transactions specially minting. 
            Params:
            params   = {     
            "message": {
            "tx_info": {
            "mint": {
                "id": id,
                "metadata": metadata,
                "address": "addr_test1qzfxu7zhedzn86v95k84m7t94z3eek99al4xlyahkuw8ammjkcctzvtrmt0chuqgaphal08kaqhn0gn295v7wefe95eqvh5ndl",
                "tokens": [
                {
                    "name": "miprueba",
                    "amount": 47,
                    "policyID": {}
                }
                ]
            }
            }
        }
        }
            Return: 
        """
        data = {}
        id = params['message']['tx_info']['id']
        data['payments'] = params['message']['tx_info']['payments']
        data['metadata'] = params['message']['tx_info']['metadata']
        data['withdrawal']='self'      
        random_coin_selection_file = Wallet.random_coin_selection(self, id, data)
        print(random_coin_selection_file)
        
        deplete = False
        quantity_input_array = []

        for inputs in random_coin_selection_file['inputs']:
            addr_origin = inputs['address']
            addr_origin_tx = self.get_transactions(addr_origin)
            quantity_input = inputs['amount']['quantity']
            quantity_input_array.append(quantity_input)
            derivation_path = inputs['derivation_path']
            utils.topayment_wallet(id,derivation_path)
            TxHash_in_array, amount_equal_array = self.utxo_selection(addr_origin_tx,quantity_input,deplete)
            
        print(TxHash_in_array, amount_equal_array)

        addr_output_array = []
        quantity_output_array = []
        for outputs in random_coin_selection_file['outputs']:
            addr_destination = outputs['address']
            quantity_output = outputs['amount']['quantity']
            quantity_output_array.append(quantity_output)
            addr_output_array.append('--tx-out')
            if inputs['assets'] != []:
                policyid_output = inputs['assets']['policy_id']
                asset_name_output = inputs['assets']['name']
                asset_quantity_output = inputs['assets']['quantity']
                addr_output_array.append(addr_destination + '+' + str(quantity_output) + '+' + str(asset_quantity_output) + ' ' + str(policyid_output) + '.' + str(asset_name_output))
            
            else:
                addr_output_array.append(addr_destination + '+' + str(quantity_output))
        
        for changes in random_coin_selection_file['change']:
            addr_change = changes['address']
            quantity_change = changes['amount']['quantity']
            quantity_output_array.append(quantity_change)
            addr_output_array.append('--tx-out')
            if inputs['assets'] != []:
                policyid_change = inputs['assets']['policy_id']
                asset_name_change = inputs['assets']['name']
                asset_quantity_change = inputs['assets']['quantity']
                addr_output_array.append(addr_change + '+' + str(quantity_change) + '+' + str(asset_quantity_change) + ' ' + str(policyid_change) + '.' + str(asset_name_change))
            else:
                addr_output_array.append(addr_change + '+' + str(quantity_change))
        
        fee = sum(quantity_input_array) - sum(quantity_output_array)

        # Check if minting tokens as part of the transaction
        mint = []
        script_path = ''
        mint_info = params['message']['tx_info']['mint']
        if mint_info != []:
            # Reading param and setting variables
            for token_info in mint_info:
                tokenname = token_info['name']
                tokenamount_mint = token_info['amount']
                policyid = token_info['policyID']
                script_path = self.KEYS_FILE_PATH + '/' + id + '/minting/' + id + '.policy.script'

                if policyid == '':
                    # Create keys and policy IDs
                    policy_script, policyid = utils.create_minting_policy(id)
                else:
                    policyid = token_info['policyID']
                    with open(script_path) as file:
                        policy_script = json.load(file)

            
            mint = '--mint=' + str(tokenamount_mint) + ' ' + str(policyid) + '.' + str(tokenname)

        metadata = params['message']['tx_info']['metadata']
        metadata_json_file = utils.save_metadata(self.TRANSACTION_PATH_FILE, metadata)
                
        #Create the tx_raw file
        self.build_raw_tx(TxHash_in_array, addr_output_array, fee, metadata_json_file, mint, script_path)

        policyid_mint = ''
        self.sign_transaction(id,policyid_mint)
        self.submit_transaction()

    def minting(self, params):
        id = params['message']['tx_info']['id']
        addresses = Wallet.get_addresses(self, id, 'used')
        for address in addresses:
            address_origin = address['id']
            derivation_path = address['derivation_path']
            addr_origin_tx = self.get_transactions(address_origin)
            if addr_origin_tx != {}:
                addr_origin_balance = self.get_balance(address_origin)
                if addr_origin_balance['lovelace'] > 2_300_000:
                    break
        utils.topayment_wallet(id,derivation_path)
        
        if addr_origin_balance != {}:


            # Check if minting tokens as part of the transaction
            script_path = ''

            deplete = False
            addr_output_array = []

            mint_info = params['message']['tx_info']['mint']
            mint_string = ''
            policyid = ''
            for token_info in mint_info:
                asset_name = token_info['name']
                asset_quantity = int(token_info['amount'])
                policyid = token_info['policyID']

                if policyid == '':
                    # Create keys and policy IDs
                    policy_script, policyid = utils.create_minting_policy(id)
                    script_path = self.KEYS_FILE_PATH + '/' + id + '/minting/' + policyid + '.policy.script'
                else:
                    policyid = token_info['policyID']
                    script_path = self.KEYS_FILE_PATH + '/' + id + '/minting/' + policyid + '.policy.script'
                    with open(script_path) as file:
                        policy_script = json.load(file)
                
                if policyid + '.' + asset_name in addr_origin_balance:
                    asset_balance = addr_origin_balance[policyid + '.' + asset_name]
                else:
                    asset_balance = 0
                
                minUTXOValue = 1_000_000
                target_calculated = minUTXOValue + 300000
                asset_balance = asset_balance + asset_quantity

                asset_mint_string = str(asset_quantity) + ' ' + str(policyid) + '.' + str(asset_name)

                mint_string = mint_string  + asset_mint_string
            
            asset_string = ''
            for key, value in addr_origin_balance.items():
                if key != 'lovelace':
                    asset_string = asset_string + ' + ' + str(value) + ' ' + str(key)

            asset_string = asset_string + '+' + mint_string
            mint_string = '--mint=' + mint_string

            addr_output_array.append('--tx-out')
            
            addr_output_array.append(address_origin + '+' + str(0) + asset_string)

            deplete = False
            TxHash_in, amount_equal = self.utxo_selection(addr_origin_tx,target_calculated,deplete)
            
            metadata = params['message']['tx_info']['metadata']
            metadata_json_file = utils.save_metadata(self.TRANSACTION_PATH_FILE, metadata)
            
            ###########################
            # Section to calculate min fees
            ###########################

            #Create the tx_raw file to calculate the min fee
            self.build_raw_tx(TxHash_in, addr_output_array, 0, metadata_json_file, mint_string, script_path)
            #Calculate min fees based on previously tx_raw file
            fee = self.tx_min_fee(str(len(TxHash_in)),str(len(addr_output_array)))
            fee = int(fee.decode('utf-8'))
            print(fee)

            ###########################
            # Section to build the actual transaction including fees
            ###########################
            addr_output_array = []
            target = amount_equal - fee
            addr_output_array.append('--tx-out')
            addr_output_array.append(address_origin + '+' + str(target) + asset_string)

            # #Create the tx_raw file with the fees included
                
            self.build_raw_tx(TxHash_in, addr_output_array, fee, metadata_json_file, mint_string, script_path)

            print("################################")

            self.sign_transaction(id,policyid)
            self.submit_transaction()
            mint = {
                "message":{
                "policyid": policyid,
                "asset_name": asset_name,
                "quantity_mint": asset_quantity,
                "fees": fee,
                "destination_address": address_origin,
                "metadata": metadata,
                "policy_script": policy_script,
                },
                "code": "Mint¡¡"
            }
        else:
            mint = {
                'message':"Not enough funds for minting",
                'code': "Not enough funds for minting",
            }
        
        return mint

       

class Wallet():

    def __init__(self, working_dir):
        with open(working_dir + '/config_file.json') as file:
            params=json.load(file)
        
        self.URL = params['node']['URL']
    
    def list_wallets(self):
        """Return a list of known wallets, ordered from oldest to newest.
        No params needed"""
        request_status_url = self.URL
        wallets_info = requests.get(request_status_url)
        return wallets_info.json()

    def generate_mnemonic(self, size=24):
        """Create mnemonic sentence (list of mnemonic words)
        Input: size number of words: 24 by default"""
        try:
            # Generate mnemonic
            command_string = [
                'cardano-wallet', 'recovery-phrase', 'generate',
                '--size', str(size)
            ]
            mnemonic = subprocess.check_output(command_string)
            mnemonic = mnemonic.decode('utf-8')
            mnemonic = mnemonic.split()
            return mnemonic

        except OSError as e:
            print("Execution failed:", e, file=sys.stderr)

    def create_wallet(self, name, passphrase, mnemonic):
        """Create or restore wallet
        Inputs: name, passphrase and mnemonic sentence
        Return: json with status of the wallet"""
        data = {
            'name': name,
            'mnemonic_sentence':mnemonic,
            'passphrase': passphrase
        }
        
        # Create wallet
        r = requests.post(self.URL,json=data)
        return r.json()

    def wallet_info(self, id):
        """ Info of the wallet
        Inputs: Id of the wallet
        Return json with status of the wallet with info like lovelace and assets balance, delegation status, etc"""
        request_status_url = self.URL + id
        wallet_info = requests.get(request_status_url)
        return wallet_info.json()

    def get_addresses(self, id,addr_state):
        """Get only unused addresses for specific wallet
        Inputs: Id of the wallet, addr_state: used, unused, all
        """
        if addr_state == 'used':
            #Get only used addresses
            request_address_url = self.URL + id + '/addresses?state=used'
        elif addr_state == 'unused':
            #Get only unused addresses
            request_address_url = self.URL + id + '/addresses?state=unused'
        else: 
            #Get only all addresses
            request_address_url = self.URL + id + '/addresses'

        addresses = requests.get (request_address_url)
        return addresses.json()

    def delete_wallet(self, id):
        """Delete wallet 
        Inputs: Id of the wallet
        """
        request_status_url = self.URL + id
        r = requests.delete(request_status_url)
        print(r.status_code)
        if r.status_code==204:
            r={
                'message':"wallet succesfully deleted",
                'code': "wallet_succesfully_deleted",
            }
        return r

    def min_fees(self, id, data):
        """ Estimate min fees for the transaction
        Inputs: Id of the wallet
                data with details of the transactio like metadata, address to, amount, etc
        Return: estimated_min, estimated_max, minimum_coins, deposit"""

        data["time_to_live"]={
                        "quantity": 10,
                        "unit": "second"
                        }
        data["withdrawal"]="self"
        request_address_url = self.URL + id + '/payment-fees'
        r = requests.post(request_address_url, json=data)
        r = r.json()
        return r

    def send_transaction(self, id, data):
        """Create, sign and submmit the transaction
        Inputs: Id of the wallet
                data with details of the transactio like metadata, address to, amount, etc
        Return: json with details of the transaction and the status
        """
        request_address_url = self.URL + id + '/transactions'
        r = requests.post(request_address_url, json=data)
        r = r.json()
        return r

    def confirm_transaction(self, id):
        """Lists all incoming and outgoing wallet's transactions.
        Inputs: Id of the wallet
        Return: json with details of the transaction and the status """
        request_address_url = self.URL + id + '/transactions'
        r = requests.get(request_address_url)
        r = r.json()
        return r
    
    def confirm_transaction_by_tx(self, id, tx_id):
        """Lists all incoming and outgoing wallet's transactions.
        Inputs: Id of the wallet
        Return: json with details of the transaction and the status """
        request_address_url = self.URL + id + '/transactions/' + tx_id
        r = requests.get(request_address_url)
        r = r.json()
        return r

    def mint_token(self, id, mint_burn):
        """Not used at the moment in this API. For minting use the node class transactions function"""
        request_address_url = self.URL + id + '/assets'
        r = requests.post(request_address_url,mint_burn)
        r = r.json()
        return r

    def assets_balance(self, id):
        """ List all assets associated with the wallet, and their metadata if known.
            An asset is associated with a wallet if it is involved in a transaction of the wallet.
        Inputs: Id of the wallet
        Return: json with the policyid, asset name, fingerprint and metadata
        """
        request_address_url = self.URL + id + '/assets'
        r = requests.get(request_address_url)
        r = r.json()
        return r

    def random_coin_selection(self, id, data):
        """Select coins to cover the given set of payments
        Inputs: Id of the wallet
            data with list of payments, withdrawal and metadata
        Return: list of transaction inputs and a list of target outputs with amount specified and
        a list of transacion change outputs
        """

        request_address_url = self.URL + id + '/coin-selections/random'
        r = requests.post(request_address_url, json=data)

        r = r.json()
        return r

class IOT(Node, Wallet):
    def __init__(self, working_dir) -> None:
        super().__init__(working_dir)

    
    def message_treatment(self, obj, client_id):

        """Main function that receives the object from the pubsub and defines which execution function to call"""
        main ={
            'client_id': client_id
        }

        if obj[0]['cmd_id'] == 'query_tip':
            print('Executing query tip')
            result = Node.query_tip_exec(self)
            main.update(result)
        
        elif obj[0]['cmd_id'] == 'generate_new_mnemonic_phrase':
            print('Executing generate_new_mnemonic_phrase')
            size = obj[0]['message']['size']
            mnemonic = Wallet.generate_mnemonic(self, size)
            main['wallet_mnemonic']=mnemonic
    
        elif obj[0]['cmd_id'] == 'generate_wallet':
            print('Executing generate wallet')
            name = obj[0]['message']['wallet_name']
            passphrase = obj[0]['message']['passphrase']
            mnemonic = obj[0]['message']['mnemonic']

            wallet_status = Wallet.create_wallet(self, name, passphrase, mnemonic)
            main['wallet_status']=wallet_status
            id = wallet_status['id']
            utils.towallet(id, mnemonic)

            address = Wallet.get_addresses(self, wallet_status['id'], 'unused')
            main['address']=address

        elif obj[0]['cmd_id'] == 'wallet_info':
            print('Executing wallet info')
            id = obj[0]['message']['id']
            wallet_info = Wallet.wallet_info(self, id)
            main['wallet_info']=wallet_info
            address = Wallet.get_addresses(self, id, 'unused')
            main['address']=address
        
        elif obj[0]['cmd_id'] == 'min_fees':
            print('Executing min fees')
            id = obj[0]['message']['id']
            tx_info = obj[0]['message']['tx_info']
            tx_result = Wallet.min_fees(self, id, tx_info)
            main['min_fees']= tx_result
        
        elif obj[0]['cmd_id'] == 'send_transaction':
            print('Executing send transaction')
            id = obj[0]['message']['id']
            tx_info = obj[0]['message']['tx_info']
            tx_info["time_to_live"]={
                            "quantity": 60,
                            "unit": "second"
                            }
            tx_info["withdrawal"]="self"
            print(tx_info)
            tx_result = Wallet.send_transaction(self, id, tx_info)
            main['tx_result']= tx_result
        
        elif obj[0]['cmd_id'] == 'confirm_transaction':
            print('Executing confirmation of all the transactions')
            id = obj[0]['message']['id']
            transactions = Wallet.confirm_transaction(self, id)
            main['tx_result'] = {
                'transactions': transactions
            }
        
        elif obj[0]['cmd_id'] == 'confirm_transaction_by_tx':
            print('Executing confirmation of the transaction')
            id = obj[0]['message']['id']
            tx_id = obj[0]['message']['tx_id']
            transactions = Wallet.confirm_transaction_by_tx(self, id, tx_id)
            main['tx_result'] = {
                'transactions_by_tx': transactions
            }
        
        elif obj[0]['cmd_id'] == 'send_transaction_2':
            print('Executing send_transaction_2')

            Node.transactions(self, obj[0])
        
        elif obj[0]['cmd_id'] == 'delete_wallet':
            print('Executing wallet deletion')
            id = obj[0]['message']['id']
            print(id)
            wallet_info = Wallet.delete_wallet(self, id)
            main['tx_result'] = wallet_info

        elif obj[0]['cmd_id'] == 'assets_balance':
            print('Executing assets info')
            id = obj[0]['message']['id']
            assets_balance = Wallet.assets_balance(self, id)
            main['assets_balance']=assets_balance
        
        elif obj[0]['cmd_id'] == 'random_coin_selection':
            print('Executing random coin selection')
            id = obj[0]['message']['id']
            tx_info = obj[0]['message']['tx_info']
            tx_info["withdrawal"]="self"
            random_coin_selection = Wallet.random_coin_selection(self, id, tx_info)
            main['random_coin_selection']=random_coin_selection

        elif obj[0]['cmd_id'] == 'mint_asset':
            print('Executing mint asset')

            mint = Node.minting(self, obj[0])
            main['tx_result'] = mint

        elif obj[0]['cmd_id'] == 'get_transactions':
            print('Executing get transactions')
            
            transactions = Node.get_transactions(self,obj[0]['message']['address'])
            main['tx_result'] = transactions

        elif obj[0]['cmd_id'] == 'get_balance':
            print('Executing get balance')

            balance = Node.get_balance(self,obj[0]['message']['address'])
            main['tx_result'] = {
                'balance': balance
            }

        obj.pop(0)
        return main