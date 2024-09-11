from abc import ABC, abstractmethod
from typing import List

from ipor_fusion_sdk import MarketId
from ipor_fusion_sdk.fuse import FuseActionDynamicStruct


class Fuse(ABC):
  @abstractmethod
  def supports(self, market_id: MarketId) -> bool:
    """
    Check if the fuse supports the market.

    :param market_id: The market id
    :return: True if the fuse supports the market, False otherwise
    """
    pass

  @abstractmethod
  def create_fuse_enter_action(self, market_id: MarketId, amount: int) -> List[FuseActionDynamicStruct]:
    """
    Create an action to enter the fuse.

    :param market_id: The market id
    :param amount: The amount to enter
    :return: A list of FuseActionDynamicStruct representing the enter action
    """
    pass

  @abstractmethod
  def create_fuse_exit_action(self, market_id: MarketId, amount: int) -> List[FuseActionDynamicStruct]:
    """
    Create an action to exit the fuse.

    :param market_id: The market id
    :param amount: The amount to exit
    :return: A list of FuseActionDynamicStruct representing the exit action
    """
    pass

  @abstractmethod
  def create_fuse_claim_action(self, market_id: MarketId) -> List[FuseActionDynamicStruct]:
    """
    Create an action to claim from the fuse.

    :param market_id: The market id
    :return: A list of FuseActionDynamicStruct representing the claim action
    """
    pass
