# General Imports
from enum import Enum
# Module Imports
from src.cardano.node_lib import Wallet, Node, IotExtensions

class WalletFunctions(Enum):
    """
    Enum loaded with the functions for Wallet Class, paired with actionable keywords that serve as commands for the IoT Service
    """
    LIST_WALLETS = Wallet.list_wallets
    GENERATE_NEW_MNEMONIC_PHRASE = Wallet.generate_mnemonic
    MIN_FEES = Wallet.min_fees
    CONFIRM_TRANSACTION = Wallet.confirm_transaction
    CONFIRM_TRANSACTION_BY_TX = Wallet.confirm_transaction_by_tx
    DELETE_WALLET = Wallet.delete_wallet
    ASSETS_BALANCE = Wallet.assets_balance

class NodeFunctions(Enum):
    """
    Enum loaded with the functions for Node Class, paired with actionable keywords that serve as commands for the IoT Service
    """
    QUERY_TIP = Node.query_tip_exec
    CREATE_MINTING_POLICY = Node.create_minting_policy
    MINT_ASSET = Node.minting
    GET_TRANSACTIONS = Node.get_transactions
    GET_BALANCE = Node.get_balance

class IotExtensionFunctions(Enum):
    """
    Enum loaded with the functions for Extensions Class, paired with actionable keywords that serve as commands for the IoT Service
    """
    WALLET_INFO = IotExtensions.get_wallet_info
    GENERATE_WALLET = IotExtensions.generate_wallet
    SEND_TRANSACTION = IotExtensions.send_transaction