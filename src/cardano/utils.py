# General imports
import os
import subprocess
from decouple import config  # type: ignore
import json

# Module imports
from src.utils.path_utils import get_root_path

working_dir = get_root_path()
cardano_configs = f'{working_dir}/config/cardano_config.json'

with open(cardano_configs) as file:
    params = json.load(file)
keys_file_path = params['node']['KEYS_FILE_PATH']
if not os.path.exists(keys_file_path):
    os.makedirs(keys_file_path)


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def save_files(path, name, content):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(path + name, 'w') as file:
        file.write(str(content))


def cat_files(path, name):
    # Generate master key
    command_string = [
        'cat', path + name
    ]
    output = subprocess.Popen(command_string, stdout=subprocess.PIPE)
    return output


def remove_files(path, name):
    if os.path.exists(path + name):
        os.remove(path + name)
    # os.rmdir(path+name)
    # shutil.rmtree(path+name)


def save_metadata(path, name, metadata):
    try:
        if metadata == {}:
            metadata_json_file = ''
        else:
            if not os.path.exists(path):
                os.makedirs(path)
            with open(path + '/' + name, 'w') as file:
                json.dump(metadata, file, indent=4, ensure_ascii=False)
            metadata_json_file = path + '/' + name

        return metadata_json_file
    except TypeError:
        raise TypeError()


def towallet(wallet_id, mnemonic):
    try:
        ################################
        # generating additional keys before the actual creation
        ################################
        # Save temp mnemonic
        content = ' '.join(mnemonic)
        path = keys_file_path + '/' + wallet_id + '/'
        temp_mnemonic = wallet_id + '.temp_mnemonic'
        save_files(path, temp_mnemonic, content)

        # Generate master key
        output = cat_files(path, temp_mnemonic)
        command_string = [
            'cardano-address', 'key', 'from-recovery-phrase', 'Shelley'
        ]
        output2 = subprocess.Popen(
            command_string, stdin=output.stdout, stdout=subprocess.PIPE)
        # output.stdout.close()

        content = output2.communicate()[0].decode('utf-8')
        # Save temp private keys files
        save_files(path, wallet_id + '.root.prv', str(content))
        # Delete file mnemonic
        remove_files(path, temp_mnemonic)

        output = cat_files(path, wallet_id + '.root.prv')
        # Generate stake key
        command_string = [
            'cardano-address', 'key', 'child', '1852H/1815H/0H/2/0'
        ]
        output3 = subprocess.Popen(
            command_string, stdin=output.stdout, stdout=subprocess.PIPE)
        # output.stdout.close()
        # Generate payment key
        output = cat_files(path, wallet_id + '.root.prv')
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
        save_files(path, wallet_id + '.stake.xprv', str(stake_xprv))
        save_files(path, wallet_id + '.payment.xprv', str(payment_xprv))

        # Generate payment verification key xpub
        output = cat_files(path, wallet_id + '.payment.xprv')
        command_string = [
            'cardano-address', 'key', 'public', '--with-chain-code'
        ]
        output1 = subprocess.Popen(
            command_string, stdin=output.stdout, stdout=subprocess.PIPE)
        # output.stdout.close()
        payment_xpub = output1.communicate()[0].decode('utf-8')
        save_files(path, wallet_id + '.payment.xpub', str(payment_xpub))
        CARDANO_NETWORK = config('CARDANO_NETWORK')

        # Generate payment address from verification key
        output = cat_files(path, wallet_id + '.payment.xprv')
        command_string = [
            'cardano-address', 'address', 'payment', '--network-tag',
            CARDANO_NETWORK]
        output1 = subprocess.Popen(
            command_string, stdin=output.stdout, stdout=subprocess.PIPE)
        # output.stdout.close()
        payment_addr = output1.communicate()[0].decode('utf-8')
        save_files(path, wallet_id + '.payment.addr', str(payment_addr))

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
        CARDANO_NETWORK_MAGIC = config('CARDANO_NETWORK_MAGIC')
        command_string = [
            'cardano-cli', 'stake-address', 'build',
            '--stake-verification-key-file', path + wallet_id + '.stake.vkey',
            '--testnet-magic', CARDANO_NETWORK_MAGIC, '--out-file',
            path + wallet_id + '.stake.addr'
        ]
        subprocess.run(command_string)
        command_string = [
            'cardano-cli', 'address', 'build',
            '--payment-verification-key-file', path + wallet_id + '.payment.vkey',
            '--testnet-magic', CARDANO_NETWORK_MAGIC, '--out-file', path + wallet_id + '.payment.addr'
        ]
        subprocess.run(command_string)
        command_string = [
            'cardano-cli', 'address', 'build',
            '--payment-verification-key-file', path + wallet_id + '.payment.vkey',
            '--stake-verification-key-file', path + wallet_id + '.stake.vkey',
            '--testnet-magic', CARDANO_NETWORK_MAGIC, '--out-file', path + wallet_id + '.base.addr'
        ]
        subprocess.run(command_string)
    except Exception:
        print('problems generating the keys or saving the files')


def topayment_wallet(wallet_id, derivation_path):
    # Generate payment key
    path = keys_file_path + '/' + wallet_id + '/'
    derivation_path_concat = '/'.join(derivation_path)
    output = cat_files(path, wallet_id + '.root.prv')
    command_string = [
        'cardano-address', 'key', 'child', derivation_path_concat
    ]
    output1 = subprocess.Popen(
        command_string, stdin=output.stdout, stdout=subprocess.PIPE)
    # output.stdout.close()
    payment_xprv = output1.communicate()[0].decode('utf-8')
    # output1.stdout.close()
    save_files(path, wallet_id + '.payment.xprv', str(payment_xprv))

    # Convert cardano-addresses extended signing keys to corresponding
    # Shelley-format keys.

    command_string = [
        'cardano-cli', 'key', 'convert-cardano-address-key',
        '--shelley-payment-key', '--signing-key-file',
        path + wallet_id + '.payment.xprv', '--out-file', path + wallet_id + '.payment.skey'
    ]
    subprocess.run(command_string)


def validate_vars_mandatory(keywords: list, input_vars: dict) -> list:
    """
    Complementing `validate_dict` and implemented
    at `parse_inputs`.

    """
    result = []
    keys = input_vars.keys()
    for key in keywords:
        try:
            assert key in keys and input_vars[key] is not None
            result.append(input_vars[key])
        except AssertionError:
            print(f'{key} is missing')
            result = []
            break
    return result


def validate_address(address: str) -> bool:
    """

    """
    if not address.startswith('addr' or 'DdzFF'):
        print(f"{address} is not a valid addresss")
        return False
    else:
        return True


def validate_vars_others(keywords: list, input_vars: dict) -> list:
    """
    Complementing `validate_dict` and implemented
    at `parse_inputs`.

    """
    result = []
    for key in keywords:
        if key in input_vars.keys():
            result.append(input_vars[key])
        else:
            result.append(None)
    return result


def validate_dict(keywords: list, vals: Union[str, dict]):
    """
    Complementing `validate_vars` and implemented
    at `parse_inputs`.
    """
    if isinstance(vals, str):
        try:
            with open(vals) as f:
                from_json = json.load(f)
                return from_json
        except FileNotFoundError:
            try:
                from_json = json.loads(vals)
                return from_json
            except TypeError:
                print('Provide a valid format for JSON.')
    else:
        try:
            return [val for arg in vals for name, val in arg.items()
                    if name in keywords]
        except AttributeError:
            print('Provide a valid input')


def parse_inputs(keywords: list, *args, **kwargs):
    """
    Parse the input for Cardano objects functions.
    """
    if args:
        output = validate_dict(keywords, args[0])
        if isinstance(output, dict):
            return [val for key, val in output.items()]
        else:
            return output
    else:
        return validate_vars_mandatory(keywords, kwargs)


def min_utxo_lovelace1(num_assets, total_asset_name_len, utxoCostPerWord, era):

    ################################################
    # minAda (u) = max (minUTxOValue, (quot (minUTxOValue, adaOnlyUTxOSize)) * (utxoEntrySizeWithoutVal + (size B)))

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
