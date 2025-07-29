from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd


def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]



def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0

    info_src = get_contract_info('source', contract_info)
    info_dst = get_contract_info('destination', contract_info)

    w3_src = connect_to('source')
    w3_dst = connect_to('destination')
    src = w3_src.eth.contract(address=info_src['address'], abi=info_src['abi'])
    dst = w3_dst.eth.contract(address=info_dst['address'], abi=info_dst['abi'])

    # warden account
    warden_key = info_src['private_key']
    acct_src = w3_src.eth.account.from_key(warden_key)
    acct_dst = w3_dst.eth.account.from_key(warden_key)

    # look at the last 5 blocks
    if chain == 'source':
        w3 = w3_src; contract = src; other = dst; acct = acct_dst
        event_name = 'Deposit'
    else:
        w3 = w3_dst; contract = dst; other = src; acct = acct_src
        event_name = 'Unwrap'

    latest = w3.eth.get_block_number()
    start = latest - 5 if latest >= 5 else 0
    print(f"[{chain}] scanning blocks {start}–{latest}")

    # create the filter
    event_obj = getattr(contract.events, event_name)
    evf = event_obj.create_filter(from_block=start, to_block=latest)
    entries = evf.get_all_entries()
    print(f"[{chain}] saw {len(entries)} {event_name} events")

    for e in entries:
        if chain == 'source':
            tx = other.functions.wrap(
                e.args['token'],
                e.args['recipient'],
                e.args['amount']
            )
            w3_o = w3_dst
            acct_o = acct_dst
        else:
            tx = other.functions.withdraw(
                e.args['wrapped_token'],
                e.args['to'],
                e.args['amount']
            )
            w3_o = w3_src
            acct_o = acct_src

        # build, sign, and send on the other chain
        nonce = w3_o.eth.get_transaction_count(acct_o.address)
        built = tx.build_transaction({
            'chainId': w3_o.eth.chain_id,
            'gas':     300_000,
            'gasPrice': w3_o.eth.gas_price,
            'nonce':   nonce,
        })
        signed = acct_o.sign_transaction(built)
        txh = w3_o.eth.send_raw_transaction(signed.rawTransaction)
        print(f"→ forwarded {event_name} event in tx {txh.hex()}")

