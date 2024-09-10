from abc import abstractmethod, ABC

from ipor_fusion_sdk import MarketId


class Operation(ABC):
  @abstractmethod
  def market_id(self) -> MarketId:
    pass
