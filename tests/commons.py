from constants import (
    GAS_PRICE_MARGIN,
    DEFAULT_TRANSACTION_MAX_PRIORITY_FEE,
)


def execute_transaction(web3, contract_address, function, account):
    nonce = web3.eth.get_transaction_count(account.address)
    gas_price = web3.eth.gas_price
    max_fee_per_gas = calculate_max_fee_per_gas(gas_price)
    max_priority_fee_per_gas = get_max_priority_fee(gas_price)
    data = f"0x{function.hex()}"
    estimated_gas = int(
        1.25
        * web3.eth.estimate_gas(
            {"to": contract_address, "from": account.address, "data": data}
        )
    )

    transaction = {
        "chainId": web3.eth.chain_id,
        "gas": estimated_gas,
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": max_priority_fee_per_gas,
        "to": contract_address,
        "from": account.address,
        "nonce": nonce,
        "data": data,
    }

    signed_tx = web3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt["status"] == 1, "Transaction failed"


def read_token_balance(web3, holder, token):
    contract = web3.eth.contract(
        address=token,
        abi=[
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ],
    )
    return contract.functions.balanceOf(holder).call()


def calculate_max_fee_per_gas(gas_price):
    return gas_price + percent_of(gas_price, GAS_PRICE_MARGIN)


def get_max_priority_fee(gas_price):
    return min(DEFAULT_TRANSACTION_MAX_PRIORITY_FEE, gas_price // 10)


def percent_of(value, percentage):
    return value * percentage // 100
