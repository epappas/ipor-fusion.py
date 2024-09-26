from eth_abi import encode
from eth_utils import function_signature_to_4byte_selector

from ipor_fusion_sdk.MarketId import MarketId
from ipor_fusion_sdk.fuse.FuseActionDynamicStruct import FuseActionDynamicStruct


class UniswapV3ModifyPositionFuseEnterData:
  def __init__(
      self,
      token0: str,
      token1: str,
      token_id: int,
      amount0_desired: int,
      amount1_desired: int,
      amount0_min: int,
      amount1_min: int,
      deadline: int, ):
    self.token0 = token0
    self.token1 = token1
    self.token_id = token_id
    self.amount0_desired = amount0_desired
    self.amount1_desired = amount1_desired
    self.amount0_min = amount0_min
    self.amount1_min = amount1_min
    self.deadline = deadline

  def encode(self) -> bytes:
    return encode(['(address,address,uint256,uint256,uint256,uint256,uint256,uint256)'],
      [[self.token0, self.token1, self.token_id, self.amount0_desired, self.amount1_desired, self.amount0_min,
        self.amount1_min, self.deadline, ]], )

  @staticmethod
  def function_selector() -> bytes:
    return function_signature_to_4byte_selector(
      "enter((address,address,uint256,uint256,uint256,uint256,uint256,uint256))")

  def function_call(self) -> bytes:
    return self.function_selector() + self.encode()


class UniswapV3ModifyPositionFuseExitData:
  def __init__(
      self, token_id: int, liquidity: int, amount0_min: int, amount1_min: int, deadline: int):
    self.token_id = token_id
    self.liquidity = liquidity
    self.amount0_min = amount0_min
    self.amount1_min = amount1_min
    self.deadline = deadline

  def encode(self) -> bytes:
    return encode(['(uint256,uint128,uint256,uint256,uint256)'],
      [[self.token_id, self.liquidity, self.amount0_min, self.amount1_min, self.deadline, ]])

  @staticmethod
  def function_selector() -> bytes:
    return function_signature_to_4byte_selector("exit((uint256,uint128,uint256,uint256,uint256))")

  def function_call(self) -> bytes:
    return self.function_selector() + self.encode()


class UniswapV3ModifyPositionFuse:
  PROTOCOL_ID = "uniswap-v3"

  def __init__(self, uniswap_v3_modify_position_fuse_address: str):
    self.uniswap_v3_modify_position_fuse_address = self._require_non_null(uniswap_v3_modify_position_fuse_address,
      "uniswap_v3_modify_position_fuse_address is required", )

  def create_fuse_enter_action(
      self,
      token0: str,
      token1: str,
      token_id: int,
      amount0_desired: int,
      amount1_desired: int,
      amount0_min: int,
      amount1_min: int,
      deadline: int):
    data = UniswapV3ModifyPositionFuseEnterData(token0,
      token1,
      token_id,
      amount0_desired,
      amount1_desired,
      amount0_min,
      amount1_min,
      deadline)
    return [FuseActionDynamicStruct(self.uniswap_v3_modify_position_fuse_address, data.function_call())]

  def create_fuse_exit_action(
      self, token_id: int, liquidity: int, amount0_min: int, amount1_min: int, deadline: int, ):
    data = UniswapV3ModifyPositionFuseExitData(token_id, liquidity, amount0_min, amount1_min, deadline)
    return [FuseActionDynamicStruct(self.uniswap_v3_modify_position_fuse_address, data.function_call())]

  @staticmethod
  def _require_non_null(value, message):
    if value is None:
      raise ValueError(message)
    return value

  def supports(self, market_id: MarketId) -> bool:
    if market_id is None:
      raise ValueError("marketId is required")
    return market_id.protocol_id == self.PROTOCOL_ID and market_id.market_id == "modify-position"
