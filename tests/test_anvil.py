import logging
import os

import pytest

from anvil_container import AnvilTestContainerStarter

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

ANVIL_FORK_URL = "ANVIL_FORK_URL"
FORK_URL = os.getenv(ANVIL_FORK_URL)
if not FORK_URL:
  raise ValueError("Environment variable ANVIL_FORK_URL must be set")


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


def test_anvil_reset(web3, anvil):
  # given
  block_number = 254080000

  # when
  anvil.reset_fork(block_number)

  # then
  assert web3.eth.get_block('latest').number == block_number
