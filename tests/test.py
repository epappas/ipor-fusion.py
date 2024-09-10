import pytest
from eth_account import Account
from web3 import Web3
from web3.contract.contract import ContractFunction

from ipor_fusion_sdk.MarketId import MarketId
from ipor_fusion_sdk.VaultExecuteCallFactory import VaultExecuteCallFactory
from ipor_fusion_sdk.fuse.AaveV3SupplyFuse import AaveV3SupplyFuse
from ipor_fusion_sdk.fuse.CompoundV3SupplyFuse import CompoundV3SupplyFuse
from ipor_fusion_sdk.operation.Supply import Supply
from ipor_fusion_sdk.operation.Withdraw import Withdraw
from tests.constants import ANVIL_WALLET_PRIVATE_KEY, USDC, ONE_HUNDRED_USDC, AAVEV_V3_FUSE_ADDRESS, \
  COMPOUND_V3_FUSE_ADDRESS, PLASMA_VAULT


@pytest.fixture(scope="module")
def web3():
  w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
  return w3


@pytest.fixture(scope="module")
def account():
  return Account.from_key(ANVIL_WALLET_PRIVATE_KEY)


def test_withdraw_and_supply_pilot_v2(web3):
  withdraw = Withdraw(MarketId("aave-v3", USDC), ONE_HUNDRED_USDC)
  supply = Supply(MarketId("compound-v3", USDC), ONE_HUNDRED_USDC)
  operations = [withdraw, supply]
  aave_v3_fuse = AaveV3SupplyFuse(AAVEV_V3_FUSE_ADDRESS, USDC)
  compound_v3_fuse = CompoundV3SupplyFuse(COMPOUND_V3_FUSE_ADDRESS, USDC)
  vault_execute_call_factory = VaultExecuteCallFactory({aave_v3_fuse, compound_v3_fuse})
  function = vault_execute_call_factory.create_execute_call(operations)

  print(contract)
