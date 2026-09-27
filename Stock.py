from dataclasses import dataclass, field
from typing import Callable

from services.Price import get_current_price


@dataclass(frozen=True)
class Stock:
    """
    A stock identified by its ticker symbol.

    The price is not stored on the object: it is fetched on demand via
    `current_price()`, as required by the exercise. Where the price comes from is
    determined by `price_provider` (a function symbol -> price). This keeps the
    class independent from Alpha Vantage and allows tests to inject a fixed price.

    It is immutable and its equality/hash depend only on the symbol so it can be
    used as a key in `Portfolio` dictionaries.
    """

    symbol: str
    price_provider: Callable[[str], float] = field(
        default=get_current_price, compare=False, repr=False
    )

    def current_price(self) -> float:
        """Latest available price for the stock."""
        price = float(self.price_provider(self.symbol))
        if price <= 0:
            # With a price of 0 we cannot convert an amount into a number of shares.
            raise ValueError(f"Invalid price for {self.symbol}: {price}")
        return price
