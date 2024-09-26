from typing import List

from ipor_fusion_sdk import MarketId
from ipor_fusion_sdk.operation.Operation import Operation


class ClosePosition(Operation):
    def __init__(
        self,
        market_id: MarketId,
        token_ids: List[int]
    ):
        if market_id is None:
            raise ValueError("market_id is required")
        if token_ids is None:
            raise ValueError("token_ids is required")

        self._market_id = market_id
        self._token_ids = token_ids

    def market_id(self) -> MarketId:
        return self._market_id

    def token_ids(self) -> List[int]:
        return self._token_ids

