# Create Cardano Wallets
from src.cardano.base import Keys
key= Keys()

nWallets = 3
names = ['wallet01', 'wallet02', 'wallet03']

for name in names:
    key.deriveAllKeys(24,name)