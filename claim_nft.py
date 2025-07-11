from web3 import Web3
import json
import random

# ────────────────────────────────────────────────────────────────────────
# 1) Connect to Avalanche Fuji Testnet
RPC_URL = "https://api.avax-test.network/ext/bc/C/rpc"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# If you upgrade to a web3.py release that includes PoA middleware,
# you can uncomment these two lines:
# from web3.middleware import geth_poa_middleware
# w3.middleware_onion.inject(geth_poa_middleware, layer=0)

assert w3.is_connected(), "Failed to connect to Fuji Testnet"

# ────────────────────────────────────────────────────────────────────────
# 2) Load your private key & account
PRIVATE_KEY = "0x90f64d6fc93bb5d55275e58c58c06e7d74d6e30c52a2daf2b5a3cefa9fd5ff01"
acct = w3.eth.account.from_key(PRIVATE_KEY)
print("Using address:", acct.address)

# ────────────────────────────────────────────────────────────────────────
# 3) Load the NFT contract
with open("NFT.abi", "r") as f:
    abi = json.load(f)

CONTRACT_ADDRESS = "0x85ac2e065d4526FBeE6a2253389669a12318A412"
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

# ────────────────────────────────────────────────────────────────────────
# 4) Build your `claim` transaction with a bytes32 nonce
nonce = w3.eth.get_transaction_count(acct.address)

# Generate a random 256-bit integer and convert to 32 bytes
random_int  = random.getrandbits(256)
nonce_bytes = random_int.to_bytes(32, byteorder="big")

tx = contract.functions.claim(
    acct.address,    # recipient
    nonce_bytes      # bytes32 nonce
).build_transaction({
    "chainId": 43113,            # Fuji chain ID
    "gas":     300_000,
    "gasPrice": w3.eth.gas_price,
    "nonce":   nonce
})

# ────────────────────────────────────────────────────────────────────────
# 5) Sign & send
signed_tx = acct.sign_transaction(tx)
tx_hash   = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print("Claim tx submitted:", tx_hash.hex())

# 6) Wait for it to be mined
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("✅ Mined in block", receipt.blockNumber)

# 7) Decode the Transfer event to see which token ID you got
transfer_events = contract.events.Transfer().process_receipt(receipt)
for ev in transfer_events:
    token_id = ev["args"]["tokenId"]
    print(f"🎉 You just claimed Token ID: {token_id}")

# 8) Confirm your balance
balance = contract.functions.balanceOf(acct.address).call()
print("Your ERC-721 balance is:", balance)

