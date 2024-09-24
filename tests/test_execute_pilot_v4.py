import logging
import os

import pytest
from eth_account import Account

from anvil_container import AnvilTestContainerStarter
from constants import ANVIL_WALLET_PRIVATE_KEY, FLUID_INSTADAPP_STAKING_FUSE_ADDRESS, FLUID_INSTADAPP_USDC_POOL_ADDRESS, \
  FLUID_INSTADAPP_POOL_FUSE_ADDRESS, FLUID_INSTADAPP_STAKING_ADDRESS, FLUID_INSTADAPP_CLAIM_FUSE_ADDRESS, \
  GEARBOX_USDC_POOL_ADDRESS, GEARBOX_POOL_FUSE_ADDRESS, GEARBOX_FARM_USDC_POOL_ADDRESS, GEARBOX_FARM_FUSE_ADDRESS, \
  GEARBOX_CLAIM_FUSE_ADDRESS, GAS_PRICE_MARGIN, DEFAULT_TRANSACTION_MAX_PRIORITY_FEE, \
  IPOR_FUSION_V3_ACCESS_MANAGER_USDC_ADDRESS, ANVIL_WALLET, USDC, AAVEV_V3_FUSE_ADDRESS, COMPOUND_V3_FUSE_ADDRESS, USDT, \
  SWAP_FUSE_UNISWAP_V3_ADDRESS, \
  PLASMA_VAULT_V4, IPOR_FUSION_V4_ACCESS_MANAGER_USDC_ADDRESS, FORK_BLOCK_NUMBER
from ipor_fusion_sdk.MarketId import MarketId
from ipor_fusion_sdk.VaultExecuteCallFactory import VaultExecuteCallFactory
from ipor_fusion_sdk.fuse.AaveV3SupplyFuse import AaveV3SupplyFuse
from ipor_fusion_sdk.fuse.CompoundV3SupplyFuse import CompoundV3SupplyFuse
from ipor_fusion_sdk.fuse.FluidInstadappSupplyFuse import FluidInstadappSupplyFuse
from ipor_fusion_sdk.fuse.GearboxSupplyFuse import GearboxSupplyFuse
from ipor_fusion_sdk.fuse.SwapFuseUniswapV3 import SwapFuseUniswapV3
from ipor_fusion_sdk.operation.Swap import Swap

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

ANVIL_FORK_URL = "ANVIL_FORK_URL"
FORK_URL = os.getenv(ANVIL_FORK_URL)
if not FORK_URL:
  raise ValueError("Environment variable ANVIL_FORK_URL must be set")

SET_ANVIL_WALLET_AS_PILOT_V3_ALPHA_COMMAND = ["cast", "send", "--unlocked", "--from",
                                              "0x4E3C666F0c898a9aE1F8aBB188c6A2CC151E17fC",
                                              IPOR_FUSION_V3_ACCESS_MANAGER_USDC_ADDRESS,
                                              "grantRole(uint64,address,uint32)()", "200", ANVIL_WALLET, "0"]

SET_ANVIL_WALLET_AS_PILOT_V4_ALPHA_COMMAND = ["cast", "send", "--unlocked", "--from",
                                              "0x4E3C666F0c898a9aE1F8aBB188c6A2CC151E17fC",
                                              IPOR_FUSION_V4_ACCESS_MANAGER_USDC_ADDRESS,
                                              "grantRole(uint64,address,uint32)()", "200", ANVIL_WALLET, "0"]


@pytest.fixture(scope="module")
def anvil():
  logging.basicConfig(level=logging.DEBUG)
  container = AnvilTestContainerStarter()
  container.start()
  return container


@pytest.fixture(scope="module")
def web3(anvil):
  client = anvil.get_client()
  print(f"Connected to Ethereum network with chain ID: {anvil.get_chain_id()}")
  print(f"Anvil HTTP URL: {anvil.get_anvil_http_url()}")
  return client


@pytest.fixture(scope="module")
def account():
  return Account.from_key(ANVIL_WALLET_PRIVATE_KEY)


@pytest.fixture(scope="module")
def vault_execute_call_factory() -> VaultExecuteCallFactory:
  fluid_fuse = FluidInstadappSupplyFuse(FLUID_INSTADAPP_USDC_POOL_ADDRESS,
                                        FLUID_INSTADAPP_POOL_FUSE_ADDRESS,
                                        FLUID_INSTADAPP_STAKING_ADDRESS,
                                        FLUID_INSTADAPP_STAKING_FUSE_ADDRESS,
                                        FLUID_INSTADAPP_CLAIM_FUSE_ADDRESS)

  gearbox_fuse = GearboxSupplyFuse(GEARBOX_USDC_POOL_ADDRESS,
                                   GEARBOX_POOL_FUSE_ADDRESS,
                                   GEARBOX_FARM_USDC_POOL_ADDRESS,
                                   GEARBOX_FARM_FUSE_ADDRESS,
                                   GEARBOX_CLAIM_FUSE_ADDRESS)

  aave_v3_fuse = AaveV3SupplyFuse(AAVEV_V3_FUSE_ADDRESS, USDC)

  compound_v3_fuse = CompoundV3SupplyFuse(COMPOUND_V3_FUSE_ADDRESS, USDC)

  uniswap_v3_swap_fuse = SwapFuseUniswapV3(SWAP_FUSE_UNISWAP_V3_ADDRESS)

  return VaultExecuteCallFactory({fluid_fuse, gearbox_fuse, aave_v3_fuse, compound_v3_fuse, uniswap_v3_swap_fuse})


@pytest.fixture
def setup(web3, account, anvil, vault_execute_call_factory):
  anvil.reset_fork(254084008)
  anvil.execute_in_container(SET_ANVIL_WALLET_AS_PILOT_V4_ALPHA_COMMAND)
  yield


def test_should_swap_when_one_hop_uniswap_v3(setup, web3, anvil, account, vault_execute_call_factory):
  # given
  token_in_amount = int(100e6)
  min_out_amount = 0
  fee = 100

  swap = Swap(MarketId(SwapFuseUniswapV3.PROTOCOL_ID, "swap"), USDC, USDT, fee, token_in_amount, min_out_amount)

  operations = [swap]

  function = vault_execute_call_factory.create_execute_call(operations)

  vault_usdc_balance_before = read_token_balance(web3, PLASMA_VAULT_V4, USDC)
  vault_usdt_balance_before = read_token_balance(web3, PLASMA_VAULT_V4, USDT)

  # when
  execute_transaction(web3, PLASMA_VAULT_V4, function, account)

  # then
  vault_usdc_balance_after = read_token_balance(web3, PLASMA_VAULT_V4, USDC)
  vault_usdt_balance_after = read_token_balance(web3, PLASMA_VAULT_V4, USDT)

  assert vault_usdc_balance_after - vault_usdc_balance_before == -token_in_amount, "vault_usdc_balance_before - vault_usdc_balance_after == token_in_amount"
  assert vault_usdt_balance_after - vault_usdt_balance_before > int(90e6), "vault_usdt_balance_after - vault_usdt_balance_before  > 90e6"


def execute_transaction(web3, contract_address, function, account):
  nonce = web3.eth.get_transaction_count(account.address)
  gas_price = web3.eth.gas_price
  max_fee_per_gas = calculate_max_fee_per_gas(gas_price)
  max_priority_fee_per_gas = get_max_priority_fee(gas_price)
  data = f'0x{function.hex()}'
  estimated_gas = int(1.25 * web3.eth.estimate_gas({'to': contract_address, 'from': account.address, 'data': data}))

  transaction = {'chainId': web3.eth.chain_id, 'gas': estimated_gas, 'maxFeePerGas': max_fee_per_gas,
                 'maxPriorityFeePerGas': max_priority_fee_per_gas, 'to': contract_address, 'from': account.address,
                 'nonce': nonce, 'data': data}

  signed_tx = web3.eth.account.sign_transaction(transaction, account.key)
  tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
  receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
  assert receipt["status"] == 1, "Transaction failed"


def read_token_balance(web3, holder, token):
  contract = web3.eth.contract(address=token,
                               abi=[{"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
                                     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}],
                                     "type": "function", }])
  return contract.functions.balanceOf(holder).call()


def calculate_max_fee_per_gas(gas_price):
  return gas_price + percent_of(gas_price, GAS_PRICE_MARGIN)


def get_max_priority_fee(gas_price):
  return min(DEFAULT_TRANSACTION_MAX_PRIORITY_FEE, gas_price // 10)


def percent_of(value, percentage):
  return value * percentage // 100
