#! /bin/bash

final_path=$1

curl -k -O -J https://hydra.iohk.io/build/7654130/download/1/testnet-topology.json \
    -k -O -J https://hydra.iohk.io/build/7654130/download/1/testnet-shelley-genesis.json \
    -k -O -J https://hydra.iohk.io/build/7654130/download/1/testnet-config.json \
    -k -O -J https://hydra.iohk.io/build/7654130/download/1/testnet-byron-genesis.json \
    -k -O -J https://hydra.iohk.io/build/7654130/download/1/testnet-alonzo-genesis.json

if [ ${final_path} ]; then
    mv testnet-*.json ${final_path}/
fi

echo 'Configuration files succesfully downloaded'