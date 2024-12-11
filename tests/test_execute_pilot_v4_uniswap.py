import os
import time
from typing import Tuple

from eth_abi.abi import decode
from web3 import Web3
from web3.types import TxReceipt

from constants import (
    ANVIL_WALLET,
    ARBITRUM,
    ANVIL_WALLET_PRIVATE_KEY,
)
from ipor_fusion.AnvilTestContainerStarter import AnvilTestContainerStarter
from ipor_fusion.CheatingPlasmaVaultSystemFactory import (
    CheatingPlasmaVaultSystemFactory,
)
from ipor_fusion.PlasmaVaultSystemFactory import PlasmaVaultSystemFactory
from ipor_fusion.Roles import Roles

fork_url = os.getenv("ARBITRUM_PROVIDER_URL")
# anvil = AnvilTestContainerStarter(fork_url, 254084008)
anvil = AnvilTestContainerStarter(fork_url)
anvil.start()


def test_should_open_new_position_uniswap_v3():
    # Reset state and grant necessary roles
    # anvil.reset_fork(254084008)

    system = PlasmaVaultSystemFactory(
        provider_url=anvil.get_anvil_http_url(),
        private_key=ANVIL_WALLET_PRIVATE_KEY,
    ).get(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    cheating = CheatingPlasmaVaultSystemFactory(
        provider_url=anvil.get_anvil_http_url(),
        private_key=ANVIL_WALLET_PRIVATE_KEY,
    ).get(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    cheating.prank(system.access_manager().owner())
    cheating.access_manager().grant_role(Roles.ALPHA_ROLE, ANVIL_WALLET, 0)

    # Swap USDC to USDT
    swap = system.uniswap_v3().swap(
        token_in_address=system.usdc().address(),
        token_out_address=system.usdt().address(),
        fee=100,
        token_in_amount=int(500e6),
        min_out_amount=0,
    )
    system.plasma_vault().execute([swap])

    # Check balances after swap
    vault_usdc_balance_after_swap = system.usdc().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )
    vault_usdt_balance_after_swap = system.usdt().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )

    # Create a new position with specified parameters
    new_position = system.uniswap_v3().new_position(
        token0=system.usdc().address(),
        token1=system.usdt().address(),
        fee=100,
        tick_lower=-100,
        tick_upper=101,
        amount0_desired=int(499e6),
        amount1_desired=int(499e6),
        amount0_min=0,
        amount1_min=0,
        deadline=int(time.time()) + 100,
    )

    # Execute the creation of the new position
    system.plasma_vault().execute([new_position])

    # Check balances after opening the new position
    vault_usdc_balance_after_new_position = system.usdc().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )
    vault_usdt_balance_after_new_position = system.usdt().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )

    # Assert on balance changes after creating the new position
    usdc_change = vault_usdc_balance_after_new_position - vault_usdc_balance_after_swap
    usdt_change = vault_usdt_balance_after_new_position - vault_usdt_balance_after_swap

    assert usdc_change == -int(
        499e6
    ), "USDC balance after new position does not match expected change of -499e6"
    assert (
        usdt_change == -489_152502
    ), "USDT balance after new position does not match expected change of -489_152502"


def test_should_collect_all_after_decrease_liquidity():
    # Reset state and grant necessary roles
    # anvil.reset_fork(254084008)

    system = PlasmaVaultSystemFactory(
        provider_url=anvil.get_anvil_http_url(),
        private_key=ANVIL_WALLET_PRIVATE_KEY,
    ).get(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    cheating = CheatingPlasmaVaultSystemFactory(
        provider_url=anvil.get_anvil_http_url(),
        private_key=ANVIL_WALLET_PRIVATE_KEY,
    ).get(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    cheating.prank(system.access_manager().owner())
    cheating.access_manager().grant_role(Roles.ALPHA_ROLE, ANVIL_WALLET, 0)

    # Swap USDC to USDT
    swap = system.uniswap_v3().swap(
        token_in_address=system.usdc().address(),
        token_out_address=system.usdt().address(),
        fee=100,
        token_in_amount=int(500e6),
        min_out_amount=0,
    )
    system.plasma_vault().execute([swap])

    # Create a new position with specified parameters
    new_position = system.uniswap_v3().new_position(
        token0=system.usdc().address(),
        token1=system.usdt().address(),
        fee=100,
        tick_lower=-100,
        tick_upper=101,
        amount0_desired=int(499e6),
        amount1_desired=int(499e6),
        amount0_min=0,
        amount1_min=0,
        deadline=int(time.time()) + 100,
    )
    tx = system.plasma_vault().execute([new_position])

    # Extract data from the new position creation event
    _, new_token_id, liquidity, *_ = extract_enter_data_form_new_position_event(tx)

    # Decrease the liquidity of the newly created position
    decrease_action = system.uniswap_v3().decrease_position(
        token_id=new_token_id,
        liquidity=liquidity,
        amount0_min=0,
        amount1_min=0,
        deadline=int(time.time()) + 100,
    )
    system.plasma_vault().execute([decrease_action])

    # Check balances before the collect action
    vault_usdc_balance_before = system.usdc().balance_of(ARBITRUM.PILOT.V5.PLASMA_VAULT)
    vault_usdt_balance_before = system.usdt().balance_of(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    # Perform the collect action
    collect = system.uniswap_v3().collect(token_ids=[new_token_id])
    system.plasma_vault().execute([collect])

    # Check balances after the collect action
    vault_usdc_balance_after = system.usdc().balance_of(ARBITRUM.PILOT.V5.PLASMA_VAULT)
    vault_usdt_balance_after = system.usdt().balance_of(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    collect_usdc_change = vault_usdc_balance_after - vault_usdc_balance_before
    collect_usdt_change = vault_usdt_balance_after - vault_usdt_balance_before

    # Assert on balance changes after collect action
    assert (
        498_000000 < collect_usdc_change < 500_000000
    ), "USDC balance after collect is out of expected range"
    assert (
        489_000000 < collect_usdt_change < 500_000000
    ), "USDT balance after collect is out of expected range"

    # Close the position
    close_position = system.uniswap_v3().close_position(token_ids=[new_token_id])
    receipt = system.plasma_vault().execute([close_position])

    # Extract data from the position closing event
    _, close_token_id = extract_exit_data_form_new_position_event(receipt)

    # Assert that the token ID of the new position matches the closed position's token ID
    assert (
        new_token_id == close_token_id
    ), "Token ID of new position does not match closed position"


def test_should_increase_liquidity():
    # Setup: Reset state and grant necessary roles
    # anvil.reset_fork(254084008)

    system = PlasmaVaultSystemFactory(
        provider_url=anvil.get_anvil_http_url(),
        private_key=ANVIL_WALLET_PRIVATE_KEY,
    ).get(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    cheating = CheatingPlasmaVaultSystemFactory(
        provider_url=anvil.get_anvil_http_url(),
        private_key=ANVIL_WALLET_PRIVATE_KEY,
    ).get(ARBITRUM.PILOT.V5.PLASMA_VAULT)

    cheating.prank(system.access_manager().owner())
    cheating.access_manager().grant_role(Roles.ALPHA_ROLE, ANVIL_WALLET, 0)

    # Initial swap from USDC to USDT
    swap = system.uniswap_v3().swap(
        token_in_address=system.usdc().address(),
        token_out_address=system.usdt().address(),
        fee=100,
        token_in_amount=int(500e6),
        min_out_amount=0,
    )
    system.plasma_vault().execute([swap])

    # Create a new liquidity position
    new_position = system.uniswap_v3().new_position(
        token0=system.usdc().address(),
        token1=system.usdt().address(),
        fee=100,
        tick_lower=-100,
        tick_upper=101,
        amount0_desired=int(400e6),
        amount1_desired=int(400e6),
        amount0_min=0,
        amount1_min=0,
        deadline=int(time.time()) + 100,
    )
    receipt = system.plasma_vault().execute([new_position])

    # Extract the new token ID from the receipt
    _, new_token_id, *_ = extract_enter_data_form_new_position_event(receipt)

    # Prepare to increase liquidity for the existing position
    increase_position = system.uniswap_v3().increase_position(
        token0=system.usdc().address(),
        token1=system.usdt().address(),
        token_id=new_token_id,
        amount0_desired=int(99e6),
        amount1_desired=int(99e6),
        amount0_min=0,
        amount1_min=0,
        deadline=int(time.time()) + 100,
    )

    # Record balances before increasing liquidity
    vault_usdc_balance_before_increase = system.usdc().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )
    vault_usdt_balance_before_increase = system.usdt().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )

    # Execute the increase liquidity operation
    system.plasma_vault().execute([increase_position])

    # Record balances after increasing liquidity
    vault_usdc_balance_after_increase = system.usdc().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )
    vault_usdt_balance_after_increase = system.usdt().balance_of(
        ARBITRUM.PILOT.V5.PLASMA_VAULT
    )

    # Calculate balance changes
    increase_position_change_usdc = (
        vault_usdc_balance_after_increase - vault_usdc_balance_before_increase
    )
    increase_position_change_usdt = (
        vault_usdt_balance_after_increase - vault_usdt_balance_before_increase
    )

    # Assertions to verify the changes in balance
    assert increase_position_change_usdc == -int(
        99e6
    ), "USDC balance should decrease by 99,000,000"
    assert increase_position_change_usdt == -int(
        97_046288
    ), "USDT balance should decrease by 97,046,288"


def extract_enter_data_form_new_position_event(
    receipt: TxReceipt,
) -> Tuple[str, int, int, int, int, str, str, int, int, int]:
    event_signature_hash = Web3.keccak(
        text="UniswapV3NewPositionFuseEnter(address,uint256,uint128,uint256,uint256,address,address,uint24,int24,int24)"
    )

    for evnet_log in receipt["logs"]:
        if evnet_log["topics"][0] == event_signature_hash:
            decoded_data = decode(
                [
                    "address",
                    "uint256",
                    "uint128",
                    "uint256",
                    "uint256",
                    "address",
                    "address",
                    "uint24",
                    "int24",
                    "int24",
                ],
                evnet_log["data"],
            )
            (
                version,
                token_id,
                liquidity,
                amount0,
                amount1,
                sender,
                recipient,
                fee,
                tick_lower,
                tick_upper,
            ) = decoded_data
            return (
                version,
                token_id,
                liquidity,
                amount0,
                amount1,
                sender,
                recipient,
                fee,
                tick_lower,
                tick_upper,
            )
    raise ValueError("Event log for UniswapV3NewPositionFuseEnter not found")


def extract_exit_data_form_new_position_event(receipt: TxReceipt) -> Tuple[str, int]:
    event_signature_hash = Web3.keccak(
        text="UniswapV3NewPositionFuseExit(address,uint256)"
    )

    for event_log in receipt["logs"]:
        if event_log["topics"][0] == event_signature_hash:
            decoded_data = decode(
                [
                    "address",
                    "uint256",
                ],
                event_log["data"],
            )
            (
                version,
                token_id,
            ) = decoded_data
            return (
                version,
                token_id,
            )
    raise ValueError("Event log for UniswapV3NewPositionFuseExit not found")
