import logging
import os

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

ARBITRUM_PROVIDER_URL = "ARBITRUM_PROVIDER_URL"
FORK_URL = os.getenv(ARBITRUM_PROVIDER_URL)
if not FORK_URL:
    raise ValueError("Environment variable ARBITRUM_PROVIDER_URL must be set")


def test_anvil_reset(web3, anvil):
    # given
    block_number = 254080000

    # when
    anvil.reset_fork(block_number)

    # then
    assert web3.eth.get_block("latest").number == block_number
