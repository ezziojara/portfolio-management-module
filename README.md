# Portfolio rebalance

`Portfolio` class that, given the current holdings and the target distribution
(`allocation`, e.g. 40% META / 60% AAPL), calculates which positions to sell and
which to buy to reach the target balance.

## Structure

- `Stock.py`: `Stock(symbol)` with `current_price()`. The price source is injected
  via `price_provider`, so the class does not depend on a specific API.
- `Portfolio.py`: `Portfolio(holdings, allocation)` with `total_value()` and
  `rebalance()`. The module docstring explains the reasoning and assumptions.
- `services/Price.py`: latest available close from Alpha Vantage, or from mock
  data if `ALPHAVANTAGE_API_KEY` is not set.
- `tests/`: tests using fixed prices.

## How `rebalance()` works

```
total_value = Σ quantity_i × price_i
target_i    = total_value × allocation_i
difference_i = target_i − quantity_i × price_i   (> 0 buy, < 0 sell)
shares_i    = |difference_i| / price_i
```

It returns a list of `RebalanceAction(symbol, side, shares, amount)`, with sales
first and purchases second.

Assumptions: fractional shares are allowed, there are no fees or extra cash, and
the total value does not change (what is sold pays for what is bought).

## Usage

```bash
pip install -r requirements.txt
python Portfolio.py            # example with mock data
python -m unittest -v          # tests
```

```python
meta, aapl = Stock("META"), Stock("AAPL")
portfolio = Portfolio(holdings={meta: 10, aapl: 5}, allocation={meta: 0.4, aapl: 0.6})
portfolio.rebalance()
# [RebalanceAction(symbol='META', side=SELL, shares=5.09, amount=3827.82),
#  RebalanceAction(symbol='AAPL', side=BUY,  shares=11.22, amount=3827.82)]
```

To use real prices: `export ALPHAVANTAGE_API_KEY=...`.


Link with LLM used:
https://claude.ai/code/session_01PxxzTkTyb1ZvGCWKRxuKVW
