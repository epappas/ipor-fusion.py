import logging
import os

import pytest

from commons import execute_transaction, read_token_balance
from constants import (
    ANVIL_WALLET,
    USDC,
    USDT,
    SWAP_FUSE_UNISWAP_V3_ADDRESS,
    PLASMA_VAULT_V4,
    IPOR_FUSION_V4_ACCESS_MANAGER_USDC_ADDRESS,
    NEW_POSITION_SWAP_FUSE_UNISWAP_V3_ADDRESS,
)
from ipor_fusion_sdk.MarketId import MarketId
from ipor_fusion_sdk.VaultExecuteCallFactory import VaultExecuteCallFactory
from ipor_fusion_sdk.fuse.SwapFuseUniswapV3 import SwapFuseUniswapV3
from ipor_fusion_sdk.fuse.UniswapV3NewPositionFuse import UniswapV3NewPositionFuse
from ipor_fusion_sdk.operation.NewPosition import NewPosition
from ipor_fusion_sdk.operation.Swap import Swap

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

ARBITRUM_PROVIDER_URL = "ARBITRUM_PROVIDER_URL"
FORK_URL = os.getenv(ARBITRUM_PROVIDER_URL)
if not FORK_URL:
    raise ValueError("Environment variable ARBITRUM_PROVIDER_URL must be set")

SET_ANVIL_WALLET_AS_PILOT_V4_ALPHA_COMMAND = [
    "cast",
    "send",
    "--unlocked",
    "--from",
    "0x4E3C666F0c898a9aE1F8aBB188c6A2CC151E17fC",
    IPOR_FUSION_V4_ACCESS_MANAGER_USDC_ADDRESS,
    "grantRole(uint64,address,uint32)()",
    "200",
    ANVIL_WALLET,
    "0",
]


@pytest.fixture(scope="module", name="vault_execute_call_factory")
def vault_execute_call_factory_fixture() -> VaultExecuteCallFactory:
    uniswap_v3_swap_fuse = SwapFuseUniswapV3(SWAP_FUSE_UNISWAP_V3_ADDRESS)
    uniswap_v_3_new_position_fuse = UniswapV3NewPositionFuse(
        NEW_POSITION_SWAP_FUSE_UNISWAP_V3_ADDRESS
    )
    return VaultExecuteCallFactory(
        {uniswap_v3_swap_fuse, uniswap_v_3_new_position_fuse}
    )


@pytest.fixture(name="setup", autouse=True)
def setup_fixture(anvil):
    anvil.reset_fork(254084008)
    anvil.execute_in_container(SET_ANVIL_WALLET_AS_PILOT_V4_ALPHA_COMMAND)
    yield


def test_should_swap_when_one_hop_uniswap_v3(web3, account, vault_execute_call_factory):
    # given
    token_in_amount = int(100e6)
    min_out_amount = 0
    fee = 100

    swap = Swap(
        MarketId(SwapFuseUniswapV3.PROTOCOL_ID, "swap"),
        USDC,
        USDT,
        fee,
        token_in_amount,
        min_out_amount,
    )

    operations = [swap]

    function = vault_execute_call_factory.create_execute_call(operations)

    vault_usdc_balance_before = read_token_balance(web3, PLASMA_VAULT_V4, USDC)
    vault_usdt_balance_before = read_token_balance(web3, PLASMA_VAULT_V4, USDT)

    # when
    execute_transaction(web3, PLASMA_VAULT_V4, function, account)

    # then
    vault_usdc_balance_after = read_token_balance(web3, PLASMA_VAULT_V4, USDC)
    vault_usdt_balance_after = read_token_balance(web3, PLASMA_VAULT_V4, USDT)

    assert (
        vault_usdc_balance_after - vault_usdc_balance_before == -token_in_amount
    ), "vault_usdc_balance_before - vault_usdc_balance_after == token_in_amount"
    assert vault_usdt_balance_after - vault_usdt_balance_before > int(
        90e6
    ), "vault_usdt_balance_after - vault_usdt_balance_before  > 90e6"


def test_should_open_two_new_position_uniswap_v3(
    web3, account, vault_execute_call_factory
):
    # given
    timestamp = web3.eth.get_block("latest")["timestamp"]

    token_in_amount = int(500e6)
    min_out_amount = 0
    fee = 100

    swap = Swap(
        MarketId(SwapFuseUniswapV3.PROTOCOL_ID, "swap"),
        USDC,
        USDT,
        fee,
        token_in_amount,
        min_out_amount,
    )

    operations = [swap]

    function_swap = vault_execute_call_factory.create_execute_call(operations)

    vault_usdc_balance_before_swap = read_token_balance(web3, PLASMA_VAULT_V4, USDC)
    vault_usdt_balance_before_swap = read_token_balance(web3, PLASMA_VAULT_V4, USDT)

    log.info("vault_usdc_balance_before_swap: %s", vault_usdc_balance_before_swap)
    log.info("vault_usdt_balance_before_swap: %s", vault_usdt_balance_before_swap)

    execute_transaction(web3, PLASMA_VAULT_V4, function_swap, account)

    new_position = NewPosition(
        market_id=MarketId(SwapFuseUniswapV3.PROTOCOL_ID, "new-position"),
        token0=USDC,
        token1=USDT,
        fee=100,
        tick_lower=-100,
        tick_upper=101,
        amount0_desired=int(499e6),
        amount1_desired=int(499e6),
        amount0_min=0,
        amount1_min=0,
        deadline=timestamp + 100,
    )

    operations = [new_position]

    function = vault_execute_call_factory.create_execute_call(operations)

    vault_usdc_balance_after_swap = read_token_balance(web3, PLASMA_VAULT_V4, USDC)
    vault_usdt_balance_after_swap = read_token_balance(web3, PLASMA_VAULT_V4, USDT)

    # when
    execute_transaction(web3, PLASMA_VAULT_V4, function, account)

    # then
    vault_usdc_balance_after_new_position = read_token_balance(
        web3, PLASMA_VAULT_V4, USDC
    )
    vault_usdt_balance_after_new_position = read_token_balance(
        web3, PLASMA_VAULT_V4, USDT
    )

    assert vault_usdc_balance_after_new_position - vault_usdc_balance_after_swap == -int(
        499e6
    ), "vault_usdc_balance_after_new_position - vault_usdc_balance_after_swap == -499e6"
    assert (
        vault_usdt_balance_after_new_position - vault_usdt_balance_after_swap
        == -489_152502
    ), "vault_usdt_balance_after_new_position - vault_usdt_balance_after_swap == -499e6"
