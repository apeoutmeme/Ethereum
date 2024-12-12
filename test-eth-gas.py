import time
import logging
from web3.middleware import geth_poa_middleware
import requests
from decimal import Decimal
from web3 import Web3
import json
import os

eth_node_url = ''

w3 = Web3(Web3.HTTPProvider(eth_node_url))
# Apply the PoA middleware to handle extraData length
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def get_gas_price_usd():
    # Fetch current ETH price in USD
    eth_price_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(eth_price_url)
    eth_price_usd = Decimal(str(response.json()['ethereum']['usd']))

    # Get current base fee
    last_block = w3.eth.get_block('latest')
    base_fee = Decimal(w3.from_wei(last_block['baseFeePerGas'], 'gwei'))
    
    # Estimate max priority fee
    max_priority_fee = Decimal('2')  # Set a default value of 2 Gwei

    try:
        # Try to get the suggested max priority fee from the network
        suggested_tip = w3.eth.max_priority_fee
        if suggested_tip is not None:
            max_priority_fee = Decimal(w3.from_wei(suggested_tip, 'gwei'))
    except AttributeError:
        # If max_priority_fee is not available, use a simple estimation
        max_priority_fee = base_fee * Decimal('0.1')  # 10% of base fee as priority fee

    max_priority_fee = max(max_priority_fee, Decimal('1.0'))  # Ensure it's at least 1 Gwei

    # Calculate total gas price (base fee + max priority fee)
    total_gas_price_gwei = base_fee + max_priority_fee

    # Calculate gas price in USD for a standard transaction (21000 gas)
    gas_price_usd = (total_gas_price_gwei * Decimal('21000') / Decimal('1e9')) * eth_price_usd

    return total_gas_price_gwei, gas_price_usd, base_fee, max_priority_fee

def test_gas_price():
    total_gas_price_gwei, gas_price_usd, base_fee, max_priority_fee = get_gas_price_usd()
    print(f"Total gas price: {total_gas_price_gwei:.2f} Gwei")
    print(f"Gas price in USD: ${gas_price_usd:.2f}")
    print(f"Base fee: {base_fee:.2f} Gwei")
    print(f"Max priority fee: {max_priority_fee:.2f} Gwei")

 
    # Get the latest block and print some information
    latest_block = w3.eth.get_block('latest')
    print(f"Latest block number: {latest_block['number']}")
    print(f"Latest block base fee per gas: {w3.from_wei(latest_block['baseFeePerGas'], 'gwei'):.2f} Gwei")

    # Get pending transactions and their max priority fees
    pending_transactions = w3.eth.get_block('pending')['transactions']
    if pending_transactions:
        print("Max priority fees in pending transactions:")
        for tx_hash in pending_transactions[:5]:  # Check up to 5 pending transactions
            tx = w3.eth.get_transaction(tx_hash)
            if 'maxPriorityFeePerGas' in tx:
                print(f"  {w3.from_wei(tx['maxPriorityFeePerGas'], 'gwei'):.2f} Gwei")
    else:
        print("No pending transactions found.")

if __name__ == "__main__":
    test_gas_price()
