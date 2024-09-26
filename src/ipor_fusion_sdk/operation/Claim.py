class Claim:
    def __init__(self, market_id):
        if market_id is None:
            raise ValueError("marketId is required")
        self._market_id = market_id

    def market_id(self):
        return self._market_id

    def __eq__(self, other):
        if self is other:
            return True
        if other is None or not isinstance(other, Claim):
            return False
        return self._market_id == other._market_id

    def __hash__(self):
        return hash(self._market_id)

    def __str__(self):
        return f"Claim[marketId={self._market_id}]"

    def __repr__(self):
        return self.__str__()
