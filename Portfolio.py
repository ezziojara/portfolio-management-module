"""
Portfolio management module.

Rebalancing idea
---------------
A portfolio has *holdings* (how many shares of each Stock it owns) and an
*allocation* (what fraction of the total value should be in each Stock).

1. A price snapshot is taken: each price is fetched once so all calculations use
   the same values even if prices change while the rebalance is being computed.
2. Total value   = Σ quantity_i × price_i
3. Target value_i = total value × allocation_i
4. Difference_i  = target_value_i − quantity_i × price_i
   > 0 → buy, < 0 → sell. Shares = |difference_i| / price_i

Assumptions
-----------
- Fractional shares are allowed (as in most investment apps). If whole shares
  were required, rounding would be needed and a small mismatch would have to be
  accepted.
- Rebalancing is self-financing: the total value does not change, so what is sold
  is exactly enough to cover what is bought. No fees, taxes, or cash balance are
  considered.
- A Stock in the allocation but not in holdings has quantity 0 and is bought. A
  Stock in holdings but not in the allocation has a target value of 0 and is sold
  completely.
"""
from dataclasses import dataclass
from enum import Enum

from Stock import Stock

# Differences smaller than this are treated as floating-point noise.
EPSILON = 1e-9
# Tolerance for validating that the allocation sums to 100%.
ALLOCATION_TOLERANCE = 1e-6


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class RebalanceAction:
    symbol: str
    side: Side
    shares: float
    amount: float


class Portfolio:
    def __init__(self, holdings: dict[Stock, float], allocation: dict[Stock, float]):
        """
        holdings:   Stock -> number of shares held.
        allocation: Stock -> target fraction of total value (0.4 = 40%).
                     Must sum to 1.
        """
        self._validate_holdings(holdings)
        self._validate_allocation(allocation)
        # Copies so external changes to the dicts do not affect the portfolio.
        self.holdings = dict(holdings)
        self.allocation = dict(allocation)

    @staticmethod
    def _validate_holdings(holdings: dict[Stock, float]) -> None:
        for stock, shares in holdings.items():
            if shares < 0:
                raise ValueError(f"Negative quantity for {stock.symbol}: {shares}")

    @staticmethod
    def _validate_allocation(allocation: dict[Stock, float]) -> None:
        if not allocation:
            raise ValueError("Allocation cannot be empty")
        for stock, weight in allocation.items():
            if weight < 0:
                raise ValueError(f"Negative weight for {stock.symbol}: {weight}")
        total = sum(allocation.values())
        if abs(total - 1) > ALLOCATION_TOLERANCE:
            raise ValueError(f"Allocation must sum to 1 (sum is {total})")

    def _stocks(self) -> set[Stock]:
        """All relevant Stocks: those held and those targeted."""
        return set(self.holdings) | set(self.allocation)

    def _price_snapshot(self) -> dict[Stock, float]:
        return {stock: stock.current_price() for stock in self._stocks()}

    def total_value(self) -> float:
        prices = self._price_snapshot()
        return sum(shares * prices[stock] for stock, shares in self.holdings.items())

    def rebalance(self) -> list[RebalanceAction]:
        """
        Orders needed to bring the portfolio in line with the allocation.

        It returns sales first and then purchases (sales free up the cash used to
        fund the purchases), and within each group it orders by symbol to keep the
        output deterministic. If the portfolio is already balanced, or has no
        value, it returns an empty list.
        """
        prices = self._price_snapshot()
        total = sum(shares * prices[stock] for stock, shares in self.holdings.items())
        if total <= EPSILON:
            # With no value there is nothing to redistribute. Investing new money is
            # a different use case (a "deposit"), outside the scope of this logic.
            return []

        actions = []
        for stock, price in prices.items():
            current_value = self.holdings.get(stock, 0) * price
            target_value = total * self.allocation.get(stock, 0)
            diff = target_value - current_value
            if abs(diff) <= EPSILON:
                continue
            actions.append(
                RebalanceAction(
                    symbol=stock.symbol,
                    side=Side.BUY if diff > 0 else Side.SELL,
                    shares=abs(diff) / price,
                    amount=abs(diff),
                )
            )

        actions.sort(key=lambda a: (a.side != Side.SELL, a.symbol))
        return actions


if __name__ == "__main__":
    meta = Stock("META")
    aapl = Stock("AAPL")
    portfolio = Portfolio(
        holdings={meta: 10, aapl: 5},
        allocation={meta: 0.4, aapl: 0.6},
    )

    print(f"META: {meta.current_price():.2f}  AAPL: {aapl.current_price():.2f}")
    print(f"Total value: {portfolio.total_value():.2f}")
    for action in portfolio.rebalance():
        print(f"{action.side.value:4} {action.shares:10.4f} {action.symbol:5} ({action.amount:.2f})")
