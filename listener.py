from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from pathlib import Path
import json
from datetime import datetime
import pandas as pd


def scan_blocks(chain, start_block, end_block, contract_address, eventfile='deposit_logs.csv'):
    """
    chain - string (Either 'bsc' or 'avax')
    start_block - integer first block to scan
    end_block - integer last block to scan
    contract_address - the address of the deployed contract

	This function reads "Deposit" events from the specified contract, 
	and writes information about the events to the file "deposit_logs.csv"
    """
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    else:
        w3 = Web3(Web3.HTTPProvider(api_url))

    DEPOSIT_ABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "token", "type": "address" }, { "indexed": true, "internalType": "address", "name": "recipient", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "Deposit", "type": "event" }]')
    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)

    arg_filter = {}

    if start_block == "latest":
        start_block = w3.eth.get_block_number()
    if end_block == "latest":
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print( f"Error end_block < start_block!" )
        print( f"end_block = {end_block}" )
        print( f"start_block = {start_block}" )

    if start_block == end_block:
        print( f"Scanning block {start_block} on {chain}" )
    else:
        print( f"Scanning blocks {start_block} - {end_block} on {chain}" )

    records = []
    if end_block - start_block < 30:
        event_filter = contract.events.Deposit.create_filter(from_block=start_block,to_block=end_block,argument_filters=arg_filter)
        events = event_filter.get_all_entries()
        #print( f"Got {len(events)} entries for block {block_num}" )
        for evt in events:
            records.append({
                'chain':            chain,
                'token':            evt.args['token'],
                'recipient':        evt.args['recipient'],
                'amount':           evt.args['amount'],
                'transactionHash':  evt.transactionHash.hex(),
                'address':          evt.address
            })

    else:
        for block_num in range(start_block,end_block+1):
            event_filter = contract.events.Deposit.create_filter(from_block=block_num,to_block=block_num,argument_filters=arg_filter)
            events = event_filter.get_all_entries()
            #print( f"Got {len(events)} entries for block {block_num}" )
            for evt in events:
                records.append({
                    'chain':            chain,
                    'token':            evt.args['token'],
                    'recipient':        evt.args['recipient'],
                    'amount':           evt.args['amount'],
                    'transactionHash':  evt.transactionHash.hex(),
                    'address':          evt.address
                })
    
    # put results to csv
    df = pd.DataFrame(records, columns=[
        'chain','token','recipient','amount','transactionHash','address'])
    df.to_csv(eventfile, index=False)
    print(f"Wrote {len(records)} Deposit events to {eventfile}")


if __name__ == "__main__":
    import sys
    from web3 import Web3

    if len(sys.argv) != 5:
        print("Usage: python listener.py <chain> <start_block> <end_block> <contract_address>")
        print("  e.g. python listener.py avax 10000000 10000010 0x1234…")
        sys.exit(1)

    chain            = sys.argv[1]
    start_block      = int(sys.argv[2])
    end_block        = int(sys.argv[3])
    contract_address = Web3.to_checksum_address(sys.argv[4])

    scan_blocks(chain, start_block, end_block, contract_address)
