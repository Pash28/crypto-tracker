from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import aiohttp


class CoinGeckoAPIError(RuntimeError):
    pass


class CoinNotFoundError(CoinGeckoAPIError):
    pass


@dataclass(frozen=True, slots=True)
class CoinRef:
    id: str
    symbol: str
    name: str


@dataclass(frozen=True, slots=True)
class CoinPrice:
    id: str
    symbol: str
    name: str
    price_usd: Decimal
    change_24h: Decimal | None


@dataclass(frozen=True, slots=True)
class CoinMarketData:
    id: str
    symbol: str
    name: str
    rank: int
    price_usd: Decimal
    market_cap_usd: Decimal | None


class CoinGeckoClient:
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3") -> None:
        self.base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None
        self._ticker_cache: dict[str, CoinRef] = {}

    async def __aenter__(self) -> "CoinGeckoClient":
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def connect(self) -> None:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def resolve_coin(self, ticker: str) -> CoinRef:
        symbol = ticker.strip().lower()
        if not symbol:
            raise CoinNotFoundError("Ticker is required.")
        if symbol in self._ticker_cache:
            return self._ticker_cache[symbol]

        data = await self._request_json("GET", "/search", params={"query": symbol})
        coins = data.get("coins", [])
        exact_matches = [
            coin for coin in coins if str(coin.get("symbol", "")).lower() == symbol
        ]
        if not exact_matches:
            raise CoinNotFoundError(f"Ticker {ticker.upper()} was not found.")

        selected = sorted(
            exact_matches,
            key=lambda coin: coin.get("market_cap_rank") or 10**9,
        )[0]
        ref = CoinRef(
            id=str(selected["id"]),
            symbol=str(selected["symbol"]).upper(),
            name=str(selected["name"]),
        )
        self._ticker_cache[symbol] = ref
        return ref

    async def get_coin_price(self, ticker: str) -> CoinPrice:
        coin = await self.resolve_coin(ticker)
        markets = await self._get_markets(ids=[coin.id])
        if not markets:
            raise CoinNotFoundError(f"No price found for {ticker.upper()}.")

        item = markets[0]
        return CoinPrice(
            id=coin.id,
            symbol=coin.symbol,
            name=coin.name,
            price_usd=_decimal(item.get("current_price")),
            change_24h=_optional_decimal(item.get("price_change_percentage_24h")),
        )

    async def get_prices_by_coin_ids(self, coin_ids: set[str]) -> dict[str, Decimal]:
        if not coin_ids:
            return {}
        markets = await self._get_markets(ids=sorted(coin_ids))
        return {
            str(item["id"]): _decimal(item.get("current_price"))
            for item in markets
            if item.get("id") and item.get("current_price") is not None
        }

    async def get_top_coins(self, limit: int = 10) -> list[CoinMarketData]:
        markets = await self._get_markets(per_page=limit)
        return [
            CoinMarketData(
                id=str(item["id"]),
                symbol=str(item["symbol"]).upper(),
                name=str(item["name"]),
                rank=int(item.get("market_cap_rank") or index),
                price_usd=_decimal(item.get("current_price")),
                market_cap_usd=_optional_decimal(item.get("market_cap")),
            )
            for index, item in enumerate(markets, start=1)
        ]

    async def _get_markets(
        self,
        ids: list[str] | None = None,
        per_page: int = 250,
    ) -> list[dict[str, Any]]:
        params: dict[str, str | int] = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        }
        if ids:
            params["ids"] = ",".join(ids)
            params["per_page"] = len(ids)

        data = await self._request_json("GET", "/coins/markets", params=params)
        if not isinstance(data, list):
            raise CoinGeckoAPIError("Unexpected CoinGecko response.")
        return data

    async def _request_json(
        self,
        method: str,
        path: str,
        params: dict[str, str | int] | None = None,
    ) -> Any:
        await self.connect()
        assert self._session is not None

        try:
            async with self._session.request(
                method,
                f"{self.base_url}{path}",
                params=params,
            ) as response:
                if response.status == 429:
                    raise CoinGeckoAPIError("CoinGecko rate limit reached. Try again soon.")
                if response.status >= 500:
                    raise CoinGeckoAPIError("CoinGecko is temporarily unavailable.")
                if response.status >= 400:
                    raise CoinGeckoAPIError("CoinGecko request failed.")
                return await response.json()
        except aiohttp.ClientError as exc:
            raise CoinGeckoAPIError("Could not reach CoinGecko.") from exc


def _decimal(value: Any) -> Decimal:
    if value is None:
        raise CoinGeckoAPIError("CoinGecko returned an incomplete price response.")
    return Decimal(str(value))


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
