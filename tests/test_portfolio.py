import unittest

from Portfolio import Portfolio, Side
from Stock import Stock
from services.Price import get_current_price

PRICES = {"META": 100.0, "AAPL": 50.0, "GOOGL": 200.0}


def fake_price(symbol: str) -> float:
    return PRICES[symbol]


META = Stock("META", fake_price)
AAPL = Stock("AAPL", fake_price)
GOOGL = Stock("GOOGL", fake_price)


def apply(portfolio: Portfolio, actions) -> dict[str, float]:
    """Applies the orders and returns the final weight of each symbol."""
    shares = {s.symbol: portfolio.holdings.get(s, 0) for s in portfolio._stocks()}
    for a in actions:
        shares[a.symbol] += a.shares if a.side == Side.BUY else -a.shares
    values = {sym: qty * PRICES[sym] for sym, qty in shares.items()}
    total = sum(values.values())
    return {sym: v / total for sym, v in values.items()}


class RebalanceTest(unittest.TestCase):
    def test_sells_overweight_and_buys_underweight(self):
        # 10 META (1000) + 10 AAPL (500) = 1500. Target 40/60 -> 600 / 900.
        portfolio = Portfolio({META: 10, AAPL: 10}, {META: 0.4, AAPL: 0.6})
        sell, buy = portfolio.rebalance()

        self.assertEqual((sell.symbol, sell.side), ("META", Side.SELL))
        self.assertAlmostEqual(sell.amount, 400)
        self.assertAlmostEqual(sell.shares, 4)
        self.assertEqual((buy.symbol, buy.side), ("AAPL", Side.BUY))
        self.assertAlmostEqual(buy.amount, 400)
        self.assertAlmostEqual(buy.shares, 8)

    def test_result_matches_allocation(self):
        portfolio = Portfolio(
            {META: 3, AAPL: 17, GOOGL: 1}, {META: 0.2, AAPL: 0.5, GOOGL: 0.3}
        )
        weights = apply(portfolio, portfolio.rebalance())
        self.assertAlmostEqual(weights["META"], 0.2)
        self.assertAlmostEqual(weights["AAPL"], 0.5)
        self.assertAlmostEqual(weights["GOOGL"], 0.3)

    def test_same_prices_different_holdings_give_different_actions(self):
        allocation = {META: 0.4, AAPL: 0.6}
        a = Portfolio({META: 10, AAPL: 1}, allocation).rebalance()
        b = Portfolio({META: 1, AAPL: 10}, allocation).rebalance()
        self.assertNotEqual(a, b)

    def test_balanced_portfolio_needs_no_actions(self):
        # 4 META (400) + 12 AAPL (600) is already 40/60.
        portfolio = Portfolio({META: 4, AAPL: 12}, {META: 0.4, AAPL: 0.6})
        self.assertEqual(portfolio.rebalance(), [])

    def test_buys_allocated_stock_not_held(self):
        portfolio = Portfolio({META: 10}, {META: 0.5, AAPL: 0.5})
        actions = {a.symbol: a for a in portfolio.rebalance()}
        self.assertEqual(actions["AAPL"].side, Side.BUY)
        self.assertAlmostEqual(actions["AAPL"].amount, 500)

    def test_sells_all_of_held_stock_not_allocated(self):
        portfolio = Portfolio({META: 5, GOOGL: 2}, {META: 1.0})
        actions = {a.symbol: a for a in portfolio.rebalance()}
        self.assertEqual(actions["GOOGL"].side, Side.SELL)
        self.assertAlmostEqual(actions["GOOGL"].shares, 2)

    def test_sells_come_before_buys(self):
        portfolio = Portfolio({AAPL: 10, GOOGL: 10}, {META: 0.5, AAPL: 0.5})
        sides = [a.side for a in portfolio.rebalance()]
        self.assertEqual(sides, sorted(sides, key=lambda s: s != Side.SELL))

    def test_empty_portfolio_has_nothing_to_rebalance(self):
        portfolio = Portfolio({}, {META: 0.4, AAPL: 0.6})
        self.assertEqual(portfolio.rebalance(), [])

    def test_total_value(self):
        portfolio = Portfolio({META: 2, AAPL: 3}, {META: 0.4, AAPL: 0.6})
        self.assertAlmostEqual(portfolio.total_value(), 350)


class ValidationTest(unittest.TestCase):
    def test_allocation_must_sum_one(self):
        with self.assertRaises(ValueError):
            Portfolio({META: 1}, {META: 0.4, AAPL: 0.4})

    def test_allocation_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            Portfolio({META: 1}, {META: 1.2, AAPL: -0.2})

    def test_allocation_cannot_be_empty(self):
        with self.assertRaises(ValueError):
            Portfolio({META: 1}, {})

    def test_holdings_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            Portfolio({META: -1}, {META: 1.0})

    def test_stock_rejects_non_positive_price(self):
        with self.assertRaises(ValueError):
            Stock("X", lambda _: 0).current_price()


class PriceProviderTest(unittest.TestCase):
    def test_returns_last_available_close_as_float(self):
        # The last day in the mock data is 2026-09-25.
        self.assertEqual(get_current_price("META"), 751.66)
        self.assertEqual(get_current_price("AAPL"), 341.07)

    def test_unknown_symbol_without_api_key_fails(self):
        with self.assertRaises(ValueError):
            get_current_price("ZZZZ")


if __name__ == "__main__":
    unittest.main()
