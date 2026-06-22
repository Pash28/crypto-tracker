from aiogram import Router

from app.bot.handlers.alerts import router as alerts_router
from app.bot.handlers.market import router as market_router
from app.bot.handlers.price import router as price_router
from app.bot.handlers.start import router as start_router


def setup_routers() -> Router:
    router = Router(name="crypto_tracker")
    router.include_router(start_router)
    router.include_router(price_router)
    router.include_router(alerts_router)
    router.include_router(market_router)
    return router
