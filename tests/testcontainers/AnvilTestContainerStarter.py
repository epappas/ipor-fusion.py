import os
import logging
import time
from typing import Union

from testcontainers.core.container import DockerContainer
from web3 import Web3, HTTPProvider

class AnvilTestContainerStarter:
    ANVIL_FORK_URL = "ANVIL_FORK_URL"
    ANVIL_CONTAINER = os.getenv("ANVIL_TEST_CONTAINER", "ghcr.io/foundry-rs/foundry:nightly-af97b2c75cbcfaba23462998ae75ca082bcca1f2")
    FORK_URL = os.getenv(ANVIL_FORK_URL)
    if not FORK_URL:
        raise ValueError("fork-url must not be null")
    MAX_WAIT_SECONDS = 1201
    ANVIL_HTTP_PORT = 8545
    CHAIN_ID = 42161
    FORK_BLOCK_NUMBER = 250690377
    ANVIL_COMMAND_FORMAT = f"\"anvil --steps-tracing --auto-impersonate --host 0.0.0.0 --fork-url {FORK_URL} --fork-block-number {FORK_BLOCK_NUMBER}\""

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.anvil = DockerContainer(self.ANVIL_CONTAINER)
        self.anvil.with_exposed_ports(self.ANVIL_HTTP_PORT).with_command(self.ANVIL_COMMAND_FORMAT)

    def get_anvil_http_url(self):
        return f"http://{self.anvil.get_container_host_ip()}:{self.anvil.get_exposed_port(self.ANVIL_HTTP_PORT)}"

    def get_chain_id(self):
        return self.CHAIN_ID

    def get_client(self):
        http_url = self.get_anvil_http_url()
        return Web3(HTTPProvider(http_url))

    def execute_in_container(self, command: Union[str, list[str]]) -> tuple[int, bytes]:
        result = self.anvil.exec(command)
        if result.exit_code != 0:
            self.log.error(f"Error while executing command in container: {result}")
            raise RuntimeError("Error while executing command in container")

    def start(self):
        self.log.info("[CONTAINER] [ANVIL] Anvil container is starting")
        self.anvil.start()
        time.sleep(3)
        self.log.info("[CONTAINER] [ANVIL] Anvil container started")
