# General imports
import os
import subprocess
import json

# Module imports
from src.utils.data_utils import load_configs
from src.utils.path_utils import save_file, validate_path, remove_folder, \
    create_folder, remove_file


class Cardano:

    """
    Class for Node object. Contains all the basic functions for interactions
    with cardano-cli excluding those competent to Wallet.

    Attributes
    ----------
    config_path: str, default=CARDANO_CONFIGS
        Configurations for interacting with Cardano node. Default configuration
        follow our node setup, but it is advisable to be modified based on your
        system needs.
    """

    def __init__(self, config_path):
        params = load_configs(config_path, False)

        self.CARDANO_NETWORK_MAGIC = params['node']['CARDANO_NETWORK_MAGIC']
        self.CARDANO_CLI_PATH = params['node']['CARDANO_CLI_PATH']
        self.CARDANO_NETWORK = params['node']['CARDANO_NETWORK']
        self.TRANSACTION_PATH_FILE = params['node']['TRANSACTION_PATH_FILE']
        self.KEYS_FILE_PATH = params['node']['KEYS_FILE_PATH']
        self.URL = params['node']['URL']

        _temp_dirs = [validate_path(folder, True) for folder in
                      [self.TRANSACTION_PATH_FILE, self.KEYS_FILE_PATH]]
        _is_missing = [p for p in _temp_dirs if not os.listdir(p)]

        if _is_missing:
            remove_folder(_is_missing)
            create_folder(_is_missing)

    def towallet(self, wallet_id, mnemonic):
        """
        Function to ...
        """
        try:
            ################################
            # generating additional keys before the actual creation
            ################################
            # Save temp mnemonic
            content = ' '.join(mnemonic)
            path = self.KEYS_FILE_PATH + '/' + wallet_id + '/'
            temp_mnemonic = wallet_id + '.temp_mnemonic'
            save_file(path, temp_mnemonic, content)

            # Generate master key
            output = self.cat_files(path, temp_mnemonic)
            command_string = [
                'cardano-address', 'key', 'from-recovery-phrase', 'Shelley'
            ]
            output2 = subprocess.Popen(
                command_string, stdin=output.stdout, stdout=subprocess.PIPE)
            # output.stdout.close()

            content = output2.communicate()[0].decode('utf-8')
            # Save temp private keys files
            save_file(path, wallet_id + '.root.prv', str(content))
            # Delete file mnemonic
            remove_file(path, temp_mnemonic)

            output = self.cat_files(path, wallet_id + '.root.prv')
            # Generate stake key
            command_string = [
                'cardano-address', 'key', 'child', '1852H/1815H/0H/2/0'
            ]
            output3 = subprocess.Popen(
                command_string, stdin=output.stdout, stdout=subprocess.PIPE)
            # output.stdout.close()
            # Generate payment key
            output = self.cat_files(path, wallet_id + '.root.prv')
            command_string = [
                'cardano-address', 'key', 'child', '1852H/1815H/0H/0/0'
            ]
            output4 = subprocess.Popen(
                command_string, stdin=output.stdout, stdout=subprocess.PIPE)
            # output.stdout.close()
            stake_xprv = output3.communicate()[0].decode('utf-8')
            payment_xprv = output4.communicate()[0].decode('utf-8')
            # output3.stdout.close()
            # output4.stdout.close()

            # Save payment key into file
            save_file(path, wallet_id + '.stake.xprv', str(stake_xprv))
            save_file(path, wallet_id + '.payment.xprv', str(payment_xprv))

            # Generate payment verification key xpub
            output = self.cat_files(path, wallet_id + '.payment.xprv')
            command_string = [
                'cardano-address', 'key', 'public', '--with-chain-code'
            ]
            output1 = subprocess.Popen(
                command_string, stdin=output.stdout, stdout=subprocess.PIPE)
            # output.stdout.close()
            payment_xpub = output1.communicate()[0].decode('utf-8')
            save_file(path, wallet_id + '.payment.xpub', str(payment_xpub))

            # Generate payment address from verification key
            output = self.cat_files(path, wallet_id + '.payment.xprv')
            command_string = [
                'cardano-address', 'address', 'payment', '--network-tag',
                self.CARDANO_NETWORK]
            output1 = subprocess.Popen(
                command_string, stdin=output.stdout, stdout=subprocess.PIPE)
            # output.stdout.close()
            payment_addr = output1.communicate()[0].decode('utf-8')
            save_file(path, wallet_id + '.payment.addr', str(payment_addr))

            # Convert cardano-addresses extended signing keys to corresponding
            # Shelley-format keys.

            command_string = [
                'cardano-cli', 'key', 'convert-cardano-address-key',
                '--shelley-payment-key', '--signing-key-file',
                path + wallet_id + '.payment.xprv', '--out-file', path + wallet_id + '.payment.skey']
            subprocess.run(command_string)
            command_string = [
                'cardano-cli', 'key', 'convert-cardano-address-key',
                '--shelley-stake-key', '--signing-key-file',
                path + wallet_id + '.stake.xprv', '--out-file', path + wallet_id + '.stake.skey'
            ]
            subprocess.run(command_string)

            # Get verification keys from signing keys.
            command_string = [
                'cardano-cli', 'key', 'verification-key', '--signing-key-file',
                path + wallet_id + '.stake.skey',
                '--verification-key-file', path + wallet_id + '.stake.evkey'
            ]
            subprocess.run(command_string)
            command_string = [
                'cardano-cli', 'key', 'verification-key', '--signing-key-file',
                path + wallet_id + '.payment.skey',
                '--verification-key-file', path + wallet_id + '.payment.evkey'
            ]
            subprocess.run(command_string)

            # Get non-extended verification keys from extended verification keys.
            command_string = [
                'cardano-cli', 'key', 'non-extended-key',
                '--extended-verification-key-file', path + wallet_id + '.stake.evkey',
                '--verification-key-file', path + wallet_id + '.stake.vkey'
            ]
            subprocess.run(command_string)
            command_string = [
                'cardano-cli', 'key', 'non-extended-key',
                '--extended-verification-key-file', path + wallet_id + '.payment.evkey',
                '--verification-key-file', path + wallet_id + '.payment.vkey'
            ]
            subprocess.run(command_string)

            # Build stake and payment addresses
            command_string = [
                'cardano-cli', 'stake-address', 'build',
                '--stake-verification-key-file', path + wallet_id + '.stake.vkey',
                '--testnet-magic', self.CARDANO_NETWORK_MAGIC, '--out-file',
                path + wallet_id + '.stake.addr'
            ]
            subprocess.run(command_string)
            command_string = [
                'cardano-cli', 'address', 'build',
                '--payment-verification-key-file', path + wallet_id + '.payment.vkey',
                '--testnet-magic', self.CARDANO_NETWORK_MAGIC, '--out-file', path + wallet_id + '.payment.addr'
            ]
            subprocess.run(command_string)
            command_string = [
                'cardano-cli', 'address', 'build',
                '--payment-verification-key-file', path + wallet_id + '.payment.vkey',
                '--stake-verification-key-file', path + wallet_id + '.stake.vkey',
                '--testnet-magic', self.CARDANO_NETWORK_MAGIC, '--out-file', path + wallet_id + '.base.addr'
            ]
            subprocess.run(command_string)
        except Exception:
            print('problems generating the keys or saving the files')

    def topayment_wallet(self, wallet_id, derivation_path):
        # Generate payment key
        path = self.KEYS_FILE_PATH + '/' + wallet_id + '/'
        derivation_path_concat = '/'.join(derivation_path)
        output = self.cat_files(path, wallet_id + '.root.prv')
        command_string = [
            'cardano-address', 'key', 'child', derivation_path_concat
        ]
        output1 = subprocess.Popen(
            command_string, stdin=output.stdout, stdout=subprocess.PIPE)
        # output.stdout.close()
        payment_xprv = output1.communicate()[0].decode('utf-8')
        # output1.stdout.close()
        save_file(path, wallet_id + '.payment.xprv', str(payment_xprv))

        # Convert cardano-addresses extended signing keys to corresponding
        # Shelley-format keys.

        command_string = [
            'cardano-cli', 'key', 'convert-cardano-address-key',
            '--shelley-payment-key', '--signing-key-file',
            path + wallet_id + '.payment.xprv', '--out-file', path + wallet_id + '.payment.skey'
        ]
        subprocess.run(command_string)

    def validate_address(self, address: str) -> bool:
        """
        Empty docstring
        """
        if not address.startswith('addr' or 'DdzFF'):
            print(f"{address} is not a valid addresss")
            return False
        else:
            return True

    def min_utxo_lovelace1(self, num_assets, total_asset_name_len, utxoCostPerWord, era):
        ################################################
        # minAda (u) = max (minUTxOValue, (quot (minUTxOValue, adaOnlyUTxOSize)) * (utxoEntrySizeWithoutVal + \
        #               (size B)))

        POLICYIDSize = 28
        utxo_entry_size = 27
        has_datum = False
        num_policies = 1

        byte_len = num_assets * 12 + total_asset_name_len + num_policies * POLICYIDSize
        # print(byte_len)

        b_size = 6 + (byte_len + 7) // 8
        data_hash_size = 10 if has_datum else 0
        finalized_size = utxo_entry_size + b_size + data_hash_size
        minUTxOValue = finalized_size * utxoCostPerWord

        return minUTxOValue

    @staticmethod
    def cat_files(path, name):
        # Generate master key
        command_string = [
            'cat', path + name
        ]
        output = subprocess.Popen(command_string, stdout=subprocess.PIPE)
        return output

    @staticmethod
    def save_metadata(path, name, metadata):
        if metadata == {}:
            metadata_json_file = ''
        else:
            with open(path + '/' + name, 'w') as file:
                json.dump(metadata, file, indent=4, ensure_ascii=False)
            metadata_json_file = path + '/' + name

        return metadata_json_file
